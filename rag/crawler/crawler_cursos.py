import json
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse
from app.core.config import settings
import requests
from bs4 import BeautifulSoup, NavigableString

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": UA}

# h3 que marcam o início do rodapé: ao encontrar um deles, a extração termina
H3_RODAPE = {"assuntos", "serviços", "servicos", "redes sociais", "navegação", "navegacao"}
# linhas que mudam a cada acesso ou não pertencem ao curso
RUIDO = re.compile(r"^(última alteração|ultima alteração|voltar para o topo|> voltar)", re.I)


def _limpa(texto):
    texto = texto.replace("(abre em nova janela)", "")
    return re.sub(r"\s+", " ", texto).strip()


def _links_para_markdown(soup, url_base):
    """Troca <a> por [texto](url absoluta). Links internos (#...) viram texto
    puro, ou somem se forem só um item de índice (ex.: '1º Semestre')."""
    for a in list(soup.find_all("a")):
        if a.decomposed:
            continue
        texto = _limpa(a.get_text(" "))
        href = (a.get("href") or "").strip()
        if not texto:
            a.decompose()
            continue
        if not href or href.startswith(("#", "javascript:", "<")):
            li = a.find_parent("li")
            if li is not None and _limpa(li.get_text(" ")) == texto:
                li.decompose()  # item de índice interno da página
            else:
                a.replace_with(NavigableString(texto))
            continue
        a.replace_with(NavigableString(f"[{texto}]({urljoin(url_base, href)})"))


def extrair_curso(url, ignorar=("Formas de Acesso",), timeout=(10, 60)):
    """
    Extrai apenas o conteúdo do curso (sem cabeçalho, menus e rodapé).

    A âncora é o <h2> com o nome do curso: tudo que vem antes dele (barra gov.br,
    menus, breadcrumb) é descartado, e a leitura para no primeiro <h3> do rodapé.

    Retorna {"url", "curso_id", "titulo", "secoes": {nome: [linhas]}}.
    """
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    _links_para_markdown(soup, url)

    titulo_tag = soup.find("h2")
    if titulo_tag is None:
        raise ValueError(f"Nenhum <h2> encontrado em {url}; a estrutura mudou?")

    secoes = {"Resumo": []}  # chips do topo: modalidade, tipo, campus, turno
    atual = "Resumo"
    capturados = set()

    for el in titulo_tag.find_all_next(True):
        if el.name == "h3":
            nome = _limpa(el.get_text(" "))
            if nome.lower() in H3_RODAPE:
                break
            if nome.lower().startswith("perfil"):
                nome = "Descrição"
            atual = nome
            secoes.setdefault(atual, [])
            continue

        if el.name not in ("p", "li", "tr", "h4"):
            continue
        # evita duplicar (ex.: <li><p>texto</p></li>)
        if any(id(pai) in capturados for pai in el.parents):
            continue

        if el.name == "tr":
            celulas = [_limpa(c.get_text(" ")) for c in el.find_all(["th", "td"])]
            linha = " | ".join(c for c in celulas if c)
        else:
            linha = _limpa(el.get_text(" "))
        if not linha or RUIDO.match(linha):
            continue

        capturados.add(id(el))
        if el.name == "h4":
            linha = f"**{linha}**"
        elif el.name == "li":
            linha = f"- {linha}"
        elif el.name == "tr":
            linha = f"| {linha} |"
        secoes[atual].append(linha)

    ignorar = {i.lower() for i in ignorar}
    secoes = {k: v for k, v in secoes.items() if v and k.lower() not in ignorar}

    m = re.search(r"/cursos/(\d+)", url)
    return {
        "url": url,
        "curso_id": int(m.group(1)) if m else None,
        "titulo": _limpa(titulo_tag.get_text(" ")),
        "secoes": secoes,
    }


def curso_para_markdown(curso):
    partes = [f"# {curso['titulo']}", f"Fonte: {curso['url']}"]
    for nome, linhas in curso["secoes"].items():
        partes.append(f"## {nome}\n" + "\n".join(linhas))
    return "\n\n".join(partes) + "\n"


PASTA_SAIDA_PADRAO = settings.DATALAKE_DIR / "cursos"


# ==========================================
# LISTAGEM
# ==========================================
def listar_cursos(url_lista, timeout=(10, 60), max_paginas=50, pausa=0.3):
    """
    Lê a página de listagem (com os filtros que você quiser na query string) e
    devolve ({curso_id: {...}}, total_declarado). Segue o link de "próxima página"
    se existir; na listagem testada (6 cursos) não havia paginação.
    """
    cursos, visitadas, total_declarado = {}, set(), None
    url = url_lista
    while url and url not in visitadas and len(visitadas) < max_paginas:
        visitadas.add(url)
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        if total_declarado is None:
            m = re.search(r"Mostrando\s+(\d+)\s+Curso", soup.get_text(" "))
            total_declarado = int(m.group(1)) if m else None

        for a in soup.find_all("a", href=True):
            abs_url = urljoin(url, a["href"])
            m = re.fullmatch(r"/cursos/(\d+)/?", urlparse(abs_url).path)
            if m:
                cid = int(m.group(1))
                cursos.setdefault(cid, {
                    "curso_id": cid,
                    "url": abs_url,
                    "descricao_listagem": _limpa(a.get_text(" ")),
                })

        prox = soup.find("a", rel="next") or soup.find(
            "a", string=re.compile(r"próxim|next|›|»", re.I))
        href = prox.get("href", "") if prox else ""
        url = urljoin(url, href) if href and not href.startswith("#") else None
        time.sleep(pausa)

    return cursos, total_declarado


# ==========================================
# FUNÇÃO PRINCIPAL (para importar na pipeline)
# ==========================================
def executar_crawler_cursos(
    url_lista,
    pasta_saida=None,
    atualizar=False,
    pausa=0.5,
    verbose=True,
):
    """
    Lista os cursos de `url_lista`, entra em cada um e salva
    <pasta_saida>/<curso_id>.md e .json (metadados + seções extraídas).

    atualizar=False pula cursos já salvos; use True para refazer (as páginas
    mudam, a de ADS mostrava "última alteração há 3 dias").
    Retorna {"resumo", "falhas", "pasta_saida", "total_listado", "total_declarado"}.
    """
    def log(msg):
        if verbose:
            print(msg)

    pasta = Path(pasta_saida) if pasta_saida else PASTA_SAIDA_PADRAO
    pasta.mkdir(parents=True, exist_ok=True)

    cursos, total_declarado = listar_cursos(url_lista)
    log(f"Cursos encontrados: {len(cursos)} (página declara: {total_declarado})")
    if total_declarado is not None and total_declarado != len(cursos):
        log("ATENÇÃO: contagem diferente da declarada; pode haver paginação não seguida.")

    resumo, falhas = Counter(), []
    for cid, info in sorted(cursos.items()):
        md = pasta / f"{cid}.md"
        js = md.with_suffix(".json")
        if not atualizar and md.exists() and js.exists():
            resumo["pulado"] += 1
            continue
        try:
            curso = extrair_curso(info["url"])
            md.write_text(curso_para_markdown(curso), encoding="utf-8")
            meta = {**info, "titulo": curso["titulo"], "secoes": curso["secoes"]}
            js.write_text(json.dumps(meta, ensure_ascii=False, indent=4), encoding="utf-8")
            resumo["salvo"] += 1
            log(f"  [{cid}] {curso['titulo']}")
        except Exception as e:
            resumo["falhou"] += 1
            falhas.append(info["url"])
            log(f"  ERRO {info['url']}: {e!r}")
        time.sleep(pausa)

    log(f"Resumo: {dict(resumo)}")
    (pasta / "falhas.txt").write_text("\n".join(falhas), encoding="utf-8")
    return {
        "resumo": resumo,
        "falhas": falhas,
        "pasta_saida": pasta,
        "total_listado": len(cursos),
        "total_declarado": total_declarado,
    }


if __name__ == "__main__":
    executar_crawler_cursos(
        "https://estudante.ifpb.edu.br/cursos/?cidade=11&nivel_formacao=GRADUACAO"
    )