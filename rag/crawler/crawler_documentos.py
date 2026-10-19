import json
import mimetypes
import os
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse
from app.core.config import settings
import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS_API = {"Accept": "application/json", "User-Agent": UA}
# sem Accept JSON, senão a URL do arquivo pode devolver JSON
HEADERS_DL = {"User-Agent": UA}

# Fora do OneDrive e com caminho curto (<projeto>/../../dados_ifpb/editais)
PASTA_SAIDA_PADRAO = settings.DATALAKE_DIR / "documentos"


# ==========================================
# UTILITÁRIOS
# ==========================================
def _slug(texto, padrao="sem-setor", setor=None):
    """Converte o nome do setor em um nome de pasta seguro (sem acento/espaço)."""
    if not texto:
        return padrao if not setor else setor
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto or padrao


# ==========================================
# LISTAGEM (API REST do Plone)
# ==========================================
def _get_json(url_busca, params, tentativas=5, log=print):
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.get(url_busca, headers=HEADERS_API, params=params, timeout=(10, 60))
            if r.status_code < 500:
                r.raise_for_status()
                return r.json()
            ultimo = f"HTTP {r.status_code}"
        except (requests.ConnectionError, requests.Timeout) as e:
            ultimo = repr(e)
        espera = 2 ** i
        log(f"  [retry {i + 1}/{tentativas}] {ultimo}; aguardando {espera}s")
        time.sleep(espera)
    raise RuntimeError(f"Falha após {tentativas} tentativas: {ultimo}")


def total_de_arquivos(url_busca, log=print):
    return _get_json(url_busca, {"portal_type": "File", "b_size": 1}, log=log)["items_total"]


def listar_arquivos(url_busca, tamanho_lote=100, log=print):
    params = {
        "portal_type": "File",
        "sort_on": "created",
        "sort_order": "ascending",
        "metadata_fields": "_all",
        "b_size": tamanho_lote,
    }
    inicio = 0
    while True:
        dados = _get_json(url_busca, {**params, "b_start": inicio}, log=log)
        itens = dados["items"]
        yield from itens
        inicio += len(itens)
        if not itens or inicio >= dados["items_total"]:
            break
        time.sleep(0.5)


# ==========================================
# METADADOS
# ==========================================
def data_valida(iso):
    # Plone usa 1969 e 2499 como "sem data"
    if not iso or iso.startswith(("1969", "2499")):
        return None
    return iso


def montar_metadados(item, base, raiz, setor_pred=None):
    caminho = PurePosixPath(unquote(urlparse(item["@id"]).path)).relative_to(raiz)
    pastas = caminho.parts[:-1]
    ano = next((m.group(1) for p in pastas if (m := re.search(r"(20\d{2})", p))), None) \
        or item["created"][:4]
    ext = os.path.splitext(item["id"])[1] \
        or mimetypes.guess_extension(item.get("mime_type") or "") or ".bin"
    meta = {
        "documento_id": item["UID"],
        "ano": ano,
        "setor": pastas[0] if pastas else setor_pred,
        "caminho": "/".join(pastas),
        "edital_pai": pastas[-1] if pastas else "Geral",
        "titulo_documento": item["title"],
        "descricao": item.get("description") or "",
        "data_publicacao": data_valida(item.get("effective")) or item["created"],
        "data_modificacao": item["modified"],
        "url_pagina_referencia": f"{base}{raiz}/" + "/".join(pastas),
        "url_arquivo_direto": item["@id"],
        "nome_original": item["id"],
        "mime_type": item.get("mime_type"),
        "tipo_documento": ext.lstrip(".").upper(),
    }
    return meta, ext


# ==========================================
# DOWNLOAD
# ==========================================
def baixar(item, pasta_saida: Path, base, raiz, setor=None):
    meta, ext = montar_metadados(item, base, raiz, setor_pred=setor)

    # Subpasta por setor: <pasta_saida>/<setor>/<UID>.<ext>
    pasta_setor = pasta_saida / _slug(meta["setor"], setor=setor)
    pasta_setor.mkdir(parents=True, exist_ok=True)

    destino = pasta_setor / f"{item['UID']}{ext}"
    destino_json = destino.with_suffix(".json")
    if destino.exists() and destino_json.exists():
        return "pulado"

    tmp = destino.with_suffix(destino.suffix + ".part")
    caminho_api = base + "/++api++" + urlparse(item["@id"]).path
    for url in (item["@id"] + "/@@download/file", item["@id"], caminho_api + "/@@download/file"):
        try:
            with requests.get(url, headers=HEADERS_DL, stream=True, timeout=(10, 60)) as r:
                tipo = r.headers.get("Content-Type", "").lower()
                if r.status_code != 200 or "html" in tipo or "json" in tipo:
                    continue
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
        except (requests.ConnectionError, requests.Timeout):
            continue
        os.replace(tmp, destino)
        destino_json.write_text(json.dumps(meta, ensure_ascii=False, indent=4), encoding="utf-8")
        return "baixado"
    return "falhou"


# ==========================================
# FUNÇÃO PRINCIPAL (para importar na pipeline)
# ==========================================
def executar_crawler(
    base,
    raiz,
    tipo_doc: str,
    pasta_saida=None,
    ano_minimo=None,
    limite=None,
    tamanho_lote=100,
    pausa=0.3,
    verbose=True,
):
    """
    Lista, baixa e salva (com metadados .json) os arquivos de uma seção do portal.

    Parâmetros
    ----------
    base : str
        URL raiz do site, ex.: "https://www.ifpb.edu.br"
    raiz : str
        Caminho da seção a varrer, ex.: "/campus/cajazeiras/editais"
    pasta_saida : str | Path | None
        Pasta de destino. Os arquivos ficam em <pasta_saida>/<setor>/.
        Padrão: PASTA_SAIDA_PADRAO.
    ano_minimo : int | None
        Só baixa documentos com ano >= ano_minimo. None = sem filtro.
    limite : int | None
        Baixa só os N primeiros (útil para testes). None = todos.
    tamanho_lote : int
        Itens por página na listagem da API.
    pausa : float
        Intervalo (s) entre downloads.
    verbose : bool
        Imprime progresso.

    Retorna
    -------
    dict com: "resumo" (Counter baixado/pulado/falhou), "falhas" (lista de URLs),
    "pasta_saida" (Path) e "total_listado" (int).
    """
    base = base.rstrip("/")
    raiz = "/" + raiz.strip("/")
    url_busca = f"{base}/++api++{raiz}/@search"
    pasta_saida = Path(pasta_saida) if pasta_saida else PASTA_SAIDA_PADRAO / tipo_doc
    pasta_saida.mkdir(parents=True, exist_ok=True)

    def log(msg):
        if verbose:
            print(msg)

    esperado = total_de_arquivos(url_busca, log=log)
    log(f"Servidor informa {esperado} arquivos. Listando...")
    itens = list(listar_arquivos(url_busca, tamanho_lote, log=log))
    uids = {i["UID"] for i in itens}
    total_listado = len(itens)
    log(f"Listados: {total_listado} | UIDs únicos: {len(uids)}")
    if total_listado != esperado or len(uids) != total_listado:
        log("ATENÇÃO: contagem diferente do esperado ou itens repetidos.")
    log(f"Tipos de arquivo: {Counter(i.get('mime_type') for i in itens)}")

    metas = {i["UID"]: montar_metadados(i, base, raiz)[0] for i in itens}
    log(f"Por ano (caminho): {sorted(Counter(m['ano'] for m in metas.values()).items())}")
    log(f"Por ano (created): {sorted(Counter(i['created'][:4] for i in itens).items())}")
    log(f"Por setor: {sorted(Counter(_slug(m['setor']) for m in metas.values()).items())}")

    if ano_minimo:
        itens = [i for i in itens if int(metas[i["UID"]]["ano"]) >= ano_minimo]
        log(f"Filtro ano >= {ano_minimo}: {len(itens)} arquivos")

    if limite:
        itens = itens[:limite]
        log(f"[MODO TESTE] baixando apenas {limite} arquivos")

    resumo, falhas = Counter(), []
    for n, item in enumerate(itens, 1):
        try:
            status = baixar(item, pasta_saida, base, raiz, setor=tipo_doc)
        except Exception as e:
            status = "falhou"
            log(f"ERRO {item['@id']} {e!r}")
        resumo[status] += 1
        if status == "falhou":
            falhas.append(item["@id"])
        if n % 25 == 0:
            log(f"  {n}/{len(itens)} {dict(resumo)}")
        time.sleep(pausa)

    log(f"Resumo: {dict(resumo)}")
    (pasta_saida / "falhas.txt").write_text("\n".join(falhas), encoding="utf-8")

    return {
        "resumo": resumo,
        "falhas": falhas,
        "pasta_saida": pasta_saida,
        "total_listado": total_listado,
    }


# Uso direto como script (opcional)
if __name__ == "__main__":
    executar_crawler(
        base="https://www.ifpb.edu.br",
        raiz="/campus/cajazeiras/ensino/regulamentos/documentos",
        ano_minimo=2000,
        tipo_doc="regulamentos"
    )