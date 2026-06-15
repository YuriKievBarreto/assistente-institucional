import os
import re
import time
import hashlib
import requests
import mimetypes
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def sanitize_filename(name):
    """Remove caracteres inválidos, limita o tamanho e substitui espaços por hifens."""
    name = name.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    
    # Substitui sequências de espaços em branco por um único hífen
    name = re.sub(r'\s+', '-', name).strip('-')
    
    # Limita o tamanho para evitar o erro de "Path Too Long" (260 chars) do Windows
    if len(name) > 60:
        # Pega os primeiros 50 caracteres e adiciona um hash para manter a unicidade
        name = name[:50].strip('-') + "-" + hashlib.md5(name.encode('utf-8')).hexdigest()[:5]
        
    return name

def normalize_url(url):
    """Remove âncoras (#) e barras sobrando."""
    url = url.split('#')[0].rstrip('/')
    url = url.replace('/@@download/file', '').replace('/@@download', '')
    return url

def extrair_nome_legivel_do_link(a_tag, url_absoluta):
    """Tenta pegar um nome útil. Se falhar, disseca a URL do Plone para achar o nome real."""
    texto = a_tag.text.strip()
    
    if texto and texto.lower() not in ['file', 'download', 'baixar', 'clique aqui', 'acesse aqui']:
        return texto
        
    partes = [p for p in unquote(url_absoluta).split('/') if p]
    if not partes:
        return "Documento-Sem-Nome"
        
    if partes[-1].lower() == 'file' and len(partes) >= 3 and '@@download' in partes[-2]:
        return partes[-3]
    elif '@@download' in partes[-1] and len(partes) >= 2:
        return partes[-2]
        
    return partes[-1]

def gerar_hash_unico(url):
    """Gera uma assinatura curta e única baseada na URL."""
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:5]

def salvar_link_como_markdown(url_link, pasta_destino, prefixo_edital, nome_documento, ano, url_pagina_origem, descricao="", data_publicacao=""):
    """Cria um arquivo .md contendo o link e o seu respectivo manifesto JSON de metadados."""
    if not url_link.startswith('http'): return

    try:
        url_link_norm = normalize_url(url_link)
        hash_url = gerar_hash_unico(url_link_norm)
        nome_doc_seguro = sanitize_filename(nome_documento) if nome_documento else "Link-Externo"
        
        if prefixo_edital:
            nome_base_arquivo = f"{prefixo_edital}---{nome_doc_seguro}-{hash_url}"
        else:
            nome_base_arquivo = f"{nome_doc_seguro}-{hash_url}"
            
        caminho_salvar = os.path.join(pasta_destino, f"{nome_base_arquivo}.md")
        caminho_json = os.path.join(pasta_destino, f"{nome_base_arquivo}.json")

        if os.path.exists(caminho_salvar): return

        print(f"  -> [SALVANDO LINK MD] {nome_base_arquivo[:60]}...")
        conteudo_md = f"# {nome_documento}\n\n**Edital Relacionado:** {prefixo_edital}\n**URL Oficial:** {url_link}\n**Tipo:** Link / Formulário Externo"
        
        with open(caminho_salvar, 'w', encoding='utf-8') as f:
            f.write(conteudo_md)

        metadados = {
            "documento_id": nome_base_arquivo,
            "ano": ano,
            "edital_pai": prefixo_edital if prefixo_edital else "Geral",
            "titulo_documento": nome_documento if nome_documento else "Link Externo",
            "descricao": descricao,
            "data_publicacao": data_publicacao,
            "url_pagina_referencia": url_pagina_origem,
            "url_arquivo_direto": url_link,
            "tipo_documento": "LINK_EXTERNO"
        }
        with open(caminho_json, 'w', encoding='utf-8') as f_json:
            json.dump(metadados, f_json, ensure_ascii=False, indent=4)

    except Exception:
        pass

def tentar_baixar_arquivo(url_arquivo, pasta_destino, prefixo_edital, nome_documento, ano, url_pagina_origem, descricao="", data_publicacao=""):
    """Tenta baixar o arquivo binário e salva o manifesto JSON de metadados ao lado com descrição e data."""
    try:
        download_url = f"{url_arquivo}/@@download/file" if '@@download' not in url_arquivo else url_arquivo
        headers_download = HEADERS.copy()
        headers_download['Accept'] = '*/*'

        resposta = requests.get(download_url, headers=headers_download, stream=True)
        
        if resposta.status_code != 200:
            resp_fallback = requests.get(url_arquivo, headers=HEADERS)
            return False, resp_fallback.url

        content_type = resposta.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            return False, resposta.url 

        nome_final_arquivo = None
        cd = resposta.headers.get('Content-Disposition', '')
        match = re.search(r'filename="?([^"]+)"?', cd)
        if match:
            nome_final_arquivo = match.group(1)

        if not nome_final_arquivo:
            extensao = mimetypes.guess_extension(content_type.split(';')[0]) or '.pdf'
            nome_doc_seguro = sanitize_filename(nome_documento) if nome_documento else "Documento"
            nome_final_arquivo = f"{nome_doc_seguro}{extensao}"

        url_normalizada = normalize_url(url_arquivo)
        hash_url = gerar_hash_unico(url_normalizada)
        
        nome_doc_seguro = sanitize_filename(nome_final_arquivo)
        nome_base, ext = os.path.splitext(nome_doc_seguro)
        if not ext: ext = '.pdf'

        if prefixo_edital:
            nome_base_arquivo = f"{prefixo_edital}---{nome_base}-{hash_url}"
        else:
            nome_base_arquivo = f"{nome_base}-{hash_url}"
            
        caminho_salvar = os.path.join(pasta_destino, f"{nome_base_arquivo}{ext}")
        caminho_json = os.path.join(pasta_destino, f"{nome_base_arquivo}.json")

        if os.path.exists(caminho_salvar):
            print(f"  -> [PULANDO] Já baixado: {nome_base_arquivo[:60]}...")
            return True, None

        print(f"  -> [BAIXANDO ARQUIVO] {nome_base_arquivo[:60]}...")
        with open(caminho_salvar, 'wb') as f:
            for chunk in resposta.iter_content(chunk_size=8192):
                f.write(chunk)

        metadados = {
            "documento_id": nome_base_arquivo,
            "ano": ano,
            "edital_pai": prefixo_edital if prefixo_edital else "Geral",
            "titulo_documento": nome_documento if nome_documento else nome_base,
            "descricao": descricao,
            "data_publicacao": data_publicacao,
            "url_pagina_referencia": url_pagina_origem,
            "url_arquivo_direto": url_arquivo,
            "tipo_documento": ext.replace('.', '').upper()
        }
        with open(caminho_json, 'w', encoding='utf-8') as f_json:
            json.dump(metadados, f_json, ensure_ascii=False, indent=4)
                
        return True, None
                
    except Exception as e:
        return False, url_arquivo

def vasculhar_pagina_recursivamente(url_pagina, pasta_pai, visited_urls, ano, is_root=False):
    """Spider absoluto: Lida com HTML, API paginada e extração em tabelas."""
    url_pagina = normalize_url(url_pagina)
    
    if url_pagina in visited_urls: return
    visited_urls.add(url_pagina)

    print(f"\n[INSPECIONANDO] {url_pagina}")
    
    pasta_atual = pasta_pai
    titulo_seguro = ""
    mapa_metadados_visuais = {} 
    
    try:
        resposta = requests.get(url_pagina, headers=HEADERS)
        soup = BeautifulSoup(resposta.text, 'html.parser') if resposta.status_code == 200 else None
        
        if not is_root and soup:
            h1 = soup.find('h1', class_='documentFirstHeading')
            titulo = h1.text.strip() if h1 else unquote(url_pagina.split('/')[-1])
            titulo_seguro = sanitize_filename(titulo)
            
            # Previne a criação de pastas duplicadas com nomes idênticos no meio do caminho
            if titulo_seguro in pasta_pai:
                pasta_atual = pasta_pai
            else:
                pasta_atual = os.path.join(pasta_pai, titulo_seguro)
                
            os.makedirs(pasta_atual, exist_ok=True)
            
        if soup:
            tabela_previa = soup.find('table', class_='edital-items-table')
            if tabela_previa:
                for tr in tabela_previa.find_all('tr'):
                    tds = tr.find_all('td')
                    if not tds: continue
                    a_tag = tds[0].find('a', href=True)
                    if not a_tag: continue
                    
                    raw_u = urljoin(url_pagina, a_tag['href'])
                    u_abs = normalize_url(raw_u)
                    
                    desc_vis = tds[1].get_text(strip=True) if len(tds) > 1 else ""
                    data_vis = tds[2].get_text(strip=True) if len(tds) > 2 else ""
                    
                    mapa_metadados_visuais[u_abs] = {
                        "descricao": desc_vis,
                        "data": data_vis
                    }
    except Exception:
        soup = None

    url_com_barra = url_pagina if url_pagina.endswith('/') else url_pagina + '/'

    # =================================================================
    # FASE 1: RASPAGEM VIA API
    # =================================================================
    if "https://www.ifpb.edu.br" in url_pagina:
        api_url = url_pagina.replace("https://www.ifpb.edu.br", "https://www.ifpb.edu.br/++api++")
        b_start = 0
        limit = 25
        total_itens = 9999

        while b_start < total_itens:
            url_paginada = f"{api_url}?b_start={b_start}&b_size={limit}"
            try:
                headers_api = HEADERS.copy()
                headers_api["Accept"] = "application/json"
                r_api = requests.get(url_paginada, headers=headers_api)
                if r_api.status_code != 200: break
                dados = r_api.json()
            except Exception:
                break

            itens = dados.get("items", [])
            total_itens = dados.get("items_total", 0)

            if not itens: break
            if total_itens > limit and b_start > 0:
                print(f"  -> [PAGINAÇÃO DA API] Processando itens {b_start} a {min(b_start+limit, total_itens)}...")

            for item in itens:
                tipo = item.get("@type", "")
                titulo = item.get("title", "")
                href = item.get("@id", "")
                if href: href = normalize_url(href.replace("/++api++", ""))
                
                if not href or href == url_pagina or href in visited_urls:
                    continue

                meta_visual = mapa_metadados_visuais.get(href, {})
                descricao = meta_visual.get("descricao") or item.get("description", "")
                data_pub = meta_visual.get("data")
                
                if not data_pub:
                    data_pub = item.get("effective", "")
                    if not data_pub or "1969" in data_pub:
                        data_pub = item.get("created", item.get("modified", ""))

                if tipo in ["File", "Document"]:
                    tentar_baixar_arquivo(href, pasta_atual, titulo_seguro, titulo, ano, url_pagina, descricao, data_pub)
                    visited_urls.add(href)
                elif tipo == "Link":
                    salvar_link_como_markdown(href, pasta_atual, titulo_seguro, titulo, ano, url_pagina, descricao, data_pub)
                    visited_urls.add(href)
                elif tipo in ["Folder", "News Item", "Collection"]:
                    if href.startswith(url_com_barra):
                        print(f"  -> [RECURSÃO API] Sub-página encontrada: {titulo[:40]}")
                        vasculhar_pagina_recursivamente(href, pasta_atual, visited_urls, ano, is_root=False)

            b_start += limit
            time.sleep(0.3)

    # =================================================================
    # FASE 2: RASPAGEM HTML
    # =================================================================
    if soup:
        tabela = soup.find('table', class_='edital-items-table')
        if tabela:
            for tr in tabela.find_all('tr'):
                tds = tr.find_all('td')
                if not tds: continue 
                
                a_tag = tds[0].find('a', href=True)
                if not a_tag: continue
                
                descricao_texto = tds[1].get_text(strip=True) if len(tds) > 1 else ""
                data_texto = tds[2].get_text(strip=True) if len(tds) > 2 else ""

                if any(param in a_tag.get('href', '') for param in ["?b_start", "++theme++", "?page="]): continue
                
                raw_url = urljoin(url_pagina, a_tag['href'])
                url_abs = normalize_url(raw_url)
                if url_abs in visited_urls: continue
                
                texto_link = extrair_nome_legivel_do_link(a_tag, url_abs)
                is_file, u_final = tentar_baixar_arquivo(url_abs, pasta_atual, titulo_seguro, texto_link, ano, url_pagina, descricao_texto, data_texto)
                
                if not is_file:
                    if not u_final.startswith("https://www.ifpb.edu.br"):
                        salvar_link_como_markdown(u_final, pasta_atual, titulo_seguro, texto_link, ano, url_pagina, descricao_texto, data_texto)
                    elif u_final.startswith(url_com_barra) and u_final != url_pagina:
                        if not any(param in u_final for param in ["?b_start", "++theme++", "?page="]):
                            print(f"  -> [RECURSÃO HTML] Entrando em: {texto_link[:40]}")
                            vasculhar_pagina_recursivamente(u_final, pasta_atual, visited_urls, ano, is_root=False)
                    else:
                        salvar_link_como_markdown(u_final, pasta_atual, titulo_seguro, texto_link, ano, url_pagina, descricao_texto, data_texto)
                visited_urls.add(url_abs)

        area_conteudo = soup.find('main') or soup.find(id='content') or soup
        for a_tag in area_conteudo.find_all('a', href=True):
            if any(param in a_tag.get('href', '') for param in ["?b_start", "++theme++", "?page="]): continue
            raw_url = urljoin(url_pagina, a_tag['href'])
            url_abs = normalize_url(raw_url)
            
            if url_abs in visited_urls: continue
            texto_link = extrair_nome_legivel_do_link(a_tag, url_abs)
            
            if url_abs.lower().endswith(('.pdf', '.docx', '.xlsx')) or '@@download' in url_abs.lower():
                is_file, u_final = tentar_baixar_arquivo(url_abs, pasta_atual, titulo_seguro, texto_link, ano, url_pagina)
                if not is_file and not u_final.startswith("https://www.ifpb.edu.br"):
                    salvar_link_como_markdown(u_final, pasta_atual, titulo_seguro, texto_link, ano, url_pagina)
                visited_urls.add(url_abs)
                
            elif url_abs.startswith(url_com_barra) and url_abs != url_pagina:
                try:
                    req_teste = requests.get(url_abs, headers=HEADERS, timeout=10)
                    if not req_teste.url.startswith("https://www.ifpb.edu.br"):
                        salvar_link_como_markdown(req_teste.url, pasta_atual, titulo_seguro, texto_link, ano, url_pagina)
                    else:
                        vasculhar_pagina_recursivamente(req_teste.url, pasta_atual, visited_urls, ano, is_root=False)
                except Exception:
                    pass
                visited_urls.add(url_abs)
                time.sleep(0.5)

def baixar_editais(urls_anos, pasta_destino):
    """Assinatura parametrizada para receber os escopos dinamicamente do script orquestrador."""
    os.makedirs(pasta_destino, exist_ok=True)
    visited_urls = set()
    
    for ano, url_ano in urls_anos.items():
        print(f"\n{'='*50}\nINICIANDO VARREDURA PARAMETRIZADA DE {ano}\n{'='*50}")
        pasta_do_ano = os.path.join(pasta_destino, str(ano))
        os.makedirs(pasta_do_ano, exist_ok=True)
        
        vasculhar_pagina_recursivamente(url_ano, pasta_do_ano, visited_urls, ano, is_root=True)

    print("\n[SUCESSO] Ingestão e Mapeamento de Metadados Concluídos!")

if __name__ == "__main__":
    TEST_URLS = { 2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/ensino/editais-2026" }
    TEST_PASTA = "pdfs_ifpb_completos/testes"
    baixar_editais(TEST_URLS, TEST_PASTA)