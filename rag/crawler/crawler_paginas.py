import json
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse
from app.core.config import settings
import requests
from bs4 import BeautifulSoup

HEADERS = {"Accept": "application/json", "User-Agent": "crawler-editais-ifpb/0.1"}

# Fora do OneDrive e com caminho curto (<projeto>/../../dados_ifpb/paginas)
PASTA_SAIDA_PADRAO = settings.DATALAKE_DIR / "paginas"


BLOCOS_IGNORADOS = {"title", "image", "description", "listing", "mainImageBlock"}


# ==========================================
# UTILITÁRIOS
# ==========================================
def _slug(texto, padrao="sem-setor"):
    """Converte o nome do setor em um nome de pasta seguro (sem acento/espaço)."""
    if not texto:
        return padrao
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto or padrao


# ==========================================
# LISTAGEM
# ==========================================
def get_json(url_busca, params, tentativas=5, log=print):
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.get(url_busca, headers=HEADERS, params=params, timeout=(10, 90))
            if r.status_code < 500:
                r.raise_for_status()
                return r.json()
            ultimo = f"HTTP {r.status_code}"
        except (requests.ConnectionError, requests.Timeout) as e:
            ultimo = repr(e)
        log(f"  [retry {i + 1}/{tentativas}] {ultimo}")
        time.sleep(2 ** i)
    raise RuntimeError(f"Falha após {tentativas} tentativas: {ultimo}")


def listar_paginas(url_busca, portal_type, tamanho_lote=20, log=print):
    inicio = 0
    while True:
        d = get_json(url_busca, {
            "portal_type": portal_type, "fullobjects": 1,
            "b_size": tamanho_lote, "b_start": inicio,
            "sort_on": "created", "sort_order": "descending",  # mais novos primeiro
        }, log=log)
        itens = d["items"]
        yield from itens
        inicio += len(itens)
        if not itens or inicio >= d["items_total"]:
            break
        time.sleep(0.5)


# ==========================================
# BLOCOS (Volto/slate) -> MARKDOWN
# ==========================================
def url_do_link(data):
    if not data:
        return ""
    if data.get("url"):
        return data["url"]
    link = data.get("link") or {}
    interno = (link.get("internal") or {}).get("internal_link") or []
    if interno:
        return interno[0].get("@id", "")
    return (link.get("external") or {}).get("external_link", "")


def render_inline(filhos):
    saida = ""
    for f in filhos:
        if "text" in f:
            saida += f["text"]
            continue
        interno = render_inline(f.get("children", []))
        if f.get("type") == "link":
            url = url_do_link(f.get("data"))
            saida += f"[{interno.strip()}]({url})" if url and interno.strip() else interno
        else:
            saida += interno
    return saida


def achar_linhas(no):
    if no.get("type") == "tr":
        return [no]
    achadas = []
    for f in no.get("children", []):
        if isinstance(f, dict):
            achadas += achar_linhas(f)
    return achadas


def render_no(no, nivel=0):
    tipo = no.get("type") or ""
    filhos = no.get("children", [])

    if tipo in ("ul", "ol"):
        linhas = []
        for n, li in enumerate(filhos, 1):
            marcador = "-" if tipo == "ul" else f"{n}."
            subs = li.get("children", [])
            texto = render_inline([c for c in subs if c.get("type") not in ("ul", "ol")]).strip()
            linhas.append("  " * nivel + f"{marcador} {texto}")
            for c in subs:
                if c.get("type") in ("ul", "ol"):
                    linhas.append(render_no(c, nivel + 1))
        return "\n".join(linhas)

    if tipo == "table":
        linhas = []
        for tr in achar_linhas(no):
            celulas = [render_inline(td.get("children", [])).strip().replace("\n", " ")
                       for td in tr.get("children", [])]
            linhas.append("| " + " | ".join(celulas) + " |")
        return "\n".join(linhas)

    if re.fullmatch(r"h[1-6]", tipo):
        texto = render_inline(filhos).strip()
        return "#" * max(int(tipo[1]), 2) + " " + texto if texto else ""

    if tipo == "blockquote":
        texto = render_inline(filhos).strip()
        return "> " + texto if texto else ""

    return render_inline(filhos).strip()


def renderizar_blocos(blocos, ordem, desconhecidos):
    partes = []
    for bid in ordem:
        b = blocos.get(bid)
        if not b:
            continue
        tipo = b.get("@type")
        if tipo == "slate":
            for no in b.get("value", []):
                texto = render_no(no)
                if texto.strip():
                    partes.append(texto)
        elif tipo == "html":
            texto = BeautifulSoup(b.get("html", ""), "html.parser").get_text(" ", strip=True)
            if texto:
                partes.append(texto)
        elif tipo in BLOCOS_IGNORADOS:
            continue
        else:
            sub = b if "blocks" in b else (b.get("data") or {})
            if isinstance(sub, dict) and isinstance(sub.get("blocks"), dict):
                ordem_sub = (sub.get("blocks_layout") or {}).get("items") or list(sub["blocks"])
                partes += renderizar_blocos(sub["blocks"], ordem_sub, desconhecidos)
            else:
                desconhecidos[tipo] += 1
    return partes


# ==========================================
# SALVAR
# ==========================================
def data_valida(iso):
    if not iso or iso.startswith(("1969", "2499")):
        return None
    return iso


def salvar_pagina(item, desconhecidos, pasta_saida, raiz, ano_minimo_noticias, min_caracteres):
    caminho = PurePosixPath(unquote(urlparse(item["@id"]).path)).relative_to(raiz)
    pastas = caminho.parts[:-1]
    tipo = item["@type"]

    if tipo == "Document" and pastas and pastas[0] == "noticias":
        return "ignorada_indice_noticias", None

    ano = next((m.group(1) for p in pastas if (m := re.search(r"(20\d{2})", p))), None) \
        or item["created"][:4]
    if tipo == "News Item" and ano_minimo_noticias and int(ano) < ano_minimo_noticias:
        return "ignorada_noticia_antiga", None

    setor = pastas[0] if pastas else None

    # Subpasta por setor: <pasta_saida>/<setor>/<UID>.md
    pasta_setor = pasta_saida / _slug(setor)
    destino_md = pasta_setor / f"{item['UID']}.md"
    destino_json = destino_md.with_suffix(".json")
    if destino_md.exists() and destino_json.exists():
        return "pulado", None

    blocos = item.get("blocks") or {}
    ordem = (item.get("blocks_layout") or {}).get("items") or list(blocos)
    partes = renderizar_blocos(blocos, ordem, desconhecidos)
    corpo = "\n\n".join(partes).strip()
    if len(corpo) < min_caracteres:
        return "vazia", None

    pasta_setor.mkdir(parents=True, exist_ok=True)

    data_pub = data_valida(item.get("effective")) or item["created"]
    descricao = item.get("description") or ""
    cabecalho = f"# {item['title']}\n\nFonte: {item['@id']}\nPublicado em: {data_pub[:10]}\n"
    if descricao:
        cabecalho += f"\n{descricao}\n"
    destino_md.write_text(cabecalho + "\n" + corpo + "\n", encoding="utf-8")

    meta = {
        "documento_id": item["UID"],
        "ano": ano,
        "setor": setor,
        "caminho": "/".join(pastas),
        "titulo_documento": item["title"],
        "descricao": descricao,
        "data_publicacao": data_pub,
        "data_modificacao": item["modified"],
        "url_pagina_referencia": item["@id"],
        "nome_original": item["id"],
        "mime_type": "text/markdown",
        "tipo_documento": "NOTICIA" if tipo == "News Item" else "PAGINA",
    }
    destino_json.write_text(json.dumps(meta, ensure_ascii=False, indent=4), encoding="utf-8")
    return "salvo", destino_md


# ==========================================
# FUNÇÃO PRINCIPAL (para importar na pipeline)
# ==========================================
def executar_crawler_paginas(
    base,
    raiz,
    pasta_saida=None,
    limite=None,
    ano_minimo_noticias=None,
    min_caracteres=50,
    tipos=("Document", "News Item"),
    tamanho_lote=20,
    verbose=True,
):
    """
    Lista páginas/notícias do portal, converte os blocos em Markdown e salva
    cada uma com seu metadado .json em <pasta_saida>/<setor>/.

    Parâmetros
    ----------
    base : str
        URL raiz do site, ex.: "https://www.ifpb.edu.br"
    raiz : str
        Caminho da seção a varrer, ex.: "/campus/cajazeiras"
    pasta_saida : str | Path | None
        Pasta de destino. Padrão: PASTA_SAIDA_PADRAO.
    limite : int | None
        Máximo de itens salvos/pulados por tipo (útil para testes). None = todos.
    ano_minimo_noticias : int | None
        Só notícias (News Item) deste ano em diante. None = sem filtro.
    min_caracteres : int
        Páginas com menos texto que isso são descartadas.
    tipos : tuple[str]
        portal_types a varrer.
    tamanho_lote : int
        Itens por página na listagem da API.
    verbose : bool
        Imprime progresso.

    Retorna
    -------
    dict com: "resumo" (Counter "tipo: status"), "desconhecidos" (Counter de
    blocos não tratados), "salvos" (lista de Paths) e "pasta_saida" (Path).
    """
    base = base.rstrip("/")
    raiz = "/" + raiz.strip("/")
    url_busca = f"{base}/++api++{raiz}/@search"
    pasta_saida = Path(pasta_saida) if pasta_saida else PASTA_SAIDA_PADRAO
    pasta_saida.mkdir(parents=True, exist_ok=True)

    def log(msg):
        if verbose:
            print(msg)

    log(f"Salvando em: {pasta_saida}")

    resumo, desconhecidos, salvos = Counter(), Counter(), []
    for portal_type in tipos:
        contados = 0
        for item in listar_paginas(url_busca, portal_type, tamanho_lote, log=log):
            status, arquivo = salvar_pagina(
                item, desconhecidos, pasta_saida, raiz, ano_minimo_noticias, min_caracteres
            )
            resumo[f"{portal_type}: {status}"] += 1
            if arquivo:
                salvos.append(arquivo)
            if limite and status == "vazia":
                nome = PurePosixPath(urlparse(item["@id"]).path).name
                log(f"  [vazia] {item['title'][:60]} | {nome}")
            if status in ("salvo", "pulado"):  # vazias não contam como amostra
                contados += 1
                if limite and contados >= limite:
                    break

    log("\nResumo:")
    for chave, n in sorted(resumo.items()):
        log(f"  {n:4d}  {chave}")
    log(f"\nBlocos não tratados (tipo -> quantidade): {dict(desconhecidos)}")

    return {
        "resumo": resumo,
        "desconhecidos": desconhecidos,
        "salvos": salvos,
        "pasta_saida": pasta_saida,
    }


# Uso direto como script (opcional)
if __name__ == "__main__":
    executar_crawler_paginas(
        base="https://www.ifpb.edu.br",
        raiz="/campus/cajazeiras",
        ano_minimo_noticias=2026,
    )