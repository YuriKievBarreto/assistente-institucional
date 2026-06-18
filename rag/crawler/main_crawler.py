from crawler_editais import baixar_editais
from crawler_resolucoes import IFPBCrawlerUnificado
from crawler_info_geral import baixar_da_web


import logging
from dotenv import load_dotenv
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

data_dir = os.getenv("DATALAKE_DIR")

WEB_PAGE_HUBS = {
        "institucional": "https://www.ifpb.edu.br/campus/cajazeiras/institucional",
        "assistencia-estudantil":"https://www.ifpb.edu.br/campus/cajazeiras/assistencia-estudantil",
        "ensino": "https://www.ifpb.edu.br/campus/cajazeiras/ensino",
        "pesquisa": "https://www.ifpb.edu.br/campus/cajazeiras/pesquisa",
        "extensao": "https://www.ifpb.edu.br/campus/cajazeiras/extensao",


        #"conselho-diretor":"https://www.ifpb.edu.br/campus/cajazeiras/conselho-diretor",
        #"acesso-a-informacao": "https://www.ifpb.edu.br/campus/cajazeiras/acesso-a-informacao",


        #"pronatec": "https://www.ifpb.edu.br/campus/cajazeiras/pronatec",
        #"assuntos": "https://www.ifpb.edu.br/campus/cajazeiras/assuntos",
        #"administracao": "https://www.ifpb.edu.br/campus/cajazeiras/administracao",
        
    }

DIRETORIO_WEB_PAGES = f"{data_dir}/paginas_web"

CONFIG_EDITAIS = {

    "ensino": {
        "urls": {
            2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/ensino/editais-2026"
        },
        "caminho": f"{data_dir}/editais/ensino"
    },

    "assistencia_estudantil": {
        "urls": {
            2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/assistencia-estudantil/2026"
        },
        "caminho": f"{data_dir}/editais/assistencia_estudantil"
    },

    "direcao_geral": {
        "urls": {
            2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/direcao-geral/2026"
        },
        "caminho": f"{data_dir}/editais/direcao_geral"
    },

    "extensao": {
        "urls": {
            2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/extensao/2026"
        },
        "caminho": f"{data_dir}/editais/extensao"
    },

    "inovacao": {
        "urls": {
            2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/editais-de-inovacao"
        },
        "caminho": f"{data_dir}/editais/invacao"
    },
    

    "pesquisa": {
        "urls": {
            2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/editais-de-pesquisa/2026",
            2024: "https://www.ifpb.edu.br/campus/cajazeiras/editais/editais-de-pesquisa/2024"
        },
        "caminho": f"{data_dir}/editais/pesquisa"
    },

}



def execute_all_crawlers():
    load_dotenv()
    tarefas = [
        ("Web Pages", lambda: baixar_da_web(WEB_PAGE_HUBS, DIRETORIO_WEB_PAGES)),
        ("Reitoria", lambda: IFPBCrawlerUnificado().executar()),
    ]

    for nome, tarefa in tarefas:
        try:
            logging.info(f"Iniciando: {nome}")
            tarefa()
        except Exception:
            logging.error(f"Falha fatal em {nome}", exc_info=True)

   
    for nome_categoria, conf in CONFIG_EDITAIS.items():
        try:
            logging.info(f"Processando categoria: {nome_categoria}")
            baixar_editais(conf["urls"], conf["caminho"])
        except Exception:
            logging.error(f"Falha na categoria {nome_categoria}", exc_info=True)


    


execute_all_crawlers()

