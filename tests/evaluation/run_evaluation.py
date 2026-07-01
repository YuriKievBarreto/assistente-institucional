import sys
import types
import os
import time
import uuid
import ast

# ---------------------------------------------------------------------------
# Shim: o Ragas 0.4.3 ainda tenta importar langchain_community.chat_models.vertexai,
# que foi removido do langchain-community a partir da 0.4.x. Isso intercepta
# esse import e redireciona pro pacote novo, sem precisar mexer em versões.
# ---------------------------------------------------------------------------
from langchain_google_vertexai import ChatVertexAI
from bs4 import BeautifulSoup

fake_module = types.ModuleType("langchain_community.chat_models.vertexai")
fake_module.ChatVertexAI = ChatVertexAI  # type: ignore
sys.modules["langchain_community.chat_models.vertexai"] = fake_module

import pandas as pd
from langchain_groq import ChatGroq
from tqdm import tqdm
from datasets import Dataset
from openai import OpenAI
from ragas import evaluate, RunConfig
from ragas.llms import llm_factory
from ragas.metrics import context_precision, context_recall, answer_relevancy

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.chatbot.memory import MemoryManager
from app.chatbot.engine import ChatEngine
from app.dependencies import get_retriever

from langchain_aws import ChatBedrock

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATASET_PATH = "tests/evaluation/dataset_ragas_editais_ifpb.csv"
CHECKPOINT_PATH = "tests/evaluation/dataset_com_respostas.csv"
RESULTS_PATH = "tests/evaluation/results.csv"


# ---------------------------------------------------------------------------
# FASE 1 — Retrieval + geração de respostas (com checkpoint)
# ---------------------------------------------------------------------------


def limpar_html(texto: str) -> str:
    return BeautifulSoup(texto, "html.parser").get_text(separator=" ").strip()

def gerar_respostas() -> pd.DataFrame:
    if os.path.exists(CHECKPOINT_PATH):
        print(f">> Checkpoint encontrado em '{CHECKPOINT_PATH}', pulando geração...")
        df = pd.read_csv(CHECKPOINT_PATH)
        df["contexts"] = df["contexts"].apply(ast.literal_eval)
        print(f">> {len(df)} perguntas carregadas do checkpoint.")
        return df

    print(">> Nenhum checkpoint encontrado. Carregando dataset original...")
    df = pd.read_csv(DATASET_PATH)
    print(f">> {len(df)} perguntas carregadas de '{DATASET_PATH}'.")

    retriever = get_retriever()

    answers = []
    contexts = []

    print(">> Iniciando retrieval + geração de respostas...")
    start_total = time.time()

    for i, question in enumerate(tqdm(df["question"], desc="Processando perguntas")):
        t0 = time.time()
        try:
            session_id = f"ragas-eval-{uuid.uuid4()}"
            memory = MemoryManager(session_id=session_id)
            chat_engine = ChatEngine(rag_retriever=retriever, memory_manager=memory)

            docs = retriever.retrieve(question)
            doc_texts = [doc.page_content for doc in docs]
            contexts.append(doc_texts)

            answer = limpar_html(chat_engine.chat(question))
            answers.append(answer)

            elapsed = time.time() - t0
            print(f"[{i + 1}/{len(df)}] OK ({elapsed:.1f}s) - {question[:60]}...")

        except Exception as e:
            elapsed = time.time() - t0
            print(f"[{i + 1}/{len(df)}] ERRO ({elapsed:.1f}s): {e}")
            contexts.append([])
            answers.append("")

    total_elapsed = time.time() - start_total
    print(f">> Geração concluída em {total_elapsed / 60:.1f} min.")

    df["contexts"] = contexts
    df["answer"] = answers

    df.to_csv(CHECKPOINT_PATH, index=False)
    print(f">> Checkpoint salvo em '{CHECKPOINT_PATH}'.")

    return df


# ---------------------------------------------------------------------------
# FASE 2 — Avaliação Ragas
# ---------------------------------------------------------------------------
def rodar_avaliacao(df: pd.DataFrame) -> None:
    print(">> Convertendo para formato Ragas...")
    eval_dataset = Dataset.from_pandas(df)

    print(">> Configurando LLM juiz e embeddings...")
    llm_judge = ChatBedrock(model="amazon.nova-micro-v1:0",
                            api_key=os.getenv("BEDROCK_API_KEY"),
                            model_kwargs={"temperature": 0},
                            region="us-east-1" 
                            )
    embeddings = HuggingFaceEndpointEmbeddings(
        model=os.getenv("EMBEDDING_MODEL_ID"),
        huggingfacehub_api_token=os.getenv("HF_TOKEN"),
    )

    print(">> Rodando avaliação Ragas (isso pode demorar)...")
    start_eval = time.time()

    result = evaluate(
        eval_dataset,
        metrics=[context_precision, context_recall, answer_relevancy],
        llm=llm_judge,
        embeddings=embeddings,
        run_config=RunConfig(
            max_retries=5,
            max_wait=60,
            timeout=120
        )
    )

    eval_elapsed = time.time() - start_eval
    print(f">> Avaliação concluída em {eval_elapsed / 60:.1f} min.")

    print(result)
    result.to_pandas().to_csv(RESULTS_PATH, index=False)
    print(f">> Resultados salvos em '{RESULTS_PATH}'.")
# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df = gerar_respostas()
    rodar_avaliacao(df)