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

# ==========================================
# UTILITÁRIOS E NOMEAÇÃO INTELIGENTE
# ==========================================
def sanitize_filename(name, max_length=60):
    """Apenas limpa a string, troca espaços por hífen e corta no limite exato (sem adicionar hash)."""
    name = name.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', '-', name).strip('-')
    
    if len(name) > max_length:
        name = name[:max_length].strip('-')
    return name

def gerar_hash_unico(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:5]

def montar_nome_arquivo_final(prefixo_edital, nome_documento, url_referencia):
    """Monta o nome do arquivo balanceando o tamanho do Pai e do Filho para nunca estourar."""
    hash_url = gerar_hash_unico(url_referencia)
    
    # O nome do documento tem mais prioridade de leitura, ganha 50 caracteres
    nome_limpo = sanitize_filename(nome_documento, max_length=50) if nome_documento else "Documento"
    
    if prefixo_edital:
        # O nome da pasta/hub é apenas contexto, ganha 30 caracteres
        prefixo_limpo = sanitize_filename(prefixo_edital, max_length=30)
        nome_base = f"{prefixo_limpo}---{nome_limpo}"
    else:
        nome_base = nome_limpo
        
    # Resultado: max 30 + 3 + 50 + 1 + 5 = ~89 caracteres totais. Muito seguro!
    return f"{nome_base}-{hash_url}"

def normalize_url(url):
    url = url.split('#')[0].rstrip('/')
    url = url.replace('/@@download/file', '').replace('/@@download', '')
    return url

def extrair_nome_legivel_do_link(a_tag, url_absoluta):
    texto = a_tag.text.strip()
    if texto and texto.lower() not in ['file', 'download', 'baixar', 'clique aqui', 'acesse aqui']:
        return texto
    partes = [p for p in unquote(url_absoluta).split('/') if p]
    if not partes: return "Documento-Sem-Nome"
    if partes[-1].lower() == 'file' and len(partes) >= 3 and '@@download' in partes[-2]: return partes[-3]
    elif '@@download' in partes[-1] and len(partes) >= 2: return partes[-2]
    return partes[-1]

# ==========================================
# FUNÇÕES DE SALVAMENTO DE DADOS
# ==========================================
def salvar_link_como_markdown(url_link, pasta_destino, prefixo_edital, nome_documento, ano, url_pagina_origem, descricao="", data_publicacao=""):
    if not url_link.startswith('http'): return
    try:
        url_link_norm = normalize_url(url_link)
        
        # USA O NOVO MONTADOR DE NOMES
        nome_base_arquivo = montar_nome_arquivo_final(prefixo_edital, nome_documento, url_link_norm)
        
        caminho_salvar = os.path.join(pasta_destino, f"{nome_base_arquivo}.md")
        caminho_json = os.path.join(pasta_destino, f"{nome_base_arquivo}.json")

        if os.path.exists(caminho_salvar): return

        print(f"    🔗 [SALVANDO LINK EXTERNO] {nome_base_arquivo}...")
        with open(caminho_salvar, 'w', encoding='utf-8') as f:
            f.write(f"# {nome_documento}\n\n**Edital Relacionado:** {prefixo_edital}\n**URL Oficial:** {url_link}\n**Tipo:** Link / Formulário Externo")

        metadados = {"documento_id": nome_base_arquivo, "ano": ano, "edital_pai": prefixo_edital if prefixo_edital else "Geral", "titulo_documento": nome_documento if nome_documento else "Link Externo", "descricao": descricao, "data_publicacao": data_publicacao, "url_pagina_referencia": url_pagina_origem, "url_arquivo_direto": url_link, "tipo_documento": "LINK_EXTERNO"}
        with open(caminho_json, 'w', encoding='utf-8') as f_json: json.dump(metadados, f_json, ensure_ascii=False, indent=4)
    except Exception:
        pass

def tentar_baixar_arquivo(url_arquivo, pasta_destino, prefixo_edital, nome_documento, ano, url_pagina_origem, descricao="", data_publicacao=""):
    try:
        url_normalizada = normalize_url(url_arquivo)
        download_url = f"{url_arquivo}/@@download/file" if '@@download' not in url_arquivo else url_arquivo
        resposta = requests.get(download_url, headers=HEADERS, stream=True)
        
        if resposta.status_code != 200: return False, url_normalizada

        content_type = resposta.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type: return False, url_normalizada

        nome_final_arquivo = None
        match = re.search(r'filename="?([^"]+)"?', resposta.headers.get('Content-Disposition', ''))
        if match: nome_final_arquivo = match.group(1)
        if not nome_final_arquivo: nome_final_arquivo = f"{sanitize_filename(nome_documento) or 'Documento'}{mimetypes.guess_extension(content_type.split(';')[0]) or '.pdf'}"

        # Descobre a extensão real do arquivo
        _, ext = os.path.splitext(sanitize_filename(nome_final_arquivo))
        if not ext: ext = '.pdf'

        # USA O NOVO MONTADOR DE NOMES (Passando o nome do arquivo bruto e a url)
        nome_base_arquivo = montar_nome_arquivo_final(prefixo_edital, nome_final_arquivo.replace(ext, ''), url_normalizada)
        
        caminho_salvar = os.path.join(pasta_destino, f"{nome_base_arquivo}{ext}")
        caminho_json = os.path.join(pasta_destino, f"{nome_base_arquivo}.json")

        if os.path.exists(caminho_salvar): return True, None

        print(f"    📄 [BAIXANDO ARQUIVO] {nome_base_arquivo}{ext}...")
        with open(caminho_salvar, 'wb') as f:
            for chunk in resposta.iter_content(chunk_size=8192): f.write(chunk)

        metadados = {"documento_id": nome_base_arquivo, "ano": ano, "edital_pai": prefixo_edital if prefixo_edital else "Geral", "titulo_documento": nome_documento if nome_documento else nome_final_arquivo, "descricao": descricao, "data_publicacao": data_publicacao, "url_pagina_referencia": url_pagina_origem, "url_arquivo_direto": url_arquivo, "tipo_documento": ext.replace('.', '').upper()}
        with open(caminho_json, 'w', encoding='utf-8') as f_json: json.dump(metadados, f_json, ensure_ascii=False, indent=4)
        return True, None
    except Exception:
        return False, normalize_url(url_arquivo)

# ==========================================
# CÉREBRO: OMNI-ROUTER RECURSIVO
# ==========================================
def vasculhar_pagina_recursivamente(url_pagina, pasta_atual, visited_urls, ano, url_raiz_crawler, is_root=False):
    url_pagina = normalize_url(url_pagina)
    if url_pagina in visited_urls: return
    visited_urls.add(url_pagina)

    print(f"\n{'='*70}")
    print(f"🔎 [INSPECIONANDO] {url_pagina}")
    print(f"📂 [PASTA ATUAL]   {pasta_atual}")
    print(f"{'='*70}")
    
    # O título seguro da pasta atual agora serve de Prefixo para os arquivos!
    titulo_seguro = os.path.basename(pasta_atual)
    mapa_metadados_visuais = {} 
    
    try:
        resposta = requests.get(url_pagina, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resposta.text, 'html.parser') if resposta.status_code == 200 else None
            
        if soup:
            tabela_previa = soup.find('table', class_='edital-items-table')
            if tabela_previa:
                print("  -> [DEBUG] Tabela de editais detectada na página!")
                for tr in tabela_previa.find_all('tr'):
                    tds = tr.find_all('td')
                    if not tds: continue
                    a_tag = tds[0].find('a', href=True)
                    if not a_tag: continue
                    u_abs = normalize_url(urljoin(url_pagina, a_tag['href']))
                    mapa_metadados_visuais[u_abs] = {
                        "descricao": tds[1].get_text(strip=True) if len(tds) > 1 else "",
                        "data": tds[2].get_text(strip=True) if len(tds) > 2 else ""
                    }
    except Exception as e:
        print(f"  -> [ERRO HTTP] Falha ao ler a página: {e}")
        soup = None

    # =================================================================
    # FASE ÚNICA: VARREDURA GERAL HTML
    # =================================================================
    if soup:
        area_conteudo = soup.find('main') or soup.find(id='content') or soup
        links_encontrados = area_conteudo.find_all('a', href=True)
        print(f"  -> [DEBUG] {len(links_encontrados)} links brutos encontrados na área de conteúdo.")

        for a_tag in links_encontrados:
            href = a_tag['href']
            
            if any(p in href for p in ["?b_start", "++theme++", "login", "search", "?page="]): 
                continue
                
            url_abs = normalize_url(urljoin(url_pagina, href))
            
            if url_abs == url_pagina or url_abs in visited_urls: 
                continue
            
            texto_link = extrair_nome_legivel_do_link(a_tag, url_abs)

            # É ARQUIVO BINÁRIO?
            if url_abs.lower().endswith(('.pdf', '.docx', '.xlsx', '.zip', '.rar')) or '@@download' in url_abs.lower():
                is_file, u_final = tentar_baixar_arquivo(url_abs, pasta_atual, titulo_seguro, texto_link, ano, url_pagina)
                visited_urls.add(url_abs)
                continue

            # É SUB-HUB?
            if url_abs.startswith(url_raiz_crawler) and len(url_abs) > len(url_pagina):
                print(f"  -> 🌟 [SUB-HUB ENCONTRADO] '{texto_link}'")
                
                # As pastas também ganham o limite mais brando para nomeação segura (50 caracteres)
                nome_pasta_filha = sanitize_filename(texto_link, max_length=50)
                if not nome_pasta_filha: nome_pasta_filha = f"Sub-Hub-{gerar_hash_unico(url_abs)}"
                
                nova_pasta_filha = os.path.join(pasta_atual, nome_pasta_filha)
                os.makedirs(nova_pasta_filha, exist_ok=True)
                print(f"  -> 📁 [PASTA CRIADA] {nova_pasta_filha}")
                
                time.sleep(0.5)
                vasculhar_pagina_recursivamente(url_abs, nova_pasta_filha, visited_urls, ano, url_raiz_crawler, is_root=False)
                visited_urls.add(url_abs)

# ==========================================
# ENTRYPOINT DO CRAWLER
# ==========================================
def baixar_editais(urls_anos, pasta_destino):
    os.makedirs(pasta_destino, exist_ok=True)
    visited_urls = set()
    
    for ano, url_ano in urls_anos.items():
        print(f"\n{'='*70}")
        print(f"🚀 INICIANDO VARREDURA PARAMETRIZADA: {ano}")
        print(f"{'='*70}")
        
        pasta_do_ano = os.path.join(pasta_destino, str(ano))
        os.makedirs(pasta_do_ano, exist_ok=True)
        
        url_raiz_limpa = normalize_url(url_ano)
        
        vasculhar_pagina_recursivamente(
            url_pagina=url_raiz_limpa, 
            pasta_atual=pasta_do_ano, 
            visited_urls=visited_urls, 
            ano=ano, 
            url_raiz_crawler=url_raiz_limpa, 
            is_root=True
        )

    print("\n[✅ SUCESSO] Ingestão e Mapeamento Concluídos!")

if __name__ == "__main__":
    TEST_URLS = { 2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/extensao/2026" }
    TEST_PASTA = "pdfs_ifpb_completos/testes"
    baixar_editais(TEST_URLS, TEST_PASTA)