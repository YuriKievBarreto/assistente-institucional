from rag.crawler.crawler_cursos import executar_crawler_cursos
from rag.crawler.crawler_documentos import executar_crawler
from rag.crawler.crawler_paginas import executar_crawler_paginas
from dotenv import load_dotenv
import logging
from app.core.config import settings


links_hubs_cursos = settings.links_hubs_cursos


def execute_all_crawlers():
    load_dotenv()
    tarefas = [
        ("Cursos", lambda: [executar_crawler_cursos(curso) for curso in links_hubs_cursos]),
        ("Editais", lambda: executar_crawler(raiz=settings.RAIZ_CRAWLER_EDITAIS, base=settings.BASE_CRAWLERS, ano_minimo=settings.ANO_MINIMO, tipo_doc="editais")),
        ("Resolucoes", lambda: executar_crawler(raiz=settings.RAIZ_CRAWLER_RESOLUCOES, base=settings.BASE_CRAWLERS, ano_minimo=settings.ANO_MINIMO_RESOLUCOES, tipo_doc="resolucoes")),
        ("Regulamentos", lambda: executar_crawler(raiz=settings.RAIZ_CRAWLER_REGULAMENTOS, base=settings.BASE_CRAWLERS, ano_minimo=settings.ANO_MINIMO_REGULAMENTOS, tipo_doc="regulamentos")),
        ("Paginas", lambda: executar_crawler_paginas(raiz=settings.RAIZ_CRAWLER_PAGINAS, base=settings.BASE_CRAWLERS, ano_minimo_noticias=settings.ANO_MINIMO_NOTICIAS))
    ]

    for nome, tarefa in tarefas:
        try:
            logging.info(f"Iniciando: {nome}")
            tarefa()
        except Exception:
            logging.error(f"Falha fatal em {nome}", exc_info=True)

if __name__ == "__main__":
    execute_all_crawlers()