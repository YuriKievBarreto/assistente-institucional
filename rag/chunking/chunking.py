import os
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from typing import Dict, Any

class RAGChunking:
    def __init__(self, datalake_directory) -> None:
        self.datalake_directory = datalake_directory
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_overlap=200,
            chunk_size=600,
            separators=["\n\n", "\n", "###", "##", "#", ".", " ", ""]
        )
        

    def chunk_content(self, markdown_path, json_metadata):
        self.headers_to_split_on = [

                    ("#", "Capitulo"),
                    ("##", "Secao"),
                    ("###", "Subsecao"),

        ]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False
        )

        with open(markdown_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        chunks = markdown_splitter.split_text(md_content)
        final_chunks = self.recursive_splitter.split_documents(chunks)
        
        for chunk in final_chunks:
    # Apenas yield se o chunk tiver conteúdo real (ex: mais de 20 caracteres)
            if len(chunk.page_content.strip()) > 20:
                chunk.metadata.update(json_metadata)
                is_web_page = True if "paginas_web" in markdown_path else False
                chunk.metadata["origem"] = "web" if is_web_page else "edital"
                yield chunk
            else:
                print(f"Pulando chunk irrelevante em: {chunk.metadata.get('titulo')}")

        

        #def chunk_web_pages():