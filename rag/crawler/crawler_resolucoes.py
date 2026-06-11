import requests
import os
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class IFPBCrawlerUnificado:

    def __init__(self):
        self.base_url = "https://www.ifpb.edu.br"

        self.session = requests.Session()
        # O cabeçalho 'Accept: application/json' força o Plone 6 a devolver os dados estruturados via RestAPI
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json" 
        })

        self.ano_urls = {
            #2025: {
               # "ad_referendum": "https://www.ifpb.edu.br/orgaoscolegiados/consuper/resolucoes/2025/resolucoes-ad-referendum",
                #"aprovadas": "https://www.ifpb.edu.br/orgaoscolegiados/consuper/resolucoes/2025/resolucoes-aprovadas-pelo-colegiado"
           # },
            2026: {
                "ad_referendum": "https://www.ifpb.edu.br/orgaoscolegiados/consuper/resolucoes/2026/resolucoes-ad-referendum",
                "aprovadas": "https://www.ifpb.edu.br/orgaoscolegiados/consuper/resolucoes/2026/resolucoes-aprovadas-pelo-colegiado"
            }
        }

    def extrair_numero(self, texto_link, url_path):
        padroes = [
            r'(?:nº|no|n)[\s_]*(\d+)',
            r'(?:ar|ad)[\s_]*(\d+)',
            r'(?:resolução|resolucao|res)[\s_]*(\d+)',
        ]
        
        for p in padroes:
            m = re.search(p, texto_link.lower(), re.IGNORECASE)
            if m:
                return int(m.group(1))
                
        slug = url_path.rstrip("/").split("/")[-1]
        for p in padroes:
            m = re.search(p, slug.lower(), re.IGNORECASE)
            if m:
                return int(m.group(1))
                
        m = re.search(r'^(\d+)(?:\.pdf)?$', slug.lower())
        if m:
            return int(m.group(1))
            
        return 9999

    def extrair_links_via_api(self, url_base, ano, categoria):
        links_unicos = set()
        resolucoes = []
        
        # Inicia a busca a partir do item 0
        b_start = 0
        limit = 25 # Padrão da API do Plone
        total_itens = 9999 # Valor temporário

        while b_start < total_itens:
            # Transforma a URL web na URL da API
            api_url = url_base.replace("https://www.ifpb.edu.br/", "https://www.ifpb.edu.br/++api++/")
            url_paginada = f"{api_url}?b_start={b_start}&b_size={limit}"
            
            print(f"    Buscando dados via API (offset: {b_start})...")

            try:
                r = self.session.get(url_paginada, timeout=30)
                r.raise_for_status()
                dados = r.json()
            except Exception as e:
                print(f"Erro ao acessar API na página: {e}")
                break

            # A chave 'items' contém a lista de documentos daquela pasta
            itens = dados.get("items", [])
            total_itens = dados.get("items_total", 0)

            if not itens:
                break
                
            for item in itens:
                tipo_item = item.get("@type", "")
                
                # Aceita tipos 'File', 'Link' ou 'Document' que possam conter os arquivos
                if tipo_item not in ["File", "Document", "Link"]:
                    continue

                titulo = item.get("title", "")
                descricao = item.get("description", "").strip() # Captura a ementa do documento
                href = item.get("@id", "").replace("/++api++", "")
                
                # Ignora a pasta pai ou caminhos internos não úteis
                if href == url_base:
                    continue

                # Identifica se é resolução
                is_resolucao = "resoluco" in href.lower() or "resolucao" in href.lower() or "ar-" in href.lower() or ".pdf" in href.lower()
                if not is_resolucao:
                    # Tenta validar pelo titulo
                    if "resolução" not in titulo.lower() and "resolucao" not in titulo.lower():
                        continue

                # No Plone 6, o download nativo via API de arquivos é a própria URL seguida de /@@download/file
                if tipo_item == "File" and "@@download" not in href:
                    href_download = href + "/@@download/file"
                else:
                    href_download = href

                if href_download in links_unicos:
                    continue

                links_unicos.add(href_download)
                numero = self.extrair_numero(titulo, href)

                resolucoes.append({
                    "ano": ano,
                    "numero": str(numero),
                    "categoria": categoria,
                    "url_download": href_download,
                    "url_original": href,
                    "nome_exibicao": titulo,
                    "descricao": descricao
                })
                
            b_start += limit
            time.sleep(0.3)

        resolucoes.sort(key=lambda x: int(x["numero"]) if x["numero"].isdigit() else 9999)
        return resolucoes

    def buscar_resolucoes(self, ano):
        todas = []
        urls_vistas = set()

        for categoria, url in self.ano_urls[ano].items():
            print(f"\n-> {categoria}")
            resolucoes = self.extrair_links_via_api(url, ano, categoria)

            for r in resolucoes:
                if r["url_download"] not in urls_vistas:
                    urls_vistas.add(r["url_download"])
                    todas.append(r)

        return todas

    def baixar_pdf(self, resolucao, output_base="pdfs_ifpb_completos"):
        ano = resolucao["ano"]
        categoria = resolucao["categoria"]
        pasta = os.path.join(output_base, str(ano), categoria)
        os.makedirs(pasta, exist_ok=True)

        # ---------------------------------------------------------
        # LÓGICA DE NOMENCLATURA: Usando o nome original limpo
        # ---------------------------------------------------------
        nome_original = resolucao.get("nome_exibicao", "").strip()
        
        # Limpa caracteres que o sistema operacional não aceita em nomes de arquivos
        nome_original = re.sub(r'[\\/*?:"<>|]', "", nome_original)
        
        # Fallback de segurança caso o título original venha vazio ou muito grande
        if not nome_original or len(nome_original) > 150:
            slug = resolucao["url_original"].rstrip("/").split("/")[-1]
            nome_original = slug.replace(".pdf", "")
            # Evita nomes nativos do Plone como fallback principal
            if nome_original in ["@@download", "file", "view", ""]:
                nome_original = f"resolucao_{resolucao['numero'].zfill(4)}"

        # Nome final do arquivo PDF e do Manifesto JSON
        arquivo = f"{nome_original}.pdf"
        caminho = os.path.join(pasta, arquivo)

        if os.path.exists(caminho):
            return

        url_principal = resolucao["url_download"]
        urls_para_tentar = [url_principal]

        if "/@@download/file" in url_principal:
            urls_para_tentar.append(url_principal.replace("/@@download/file", "/at_download/file"))
            urls_para_tentar.append(url_principal.replace("/@@download/file", ""))

        sucesso = False
        
        # O download do binário não exige o cabeçalho "Accept: application/json"
        header_download = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        for url_teste in urls_para_tentar:
            try:
                r = requests.get(url_teste, headers=header_download, timeout=30)
                if r.status_code == 200 and r.content.startswith(b"%PDF"):
                    
                    # 1. Salva o arquivo binário do PDF
                    with open(caminho, "wb") as f:
                        f.write(r.content)
                    
                    # 2. Cria o manifesto de Metadados para o Qdrant/RAG
                    caminho_json = caminho.replace(".pdf", ".json")
                    metadados_rag = {
                        "ano": int(ano),
                        "categoria": categoria,
                        "numero_resolucao": resolucao.get("numero"),
                        "titulo_documento": nome_original,
                        "descricao_ementa": resolucao.get("descricao", ""),
                        "url_referencia": resolucao.get("url_original"),
                        "url_download_direto": url_teste
                    }
                    
                    with open(caminho_json, "w", encoding="utf-8") as f_json:
                        json.dump(metadados_rag, f_json, ensure_ascii=False, indent=4)

                    print(f"OK -> {arquivo} (+ metadados JSON)")
                    sucesso = True
                    break 

            except requests.RequestException:
                continue

        if not sucesso:
            print(f"Falha ao baixar (Não é PDF válido ou Link 404): {arquivo} | URL: {url_principal}")

    def processar_ano(self, ano):
        print("\n" + "=" * 60)
        print(f"PROCESSANDO ANO {ano}")
        print("=" * 60)

        resolucoes = self.buscar_resolucoes(ano)
        print(f"\nTotal único encontrado em {ano}: {len(resolucoes)}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.baixar_pdf, r)
                for r in resolucoes
            ]
            for _ in as_completed(futures):
                pass

    def executar(self):
        for ano in sorted(self.ano_urls):
            self.processar_ano(ano)
            time.sleep(1)

if __name__ == "__main__":
    IFPBCrawlerUnificado().executar()