import os
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from typing import Dict, Any
import re
from langchain_core.documents import Document
import uuid


class RAGChunking:
    def __init__(self, datalake_directory, table_parent_threshold: int = 1500) -> None:
        self.datalake_directory = datalake_directory
        self.table_parent_threshold = table_parent_threshold

        self.headers_to_split_on = [
            ("#", "Capitulo"),
            ("##", "Secao"),
            ("###", "Subsecao"),
        ]
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def _is_table_block(self, text: str) -> bool:
        """Detecta se um bloco é uma tabela markdown: linhas com '|' e uma
        linha separadora do tipo |---|---|."""
        linhas = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if len(linhas) < 2:
            return False
        linhas_com_pipe = [l for l in linhas if l.startswith("|")]
        tem_separador = any(re.match(r"^\|[\s\-:|]+\|$", l) for l in linhas_com_pipe)
        return len(linhas_com_pipe) >= 2 and tem_separador

    def _split_into_segments(self, texto: str) -> list[tuple[str, str]]:
        """Divide o texto em segmentos ('text' | 'table'), isolando blocos
        contíguos de linhas de tabela markdown do texto corrido ao redor.

        FIX (anterior): antes, o header_chunk inteiro (que podia misturar
        prosa + tabela, já que o split é feito por cabeçalho markdown
        # ## ###) era classificado como "bloco de tabela" só porque
        continha em algum lugar >=2 linhas com '|' e um separador. Isso
        fazia com que `_split_table_header_and_rows` "engolisse" todo o
        texto corrido que vinha DEPOIS da última linha da tabela dentro
        de uma única row gigante (já que a função só fecha uma row ao
        encontrar uma nova linha começando com '|').

        Consequência prática: linhas legítimas da tabela (ex: "2 vagas
        -> 6 classificados") ficavam isoladas em chunks pequenos e pouco
        informativos, enquanto a última linha da tabela virava um chunk
        gigante contaminado com parágrafos que não tinham nada a ver com
        ela — prejudicando tanto a recuperação quanto a qualidade do
        contexto entregue ao LLM.

        Esta função resolve isso separando ANTES: cada trecho contíguo
        de linhas com '|' é isolado e só é tratado como tabela se passar
        em `_is_table_block`; o texto ao redor nunca é misturado.
        """
        linhas = texto.split("\n")
        segments: list[tuple[str, str]] = []
        buffer_texto: list[str] = []
        buffer_tabela: list[str] = []

        def flush_texto():
            if buffer_texto:
                segments.append(("text", "\n".join(buffer_texto)))
                buffer_texto.clear()

        def flush_tabela():
            if buffer_tabela:
                candidato = "\n".join(buffer_tabela)
                tipo = "table" if self._is_table_block(candidato) else "text"
                segments.append((tipo, candidato))
                buffer_tabela.clear()

        for linha in linhas:
            if linha.strip().startswith("|"):
                flush_texto()
                buffer_tabela.append(linha)
            else:
                flush_tabela()
                buffer_texto.append(linha)

        flush_tabela()
        flush_texto()

        # merge de segmentos 'text' adjacentes (pode acontecer quando um
        # bloco de linhas com '|' não é validado como tabela e cai de
        # volta como 'text', ficando ao lado de outro segmento 'text')
        merged: list[tuple[str, str]] = []
        for tipo, conteudo in segments:
            if merged and merged[-1][0] == tipo == "text":
                merged[-1] = ("text", merged[-1][1] + "\n" + conteudo)
            else:
                merged.append((tipo, conteudo))
        return merged

    def _clean_cell(self, cell: str) -> str:
        """Remove marcação markdown residual (negrito, <br>, <u>) de uma
        célula de tabela e normaliza espaços, deixando texto limpo para
        compor as frases sintéticas."""
        cell = cell.strip()
        cell = re.sub(r"\*\*", "", cell)
        cell = re.sub(r"<br\s*/?>", " ", cell, flags=re.IGNORECASE)
        cell = re.sub(r"</?u>", "", cell, flags=re.IGNORECASE)
        cell = re.sub(r"\s+", " ", cell).strip()
        return cell

    def _parse_table_line_cells(self, line: str) -> list[str]:
        """Quebra uma linha markdown '|a|b|c|' em ['a', 'b', 'c'] já limpas."""
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [self._clean_cell(c) for c in line.split("|")]

    def _looks_like_header_row(self, line: str) -> bool:
        """FIX NOVO: detecta se uma linha de tabela, embora venha logo
        APÓS o separador |---|---|, ainda é um cabeçalho real e não uma
        linha de dado.

        MOTIVAÇÃO DO BUG: várias tabelas do corpus (cronogramas de
        editais, principalmente) vêm com um título mesclado ACIMA dos
        nomes de coluna reais, seguido do separador logo depois do
        título — não depois do cabeçalho de verdade:

            |**Técnico Subsequente - 2026**|**- Edificações (Noturno)**|
            |---|---|
            |**ETAPA**|**PERÍODO**|
            |**Pré-Matrícula**|**16 a 22 de janeiro de 2026**|

        Antes desse fix, `_split_table_header_and_rows` fechava o
        header logo no separador, tratando a linha de título como se
        fossem os nomes de coluna ("Técnico Subsequente - 2026",
        "- Edificações (Noturno)") e jogando a linha "ETAPA | PERÍODO"
        — que É o cabeçalho de verdade — para dentro de `rows`, como se
        fosse uma linha de dado comum. Resultado: as frases sintéticas
        geradas ficavam com o rótulo de coluna errado (o título do curso
        no lugar de "ETAPA"/"PERÍODO"), prejudicando o embedding e a
        busca híbrida.

        HEURÍSTICA: uma linha de cabeçalho real tende a ter células
        curtas (poucas palavras), sem dígitos, e majoritariamente em
        negrito — diferente de uma linha de título (mais longa/textual)
        e diferente de uma linha de dado (costuma ter números, datas,
        nomes próprios longos etc).
        """
        celulas = self._parse_table_line_cells(line)
        celulas = [c for c in celulas if c]
        if not celulas:
            return False

        def curta_sem_digito(c: str) -> bool:
            sem_marcacao = re.sub(r"\*\*", "", c).strip()
            tem_digito = bool(re.search(r"\d", sem_marcacao))
            poucas_palavras = len(sem_marcacao.split()) <= 3
            return poucas_palavras and not tem_digito

        proporcao_curta = sum(curta_sem_digito(c) for c in celulas) / len(celulas)
        return proporcao_curta >= 0.7

    def _parse_header_columns(self, header_block: str) -> list[str]:
        """Extrai os nomes das colunas a partir da ÚLTIMA linha de
        cabeçalho do bloco de header (a linha de cabeçalho real de
        colunas, não a linha de título mesclado, quando as duas
        existirem — ver `_looks_like_header_row`).

        FIX: antes, pegava a primeira linha com '|' que não fosse o
        separador — o que dava errado quando havia título + cabeçalho
        real, pois a primeira linha era o título. Agora pega a ÚLTIMA
        linha não-separadora do header_block, que corresponde ao
        cabeçalho de colunas de fato após o fix em
        `_split_table_header_and_rows`.
        """
        linhas = [l for l in header_block.strip().split("\n") if l.strip()]
        candidatas = [
            l.strip() for l in linhas
            if l.strip().startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", l.strip())
        ]
        if not candidatas:
            return []
        return self._parse_table_line_cells(candidatas[-1])

    def _row_to_sentence(self, columns: list[str], row_text: str) -> str:
        """Converte uma linha de tabela em uma frase 'coluna: valor; coluna:
        valor' em vez de manter só o formato tabular puro.

        MOTIVAÇÃO: tabelas markdown puras (poucos tokens de texto, muitos
        números e símbolos '|') tendem a ter embeddings fracos e a perder,
        em buscas híbridas/semânticas, para chunks de prosa que repetem
        palavras-chave da pergunta várias vezes — mesmo quando a tabela é
        a resposta certa. Reforçar o chunk com uma frase que nomeia
        explicitamente cada valor (reaproveitando os nomes das colunas do
        header) aumenta a sobreposição lexical/semântica com perguntas em
        linguagem natural sobre aquela linha.
        """
        linha_unica = " ".join(l.strip() for l in row_text.strip().split("\n"))
        valores = self._parse_table_line_cells(linha_unica)
        if not columns or not valores:
            return ""
        pares = [f"{col}: {val}" for col, val in zip(columns, valores) if col and val]
        return "; ".join(pares)

    def _rows_to_sentences_block(self, header_block: str, rows: list[str]) -> str:
        """Gera o bloco de frases sintéticas para um conjunto de rows,
        reaproveitando as colunas extraídas uma única vez do header."""
        columns = self._parse_header_columns(header_block)
        frases = [self._row_to_sentence(columns, r) for r in rows]
        frases = [f for f in frases if f]
        return "\n".join(frases)

    def _split_table_header_and_rows(self, table_text: str) -> tuple[str, list[str]]:
        """Separa o header da tabela (título + linha de cabeçalho + separador)
        das linhas de dados. O header NÃO é embutido em cada row aqui — ele é
        retornado separadamente para ser reaproveitado uma única vez por
        grupo/parent.

        Pré-condição: `table_text` já deve ser um bloco isolado de tabela
        (ver `_split_into_segments`), sem prosa misturada antes ou depois.

        FIX: depois de encontrar o separador |---|---|, checa se a
        primeira linha de `data_lines` ainda "parece" um cabeçalho real
        (ver `_looks_like_header_row`) em vez de assumir que o separador
        sempre vem logo após o cabeçalho de colunas. Isso cobre o caso
        de tabelas com título mesclado acima do cabeçalho de colunas
        (ex: tabelas de cronograma), onde o separador aparece logo após
        o título, não após "ETAPA | PERÍODO". Quando detectado, essa
        linha é movida de volta para o header_block, e
        `_parse_header_columns` passa a extrair os nomes de coluna
        corretos a partir dela (por pegar a ÚLTIMA linha não-separadora
        do header_block).
        """
        linhas = [l for l in table_text.strip().split("\n") if l.strip()]

        header_lines = []
        data_lines = []
        separador_encontrado = False
        for linha in linhas:
            if not separador_encontrado:
                header_lines.append(linha)
                if re.match(r"^\|[\s\-:|]+\|$", linha.strip()):
                    separador_encontrado = True
            else:
                data_lines.append(linha)

        # FIX: se a linha logo após o separador ainda parece um cabeçalho
        # de colunas (título mesclado acima do cabeçalho real), ela é
        # movida para o header_block em vez de virar a primeira "row".
        if data_lines and self._looks_like_header_row(data_lines[0]):
            header_lines.append(data_lines.pop(0))

        header_block = "\n".join(header_lines)

        rows = []
        current_row = []
        for linha in data_lines:
            if linha.strip().startswith("|") and current_row:
                rows.append("\n".join(current_row))
                current_row = [linha]
            else:
                current_row.append(linha)
        if current_row:
            rows.append("\n".join(current_row))

        rows = [r for r in rows if r.strip()]
        return header_block, rows

    def chunk_content(self, markdown_path, json_metadata):
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False
        )

        with open(markdown_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        header_chunks = markdown_splitter.split_text(md_content)
        is_web_page = "paginas_web" in markdown_path

        for header_chunk in header_chunks:
            texto = header_chunk.page_content

            if len(texto.strip()) <= 20:
                print(f"Pulando chunk irrelevante em: {header_chunk.metadata.get('titulo')}")
                print(texto)
                continue

            # FIX: em vez de decidir "o header_chunk inteiro é tabela ou
            # não", segmentamos o conteúdo em blocos de texto e blocos de
            # tabela isolados. Assim a tabela nunca arrasta prosa junto,
            # e a prosa ao redor da tabela (que antes era descartada
            # silenciosamente) volta a ser chunkada normalmente.
            for tipo, conteudo in self._split_into_segments(texto):
                if len(conteudo.strip()) <= 20:
                    continue

                if tipo == "table":
                    yield from self._process_table_chunk(
                        conteudo, header_chunk.metadata, json_metadata, is_web_page
                    )
                else:
                    # comportamento ORIGINAL, inalterado, para texto corrido
                    temp_doc = Document(page_content=conteudo, metadata=header_chunk.metadata)
                    sub_chunks = self.recursive_splitter.split_documents([temp_doc])
                    for chunk in sub_chunks:
                        if len(chunk.page_content.strip()) > 20:
                            chunk.metadata.update(json_metadata)
                            chunk.metadata["origem"] = "web" if is_web_page else "edital"
                            chunk.metadata["chunk_type"] = "standalone"
                            yield chunk

    def _process_table_chunk(self, texto: str, header_metadata: dict, json_metadata: dict, is_web_page: bool):
        """
        FIX (anterior): antes, quando a tabela excedia o threshold, era
        criado um único parent com o texto INTEIRO da tabela (sem limite
        de tamanho), o que fazia parents de tabelas grandes (ex: ANEXO I
        com 20 disciplinas) chegarem a 10k+ caracteres — muito acima do
        table_parent_threshold.

        Agora as linhas da tabela são agrupadas em MÚLTIPLOS parents,
        cada um respeitando o table_parent_threshold. O header da tabela
        é reaproveitado (não duplicado por linha) e prefixado em cada
        parent/child para manter contexto semântico.

        FIX NOVO: quando a tabela não tem um separador |---|---| válido
        (PDF convertido de forma inconsistente, separador malformado ou
        ausente), `_split_table_header_and_rows` não encontra nenhuma
        linha de dado (`rows` fica vazio) e caímos no fallback abaixo —
        que reproduzia, sem aviso nenhum, o bug original que o
        parent-child chunking foi criado para resolver (um único parent
        gigante, sem limite de tamanho). Agora esse caminho emite um log
        de aviso, para permitir medir quantas tabelas do corpus estão
        caindo nesse fallback e decidir se vale investir em um parsing
        de separador mais tolerante.
        """
        base_metadata = {**header_metadata, **json_metadata}
        base_metadata["origem"] = "web" if is_web_page else "edital"

        if len(texto) <= self.table_parent_threshold:
            # FIX: mesmo tabelas pequenas (que cabem inteiras num único
            # chunk standalone) sofrem com embedding fraco por serem
            # majoritariamente numéricas/tabulares. Anexamos frases
            # sintéticas "coluna: valor" por linha para reforçar a
            # recuperação, sem remover o formato tabular original (que
            # continua útil para o LLM ler com precisão).
            header_block, rows = self._split_table_header_and_rows(texto)
            frases = self._rows_to_sentences_block(header_block, rows)
            texto_enriquecido = texto if not frases else f"{texto}\n\n{frases}"
            yield Document(
                page_content=texto_enriquecido,
                metadata={**base_metadata, "chunk_type": "standalone"},
            )
            return

        header_block, rows = self._split_table_header_and_rows(texto)
        header_len = len(header_block)

        # Agrupa linhas em blocos de parent respeitando o threshold
        groups: list[list[str]] = []
        current_group: list[str] = []
        current_len = header_len  # cada parent vai incluir o header

        for row_text in rows:
            projected_len = current_len + len(row_text) + 1  # +1 para o \n de junção

            if current_group and projected_len > self.table_parent_threshold:
                groups.append(current_group)
                current_group = []
                current_len = header_len

            current_group.append(row_text)
            current_len += len(row_text) + 1

        if current_group:
            groups.append(current_group)

        # FIX NOVO: log de aviso no fallback de segurança, para medir a
        # incidência de tabelas sem separador válido no corpus, em vez
        # de silenciosamente reproduzir o bug de parent sem limite.
        if not groups:
            print(
                "[AVISO] Tabela sem linhas de dado detectadas (provável "
                "separador |---|---| ausente ou malformado) — caindo em "
                "fallback SEM limite de tamanho de parent. "
                f"Capitulo: {header_metadata.get('Capitulo')!r}, "
                f"tamanho do bloco: {len(texto)} chars, "
                f"titulo_documento: {json_metadata.get('titulo_documento')!r}"
            )
            parent_id = str(uuid.uuid4())
            yield Document(
                page_content=texto,
                metadata={**base_metadata, "chunk_type": "parent", "parent_id": parent_id},
            )
            return

        columns = self._parse_header_columns(header_block)

        for group in groups:
            parent_id = str(uuid.uuid4())
            parent_text = header_block + "\n" + "\n".join(group)

            # FIX: reforça o parent com as frases sintéticas de todas as
            # rows do grupo, pelo mesmo motivo do caso standalone acima.
            frases_grupo = self._rows_to_sentences_block(header_block, group)
            parent_text_enriquecido = (
                parent_text if not frases_grupo else f"{parent_text}\n\n{frases_grupo}"
            )

            yield Document(
                page_content=parent_text_enriquecido,
                metadata={**base_metadata, "chunk_type": "parent", "parent_id": parent_id},
            )

            for row_text in group:
                child_text = header_block + "\n" + row_text

                # FIX: reforça o child (uma única linha) com sua frase
                # sintética individual — é aqui que o problema de recall
                # é mais crítico, já que o child costuma ter só o header
                # + uma linha de valores, quase sem texto semântico.
                frase_row = self._row_to_sentence(columns, row_text)
                if frase_row:
                    child_text = f"{child_text}\n\n{frase_row}"

                if len(child_text.strip()) <= 20:
                    continue
                yield Document(
                    page_content=child_text,
                    metadata={**base_metadata, "chunk_type": "child", "parent_id": parent_id},
                )