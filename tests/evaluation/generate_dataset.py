import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from ragas.testset import TestsetGenerator

load_dotenv()

loader = DirectoryLoader(
    path="pdfs_ifpb_completos/ensino",
    glob="**/*.pdf",
    loader_cls=PyPDFLoader
)

documents = loader.load()

generator_llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
critic_llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

embeddings = HuggingFaceEndpointEmbeddings(
    model=os.getenv("EMBEDDING_MODEL_ID"),
    huggingfacehub_api_token=os.getenv("HF_TOKEN")
)



generator = TestsetGenerator.from_langchain(
    llm=generator_llm,
    embedding_model=embeddings
)

testset = generator.generate_with_langchain_docs(
    documents,
    testset_size=50
)

df = testset.to_pandas()
df.to_csv("tests/evaluation/dataset.csv", index=False)

print(f"Dataset gerado com {len(df)} amostras")