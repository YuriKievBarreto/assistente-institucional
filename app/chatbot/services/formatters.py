from langchain_core.documents import Document

class DocumentFormatter:
    """
    Serviço utilitário responsável por formatar documentos e metadados 
    em representações de texto para consumo no prompt do LLM.
    """
    DEFAULT_ALLOWED_METADATA = [
        "titulo_documento",
        "Capitulo",
        "descricao",
        "ano",
        "data_publicacao",
        "url_pagina_referencia",
        "url_arquivo_direto"
    ]

    @staticmethod
    def format_context(docs: list[Document]) -> str:
        """Formata apenas o conteúdo textual dos documentos."""
        return "\n\n".join(doc.page_content for doc in docs)

    @classmethod
    def format_context_with_metadata(
        cls, 
        docs: list[Document], 
        allowed_metadata: list[str] = None
    ) -> str:
        """Formata o texto acompanhado dos metadados permitidos para o prompt do LLM."""
        allowed = allowed_metadata or cls.DEFAULT_ALLOWED_METADATA
        formatted = []

        for doc in docs:
            content = doc.page_content
            meta = doc.metadata or {}

            meta_lines = [
                f"{key}: {meta[key]}"
                for key in allowed
                if key in meta
            ]

            meta_str = "\n".join(meta_lines)
            formatted.append(f"Metadata:\n{meta_str}\n\nContext:\n{content}")

        return "\n\n---\n\n".join(formatted)
