import os
import re
import time
import hashlib
import json
import requests
import mimetypes
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import trafilatura

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ==========================================
# BLOCO DE LIXO RECORRENTE (CABEÇALHO/MENU DO SITE IFPB)
# ==========================================
CABECALHO_LIXO_IFPB = """Ir para o conteúdo
Ir para a navegação
Ir para o rodapé
Transparência
Concursos
Acesso a Sistemas
Portal da TI
Contatos
Cajazeiras"""

# ==========================================
# FUNÇÕES UTILITÁRIAS
# ==========================================
def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return re.sub(r'\s+', '_', name).strip()[:100]

def gerar_hash_unico(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:5]

def normalize_url(url):
    return url.split('#')[0].rstrip('/')

def extrair_nome_legivel_do_link(a_tag, url_absoluta):
    texto = a_tag.text.strip()
    if texto and texto.lower() not in ['file', 'download', 'baixar', 'clique aqui', 'acesse aqui']:
        return texto
    partes = [p for p in unquote(url_absoluta).split('/') if p]
    if not partes: return "Documento_Sem_Nome"
    if partes[-1].lower() == 'file' and len(partes) >= 3 and '@@download' in partes[-2]: return partes[-3]
    elif '@@download' in partes[-1] and len(partes) >= 2: return partes[-2]
    return partes[-1]

def limpar_cabecalho_lixo(texto_md):
    """
    Remove o bloco fixo de cabeçalho/menu de navegação do site do IFPB
    (CABECALHO_LIXO_IFPB) que o trafilatura está incluindo junto com
    o conteúdo extraído.

    Constrói o padrão linha a linha (em vez de escapar o bloco inteiro de
    uma vez) e junta as linhas com um separador que tolera espaços/tabs
    sobrando antes/depois de cada quebra de linha, já que extrações de
    HTML costumam deixar esses resíduos.
    """
    if not texto_md:
        return texto_md

    linhas = CABECALHO_LIXO_IFPB.split('\n')
    padrao = r'[ \t]*\n[ \t]*'.join(re.escape(linha) for linha in linhas)

    texto_limpo = re.sub(padrao, '', texto_md)
    return texto_limpo.strip()

# ==========================================
# 1. EXTRATOR DE LINKS EXTERNOS
# ==========================================
def salvar_link_como_markdown(url_link, pasta_destino, prefixo, nome_documento, url_pagina_origem):
    if not url_link.startswith('http'): return
    try:
        hash_url = gerar_hash_unico(normalize_url(url_link))
        nome_doc_seguro = sanitize_filename(nome_documento) if nome_documento else "Link_Externo"
        nome_base = f"{prefixo}_{nome_doc_seguro}_{hash_url}"
        
        caminho_md = os.path.join(pasta_destino, f"{nome_base}.md")
        if os.path.exists(caminho_md): return

        with open(caminho_md, 'w', encoding='utf-8') as f:
            f.write(f"# {nome_documento}\n\n**URL Oficial:** {url_link}\n**Origem:** {url_pagina_origem}\n**Tipo:** Link Externo/Sistema")

        metadados = {
            "documento_id": nome_base,
            "titulo_documento": nome_documento if nome_documento else "Link Externo",
            "url_pagina_referencia": url_pagina_origem,
            "url_arquivo_direto": url_link,
            "tipo_documento": "LINK_EXTERNO"
        }
        with open(os.path.join(pasta_destino, f"{nome_base}.json"), 'w', encoding='utf-8') as f_json:
            json.dump(metadados, f_json, ensure_ascii=False, indent=4)
    except Exception:
        pass

# ==========================================
# 2. EXTRATOR DE ARQUIVOS (PDF, DOCX)
# ==========================================
def baixar_arquivo(url_arquivo, pasta_destino, prefixo, nome_documento, url_pagina_origem):
    try:
        download_url = f"{url_arquivo}/@@download/file" if '@@download' not in url_arquivo else url_arquivo
        headers_download = HEADERS.copy()
        headers_download['Accept'] = '*/*'

        resposta = requests.get(download_url, headers=headers_download, stream=True)
        if resposta.status_code != 200: return False

        content_type = resposta.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type: return False

        cd = resposta.headers.get('Content-Disposition', '')
        match = re.search(r'filename="?([^"]+)"?', cd)
        nome_final_arquivo = match.group(1) if match else f"{sanitize_filename(nome_documento)}{mimetypes.guess_extension(content_type.split(';')[0]) or '.pdf'}"

        hash_url = gerar_hash_unico(normalize_url(url_arquivo))
        nome_base, ext = os.path.splitext(sanitize_filename(nome_final_arquivo))
        if not ext: ext = '.pdf'

        nome_base_arquivo = f"{prefixo}_{nome_base}_{hash_url}"
        caminho_salvar = os.path.join(pasta_destino, f"{nome_base_arquivo}{ext}")

        if os.path.exists(caminho_salvar): return True

        print(f"  -> [BAIXANDO ARQUIVO] {nome_base_arquivo[:60]}...")
        with open(caminho_salvar, 'wb') as f:
            for chunk in resposta.iter_content(chunk_size=8192): f.write(chunk)

        metadados = {
            "documento_id": nome_base_arquivo,
            "titulo_documento": nome_documento,
            "url_pagina_referencia": url_pagina_origem,
            "url_arquivo_direto": url_arquivo,
            "tipo_documento": ext.replace('.', '').upper()
        }
        with open(os.path.join(pasta_destino, f"{nome_base_arquivo}.json"), 'w', encoding='utf-8') as f_json:
            json.dump(metadados, f_json, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

# ==========================================
# 3. EXTRATOR DE TEXTO (TRAFILATURA)
# ==========================================
def extrair_html_trafilatura(url_pagina, pasta_destino, prefixo):
    downloaded = trafilatura.fetch_url(url_pagina)
    if not downloaded: return False

    texto_md = trafilatura.extract(downloaded, include_links=True, include_formatting=True, output_format='markdown')
    meta = trafilatura.extract_metadata(downloaded)

    if not texto_md or len(texto_md.strip()) < 50: return False

    # NOVO: remove o bloco de cabeçalho/menu repetitivo (lixo) extraído junto com o conteúdo
    texto_md = limpar_cabecalho_lixo(texto_md)

    # NOVO: se depois de remover o lixo não sobrou conteúdo relevante, descarta a página
    if not texto_md or len(texto_md.strip()) < 50: return False

    titulo = meta.title if meta and meta.title else url_pagina.split('/')[-1]
    hash_url = gerar_hash_unico(url_pagina)
    nome_base = f"{prefixo}_{sanitize_filename(titulo)}_{hash_url}"
    caminho_md = os.path.join(pasta_destino, f"{nome_base}.md")

    if os.path.exists(caminho_md): return True

    with open(caminho_md, 'w', encoding='utf-8') as f: f.write(texto_md)

    dados_json = {
        "documento_id": nome_base,
        "titulo_documento": titulo,
        "descricao": meta.description if meta else "",
        "data_publicacao": meta.date if meta else "",
        "url_pagina_referencia": url_pagina,
        "tipo_documento": "PAGINA_WEB_MD"
    }
    with open(os.path.join(pasta_destino, f"{nome_base}.json"), 'w', encoding='utf-8') as f_json:
        json.dump(dados_json, f_json, ensure_ascii=False, indent=4)
        
    print(f"  -> [TEXTO EXTRAÍDO] {nome_base[:60]}")
    return True

# ==========================================
# O CÉREBRO: OMNI-CRAWLER RECURSIVO
# ==========================================
def rastejar_hub_universal(url_atual, escopo_url, pasta_destino, visited_urls):
    url_atual = normalize_url(url_atual)
    if url_atual in visited_urls: return
    visited_urls.add(url_atual)

    print(f"\n[INSPECIONANDO HUB/PÁGINA] {url_atual}")

    try:
        r = requests.get(url_atual, headers=HEADERS, timeout=15)
        if 'text/html' not in r.headers.get('Content-Type', '').lower(): return
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception:
        return

    # 1. Salva o texto da página atual DENTRO da pasta recebida
    extrair_html_trafilatura(url_atual, pasta_destino, "Hub")

    # 2. Descobre filhos no miolo da página (Main ou Content)
    area_conteudo = soup.find('main') or soup.find(id='content') or soup
    
    for a_tag in area_conteudo.find_all('a', href=True):
        nova_url = normalize_url(urljoin(url_atual, a_tag['href']))
        texto_link = extrair_nome_legivel_do_link(a_tag, nova_url)
        
        # Filtros de Blindagem contra loop infinito do CMS
        if any(param in nova_url for param in ['?b_start', '++theme++', 'login', 'search', 'page=']): continue
        if nova_url in visited_urls: continue

        # --- A TRIAGEM INTELIGENTE ---
        
        # CENA A: É um arquivo explícito (PDF, DOCX, etc) ou um download forçado do Plone?
        if nova_url.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.png', '.jpg')) or '@@download' in nova_url.lower():
            if baixar_arquivo(nova_url, pasta_destino, "Anexo", texto_link, url_atual):
                visited_urls.add(nova_url)
            else:
                salvar_link_como_markdown(nova_url, pasta_destino, "Externo", texto_link, url_atual)
                visited_urls.add(nova_url)
                
        # CENA B: É um link externo ao escopo do HUB? (Ex: SUAP, MEC, ou outra seção do IFPB)
        elif not nova_url.startswith(escopo_url):
            salvar_link_como_markdown(nova_url, pasta_destino, "Externo", texto_link, url_atual)
            visited_urls.add(nova_url)
            
        # CENA C: É uma sub-página ou sub-hub dentro do nosso escopo? (RECURSÃO COM SUB-PASTA)
        else:
            time.sleep(0.3)
            
            # 1. Cria um nome seguro para a nova sub-pasta baseado no texto do link
            nome_sub_pasta = sanitize_filename(texto_link)
            if not nome_sub_pasta: # Fallback caso o link seja apenas uma imagem/ícone sem texto
                nome_sub_pasta = f"Sub_Hub_{gerar_hash_unico(nova_url)}"
                
            # 2. Monta o caminho e cria a pasta no sistema
            nova_pasta_filha = os.path.join(pasta_destino, nome_sub_pasta)
            os.makedirs(nova_pasta_filha, exist_ok=True)
            
            # 3. Mergulha na nova página repassando o caminho recém-criado
            rastejar_hub_universal(nova_url, escopo_url, nova_pasta_filha, visited_urls)

def baixar_da_web(hubs_dict, pasta_destino_base):
    os.makedirs(pasta_destino_base, exist_ok=True)
    visited_urls = set()
    
    for nome_hub, url_hub in hubs_dict.items():
        print(f"\n{'='*50}\nINICIANDO OMNI-CRAWLER NO HUB: {nome_hub}\n{'='*50}")
        
        pasta_do_hub = os.path.join(pasta_destino_base, sanitize_filename(nome_hub))
        os.makedirs(pasta_do_hub, exist_ok=True)
        
        rastejar_hub_universal(url_hub, url_hub, pasta_do_hub, visited_urls)
    
    print("\n[SUCESSO] Varredura Universal Concluída!")