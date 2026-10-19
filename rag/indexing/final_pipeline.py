from rag.crawler.main_crawler import execute_all_crawlers
from rag.extraction.document_loader import ConversorRAGMarkdown
from rag.indexing.ingest import ingest_pipeline
from app.core.config import settings

import logging


# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # 1. Carrega configs
    
    data_dir = settings.DATALAKE_DIR
    
    # 2. Pipeline com tratamento de erro global
    try:
        logging.info("Iniciando fase de Crawling...")
        execute_all_crawlers() 
        
        logging.info("Iniciando conversão para Markdown...")
        ConversorRAGMarkdown(data_dir).processar_datalake()
        
        logging.info("Iniciando ingestão no banco vetorial...")
        ingest_pipeline(data_dir)
        
        logging.info("Pipeline finalizado com sucesso.")
        
    except Exception as e:
        logging.error(f"Falha fatal no pipeline: {e}", exc_info=True)


if __name__ == "__main__":
    main()