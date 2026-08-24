from typing import Protocol
from langchain_core.documents import Document

class VectorRepositoryInterface(Protocol):
    def hybrid_search(self, query: str, limit: int = 10) -> list[Document]:
        ...

    def get_parents_by_ids(self, parents_ids: list[str], collection_name: str = "ifpb_parents") -> list[Document]:
        ...