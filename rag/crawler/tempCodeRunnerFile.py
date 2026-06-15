from crawler_editais import baixar_editais
from crawler_resolucoes import IFPBCrawlerUnificado
from crawler_info_geral import baixar_da_web

URLS_CONSUPER = {
    2026: "https://site.com/2026"
}

URLS_ASSISTENCIA_ESTUDANTIL = {
    2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/assistencia-estudantil/2026",
    #2025: "https://outro-site.com/2025",
}

URLS_DIRECAO_GERAL = {
    2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/direcao-geral/2026" 
    #2025: "https://outro-site.com/2025",
}
URLS_ENSINO = {
    2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/ensino/editais-2026"
    #2025: "https://outro-site.com/2025",
}

URLS_EXTENSAO = {
    2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/extensao/2026"
    #2025: "https://outro-site.com/2025",
}

URLS_INOVACAO = {
    2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/editais-de-inovacao"
    #2025: "https://outro-site.com/2025",
}


URLS_PESQUISA = {
    2026: "https://www.ifpb.edu.br/campus/cajazeiras/editais/editais-de-pesquisa/2026",
    2024: "https://www.ifpb.edu.br/campus/cajazeiras/editais/editais-de-pesquisa/2024"
}


WEB_PAGE_HUBS = {
        "institucional": "https://www.ifpb.edu.br/campus/cajazeiras/institucional",
        #"assistencia-estudantil":"https://www.ifpb.edu.br/campus/cajazeiras/assistencia-estudantil",
        #"ensino": "https://www.ifpb.edu.br/campus/cajazeiras/ensino",
        #"pesquisa": "https://www.ifpb.edu.br/campus/cajazeiras/pesquisa",
        #"extensao": "https://www.ifpb.edu.br/campus/cajazeiras/extensao",


        #"conselho-diretor":"https://www.ifpb.edu.br/campus/cajazeiras/conselho-diretor",
        #"acesso-a-informacao": "https://www.ifpb.edu.br/campus/cajazeiras/acesso-a-informacao",


        #"pronatec": "https://www.ifpb.edu.br/campus/cajazeiras/pronatec",
        #"assuntos": "https://www.ifpb.edu.br/campus/cajazeiras/assuntos",
        #"administracao": "https://www.ifpb.edu.br/campus/cajazeiras/administracao",
        
    }

DIRETORIO_WEB_PAGES = "pdfs_ifpb_completos/paginas_web"





## Páginas Web
baixar_da_web(WEB_PAGE_HUBS, DIRETORIO_WEB_PAGES)


## Editais
"""
baixar_editais(URLS_ASSISTENCIA_ESTUDANTIL, "pdfs_ifpb_completos/editais/assistencia_estudantil")
baixar_editais(URLS_DIRECAO_GERAL, "pdfs_ifpb_completos/editais/direcao_geral")
baixar_editais(URLS_ENSINO, "pdfs_ifpb_completos/editais/ensino")
baixar_editais(URLS_EXTENSAO, "pdfs_ifpb_completos/editais/extensao")
baixar_editais(URLS_INOVACAO, "pdfs_ifpb_completos/editais/invacao")
baixar_editais(URLS_PESQUISA, "pdfs_ifpb_completos/editais/pesquisa")

## Resoluções consuper
IFPBCrawlerUnificado().executar()
"""

