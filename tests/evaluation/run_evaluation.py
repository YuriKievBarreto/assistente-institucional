import sys
import types
import os
import time
import uuid
import ast
import re
import json
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()
from app.chatbot.models import RAGConfig
# ---------------------------------------------------------------------------
# Shim: o Ragas 0.4.3 ainda tenta importar langchain_community.chat_models.vertexai,
# que foi removido do langchain-community a partir da 0.4.x. Isso intercepta
# esse import e redireciona pro pacote novo, sem precisar mexer em versões.
# ---------------------------------------------------------------------------
from langchain_google_vertexai import ChatVertexAI

fake_module = types.ModuleType("langchain_community.chat_models.vertexai")
fake_module.ChatVertexAI = ChatVertexAI  # type: ignore
sys.modules["langchain_community.chat_models.vertexai"] = fake_module

from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from datasets import Dataset
from ragas import evaluate, RunConfig
from ragas.metrics import context_precision, context_recall, answer_relevancy, faithfulness, answer_correctness
from ragas.llms import LangchainLLMWrapper

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_aws import ChatBedrockConverse
from langchain_core.callbacks import BaseCallbackHandler

# ---------------------------------------------------------------------------
# PATCH: torna o parser do Ragas tolerante a saídas onde o modelo devolve
# MAIS DE UM bloco JSON concatenado (ex: ecoa o schema como
# {"properties": {...}} e, em seguida, os valores reais).
#
# Causa raiz observada (Claude Haiku 4.5, temperature=0): o modelo às vezes
# gera dois blocos {...} no mesmo output. A função extract_json() nativa do
# Ragas já remove cercas ```json corretamente, mas pega só o PRIMEIRO bloco
# {...} do texto -- que no seu caso era o schema ecoado, não a resposta real.
# Com temperature=0 o retry de fix_output_format repetia o mesmo erro sem
# variação (mesma resposta 3x).
#
# Este patch, testado isoladamente antes de entregar:
#   1. remove cercas ```json residuais
#   2. testa TODOS os blocos {...}/[...] candidatos do texto, na ordem,
#      e usa o primeiro que valida contra o schema Pydantic esperado
#   3. se nenhum validar direto, tenta desembrulhar um nível de "properties"
#      (caso o modelo tenha ecoado a estrutura do schema em vez dos valores)
#   4. só cai no fluxo original de fix_output_format se nada disso resolver
# ---------------------------------------------------------------------------
from ragas.prompt.pydantic_prompt import (
    RagasOutputParser,
    fix_output_format_prompt,
    OutputStringAndPrompt,
)
from ragas.prompt.utils import extract_json as _extract_json_original
from ragas.exceptions import RagasOutputParserException
from ragas.callbacks import new_group


def _find_all_json_candidates(text: str) -> list:
    """Retorna todos os blocos {...} ou [...] balanceados encontrados no texto,
    na ordem em que aparecem."""
    candidates = []
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch in "{[":
            open_char = ch
            close_char = "}" if open_char == "{" else "]"
            count = 0
            for j in range(i, n):
                if text[j] == open_char:
                    count += 1
                elif text[j] == close_char:
                    count -= 1
                    if count == 0:
                        candidates.append(text[i:j + 1])
                        i = j
                        break
        i += 1
    return candidates


def _try_unwrap_properties(raw):
    """Se o modelo ecoou a estrutura do schema (ex: {"properties": {"text": "..."}})
    em vez de retornar {"text": "..."} direto, desembrulha um nível."""
    if isinstance(raw, dict) and "properties" in raw and isinstance(raw["properties"], dict):
        return raw["properties"]
    return raw


async def _patched_parse_output_string(
    self, output_string, prompt_value, llm, callbacks, retries_left: int = 1
):
    callbacks = callbacks or []

    cleaned = re.sub(r'^```(?:json)?\s*', '', output_string.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned)

    candidates = _find_all_json_candidates(cleaned)
    if not candidates:
        candidates = [_extract_json_original(cleaned)]

    result = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue

        try:
            result = self.pydantic_object.model_validate(parsed)
            break
        except Exception:
            pass

        try:
            unwrapped = _try_unwrap_properties(parsed)
            result = self.pydantic_object.model_validate(unwrapped)
            break
        except Exception:
            continue

    if result is not None:
        return result

    # nenhum candidato validou -> comportamento original (retry via fix_output_format)
    if retries_left != 0:
        retry_rm, retry_cb = new_group(
            name="fix_output_format",
            inputs={"output_string": output_string},
            callbacks=callbacks,
        )
        fixed_output_string = await fix_output_format_prompt.generate(
            llm=llm,
            data=OutputStringAndPrompt(
                output_string=output_string,
                prompt_value=prompt_value.to_string(),
            ),
            callbacks=retry_cb,
            retries_left=retries_left - 1,
        )
        retry_rm.on_chain_end({"fixed_output_string": fixed_output_string})
        return await _patched_parse_output_string(
            self, fixed_output_string.text, prompt_value, llm, callbacks, retries_left - 1
        )
    else:
        raise RagasOutputParserException()


RagasOutputParser.parse_output_string = _patched_parse_output_string


# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATASET_PATH = "tests/evaluation/datasets/parent_child/dataset_editais_limpo.csv"
CHECKPOINT_PATH = "tests/evaluation/datasets/enriquecimento_table_editais_limpo_haiku_4-5.csv"
RESULTS_PATH = "tests/evaluation/nova_lite_as_judge/enriquecimento_teste_editais_limpo_haiku_4-5.csv"


# ---------------------------------------------------------------------------
# Callback de debug: mostra o prompt enviado e a resposta crua do juiz
# ---------------------------------------------------------------------------
class DebugCallback(BaseCallbackHandler):
    def __init__(self, max_chars=3000):
        self.max_chars = max_chars
        self.call_count = 0

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.call_count += 1
        print("\n" + "=" * 80)
        print(f"[CALL #{self.call_count}] PROMPT ENVIADO AO JUIZ:")
        print("-" * 80)
        texto = prompts[0]
        print(texto[:self.max_chars] + ("... [truncado]" if len(texto) > self.max_chars else ""))
        print("=" * 80)

    def on_llm_end(self, response, **kwargs):
        print(f"\n[CALL #{self.call_count}] RESPOSTA CRUA DO JUIZ:")
        print("-" * 80)
        try:
            texto = response.generations[0][0].text
            print(texto[:self.max_chars] + ("... [truncado]" if len(texto) > self.max_chars else ""))
        except Exception as e:
            print(f"(não consegui extrair texto da resposta: {e})")
            print(response)
        print("=" * 80 + "\n")

    def on_llm_error(self, error, **kwargs):
        print(f"\n[CALL #{self.call_count}] *** ERRO NO LLM ***: {error}\n")


# ---------------------------------------------------------------------------
# FASE 1 — Retrieval + geração de respostas (mantida igual ao original)
# ---------------------------------------------------------------------------


def format_context_for_evaluation(docs: list[Document]) -> list[Document]:
        formatted = []

        allowed_metadata = [
            "titulo_documento",
            "Capitulo",
            "descricao",
            "ano",
            "data_publicacao",
            "url_pagina_referencia",
            "url_arquivo_direto"
        ]

        for doc in docs:
            content = doc.page_content
            meta = doc.metadata or {}

            meta_lines = [
                f"{key}: {meta[key]}"
                for key in allowed_metadata
                if key in meta
            ]

            meta_str = "\n".join(meta_lines)

            formatted.append(
                Document(
                    page_content=
                    f"Metadata:\n{meta_str}\n\n"
                    f"Context:\n{content}"
                )
                
                
            )

        print("aaaaaaaaaaaaaaaaaaaaaa")
        print(formatted[0])

        
        print("formatando....")

        return formatted

def limpar_html(texto: str) -> str:
    return BeautifulSoup(texto, "html.parser").get_text(separator=" ").strip()


def gerar_respostas() -> pd.DataFrame:
    if os.path.exists(CHECKPOINT_PATH):
        print(f">> Checkpoint encontrado em '{CHECKPOINT_PATH}', pulando geração...")
        df = pd.read_csv(CHECKPOINT_PATH)
        df["contexts"] = df["contexts"].apply(ast.literal_eval)
        print(f">> {len(df)} perguntas carregadas do checkpoint.")
        return df

    from app.chatbot.memory import MemoryManager
    from app.chatbot.engine import ChatEngine
    from app.dependencies import get_retriever, get_config

    print(">> Nenhum checkpoint encontrado. Carregando dataset original...")
    df = pd.read_csv(DATASET_PATH)
    print(f">> {len(df)} perguntas carregadas de '{DATASET_PATH}'.")

    retriever = get_retriever()
    answers, contexts = [], []

    print(">> Iniciando retrieval + geração de respostas...")
    start_total = time.time()
    MAX_RETRIES = 5

    for i, question in enumerate(tqdm(df["question"], desc="Processando perguntas")):
        t0 = time.time()
        for attempt in range(MAX_RETRIES):
            try:
                session_id = f"ragas-eval-{uuid.uuid4()}"
                memory = MemoryManager(session_id=session_id)
                chat_engine = ChatEngine(memory, get_config(), retriever)

                docs = retriever._multi_query_retrieve(question)
                formatted_docs = format_context_for_evaluation(docs)
                print("---"*15)
                print("NA AVALIACAO: \n\n\n", formatted_docs[0])
                print("---"*15)
                doc_texts = [doc.page_content for doc in formatted_docs]
                answer = limpar_html(chat_engine.chat(question))

                contexts.append(doc_texts)
                answers.append(answer)

                elapsed = time.time() - t0
                print(f"[{i + 1}/{len(df)}] OK ({elapsed:.1f}s) - {question[:60]}...")
                break
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = (
                    "429" in error_msg
                    or "rate limit" in error_msg.lower()
                    or "rate_limit_exceeded" in error_msg.lower()
                )
                if is_rate_limit and attempt < MAX_RETRIES - 1:
                    match = re.search(r"try again in ([\d.]+)s", error_msg)
                    wait = float(match.group(1)) + 0.5 if match else min(5 * (2 ** attempt), 30)
                    print(f"[{i + 1}/{len(df)}] Rate limit. Tentando de novo em {wait:.1f}s ({attempt + 1}/{MAX_RETRIES})...")
                    time.sleep(wait)
                    continue

                elapsed = time.time() - t0
                print(f"[{i + 1}/{len(df)}] ERRO ({elapsed:.1f}s): {e}")
                contexts.append([])
                answers.append("")
                break

    total_elapsed = time.time() - start_total
    print(f">> Geração concluída em {total_elapsed / 60:.1f} min.")

    df["contexts"] = contexts
    df["answer"] = answers
    df.to_csv(CHECKPOINT_PATH, index=False)
    print(f">> Checkpoint salvo em '{CHECKPOINT_PATH}'.")
    return df


# ---------------------------------------------------------------------------
# FASE 2 — Avaliação Ragas (Haiku 4.5 + Converse + patch de parsing + debug opcional)
# ---------------------------------------------------------------------------
def rodar_avaliacao(df: pd.DataFrame, debug: bool = False, limitar_n: int = None) -> None:
    print(">> Convertendo para formato Ragas...")

    if limitar_n:
        df = df.head(limitar_n)
        print(f">> MODO DEBUG: usando apenas as primeiras {limitar_n} linhas.")

    eval_dataset = Dataset.from_pandas(df)

    print(">> Configurando LLM juiz e embeddings...")

    callbacks = [DebugCallback()] if debug else []

    bedrock_llm = ChatBedrockConverse(
        model="amazon.nova-lite-v1:0",
        region_name="us-east-1",
        temperature=0.2,       # >0 para permitir variação nos retries de fix_output_format
        max_tokens=4096,       # evita truncamento de JSON
        callbacks=callbacks,   # mostra prompt/resposta crus quando debug=True
    )

    evaluator_llm = LangchainLLMWrapper(bedrock_llm)

    embeddings = HuggingFaceEndpointEmbeddings(
        model=os.getenv("EMBEDDING_MODEL_ID"),
        huggingfacehub_api_token=os.getenv("HF_TOKEN"),
    )

    print(">> Rodando avaliação Ragas (isso pode demorar)...")
    start_eval = time.time()

    result = evaluate(
        eval_dataset,
        metrics=[context_precision, 
                 context_recall, 
                 answer_relevancy, 
                 faithfulness,
                 answer_correctness],
        llm=evaluator_llm,
        embeddings=embeddings,
        run_config=RunConfig(
            max_workers=1 if debug else 10,  # sequencial no debug; até 10 em produção
            max_retries=10,
            max_wait=90,
            timeout=300,
        ),
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

    # Etapa 1 (opcional): valide com poucas perguntas + debug antes de rodar tudo
    # rodar_avaliacao(df, debug=True, limitar_n=5)

    # Etapa 2: dataset completo, sem debug, com mais workers
    rodar_avaliacao(df, debug=False, limitar_n=None)