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

    def _split_table_header_and_rows(self, table_text: str) -> tuple[str, list[str]]:
        """Separa o header da tabela (título + linha de cabeçalho + separador)
        das linhas de dados. Diferente da versão original, o header NÃO é
        mais embutido em cada row — ele é retornado separadamente para ser
        reaproveitado uma única vez por grupo/parent."""
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
                continue

            if self._is_table_block(texto):
                yield from self._process_table_chunk(texto, header_chunk.metadata, json_metadata, is_web_page)
            else:
                # comportamento ORIGINAL, inalterado, para texto corrido
                sub_chunks = self.recursive_splitter.split_documents([header_chunk])
                for chunk in sub_chunks:
                    if len(chunk.page_content.strip()) > 20:
                        chunk.metadata.update(json_metadata)
                        chunk.metadata["origem"] = "web" if is_web_page else "edital"
                        chunk.metadata["chunk_type"] = "standalone"
                        yield chunk

    def _process_table_chunk(self, texto: str, header_metadata: dict, json_metadata: dict, is_web_page: bool):
        """
        FIX: antes, quando a tabela excedia o threshold, era criado um único
        parent com o texto INTEIRO da tabela (sem limite de tamanho), o que
        fazia parents de tabelas grandes (ex: ANEXO I com 20 disciplinas)
        chegarem a 10k+ caracteres — muito acima do table_parent_threshold.

        Agora as linhas da tabela são agrupadas em MÚLTIPLOS parents,
        cada um respeitando o table_parent_threshold. O header da tabela
        é reaproveitado (não duplicado por linha) e prefixado em cada
        parent/child para manter contexto semântico.
        """
        base_metadata = {**header_metadata, **json_metadata}
        base_metadata["origem"] = "web" if is_web_page else "edital"

        if len(texto) <= self.table_parent_threshold:
            yield Document(
                page_content=texto,
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

        # fallback de segurança: se por algum motivo não formou nenhum grupo
        # (ex: tabela sem linhas de dados detectadas), volta pro comportamento
        # antigo em vez de silenciosamente não emitir nada.
        if not groups:
            parent_id = str(uuid.uuid4())
            yield Document(
                page_content=texto,
                metadata={**base_metadata, "chunk_type": "parent", "parent_id": parent_id},
            )
            return

        for group in groups:
            parent_id = str(uuid.uuid4())
            parent_text = header_block + "\n" + "\n".join(group)

            yield Document(
                page_content=parent_text,
                metadata={**base_metadata, "chunk_type": "parent", "parent_id": parent_id},
            )

            for row_text in group:
                child_text = header_block + "\n" + row_text
                if len(child_text.strip()) <= 20:
                    continue
                yield Document(
                    page_content=child_text,
                    metadata={**base_metadata, "chunk_type": "child", "parent_id": parent_id},
                )