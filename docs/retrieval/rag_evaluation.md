# Registro de Otimizações do RAG

## Objetivo

Melhorar a qualidade da recuperação e da geração de respostas do chatbot de editais do IFPB.

Framework de avaliação: RAGAS

---

# Linha de base

**Data:** 03/07/2026

### Configuração

- PyMuPDF4LLM
- Preservação da hierarquia do documento
- MarkdownHeaderTextSplitter
- Bedrock Embeddings
- Dense Retrieval

### Resultados

| Métrica | Valor |
|---------|------:|
| Context Precision | 0.6600 |
| Context Recall | 0.6800 |
| Answer Relevancy | 0.2900 |

### Observações

- A recuperação frequentemente não encontra o artigo correto.

---

# Experimento 1
**Data:** 03/07/2026

## Hybrid Search + melhoria no Chunking

### Alterações

- Adicionado BM25
- Hybrid Search
- aumento no chunk size para 800 com 100 de overlap

### Resultados usando amazon nova micro como judge

| Métrica | Antes | Depois | Δ |
|---------|-------:|--------:|--:|
| Context Precision | 0.6600 | 0.7440 | +12,7% |
| Context Recall | 0.6800 | 0.7386 | +8,6% |
| Answer Relevancy | 0.2900 | 0.4251 | +46,6% |

### Análise

O Hybrid Search aumentou significativamente a qualidade da recuperação.

O maior ganho ocorreu em **Answer Relevancy**, indicando que a melhoria na recuperação teve impacto direto na resposta final.


---

# Experimento 2

## LLMs de maior porte

### Alterações

- Avaliação com RAGAS usando três modelos diferentes pra responder a perguntas: Amazon Nova Lite, Claude Haiku 4.5, Llama 4 Scout
- Mudança do modelo de julgamento anterior: Amazon Nova Micro → Amazon Nova Lite
- Adição da métrica **Faithfulness** (não avaliada no experimento anterior)

### Hipótese

Melhorar o parâmetro **Answer Relevancy** após o uso de um modelo de maior porte tanto na entrada (sistema RAG) quanto na avaliação (Judge LLM com RAGAS)

### Resultados — Judge: Amazon Nova Micro

| Métrica | Baseline | Nova Lite | Δ | Llama 4 Scout | Δ | Claude Haiku 4.5 | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Context Precision | 0,7440 | 0,7618 | +2,4% | 0,7412 | -0,4% | 0,7511 | +1,0% |
| Context Recall | 0,7440 | 0,7386 | -0,7% | 0,7386 | -0,7% | 0,7386 | -0,7% |
| Answer Relevancy | 0,4251 | 0,4010 | -5,7% | 0,3593 | -15,5% | 0,3446 | -18,9% |
| Faithfulness | NA | 0,5301 | NA | 0,5275 | NA | 0,5907 | NA |

### Resultados — Judge: Amazon Nova Lite

| Métrica | Baseline | Nova Lite | Δ | Llama 4 Scout | Δ | Claude Haiku 4.5 | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Context Precision | 0,7440 | 0,5825 | -21,7% | 0,5759 | -22,6% | 0,5776 | -22,4% |
| Context Recall | 0,7440 | 0,7010 | -5,8% | 0,7010 | -5,8% | 0,7059 | -5,1% |
| Answer Relevancy | 0,4251 | 0,4576 | +7,6% | 0,3961 | -6,8% | 0,3439 | -19,1% |
| Faithfulness | NA | 0,4926 | NA | 0,4691 | NA | 0,5861 | NA |


### Análise

O modelo **Claude Haiku 4.5** apresenta o maior **faithfulness** entre os três avaliados (0,59 com Nova Micro / 0,59 com Nova Lite), confirmando que o modelo é mais criterioso ao basear respostas no contexto — inventa menos. No entanto, esse comportamento tem um custo direto no **answer_relevancy** (0,34), o mais baixo dos três modelos.


Os resultados sugerem que o **Amazon Nova Lite** adota um critério de avaliação mais rigoroso para algumas métricas, especialmente Context Precision, atribuindo notas sistematicamente inferiores às obtidas **pelo Amazon Nova Micro**. Esse comportamento pode ser desejável em cenários nos quais se pretende reduzir avaliações excessivamente otimistas e adotar um processo de validação mais conservador.

## análise no documento de resultados do claude haiku 4.5
A análise por caso revela que os 9 zeros de `answer_relevancy` correspondem a perguntas onde o Haiku recusou responder mesmo com contexto parcialmente disponível — especialmente perguntas sobre tabelas grandes (Anexo I do PROMIFPB, resultado IVS) cujos dados foram truncados pelo chunking. Nesses casos o `faithfulness` é alto (1.0) porque o modelo não inventou nada, mas a resposta vazia penaliza a relevância.

Os 12 zeros de `context_precision` e 15 de `context_recall` concentram-se nos mesmos documentos: resultados tabelados do IVS, PAPE e informações do Conselho Diretor — evidenciando que o principal gargalo atual é o **chunking de tabelas longas**, e não o modelo ou o retriever. **O parent-child chunking é a melhoria com maior potencial de impacto nessa etapa.**

A tensão entre `faithfulness` e `answer_relevancy` é esperada em sistemas com prompt de recusa explícita: um modelo que honestamente declara não ter informação suficiente terá faithfulness alto e relevancy baixo. Para um assistente institucional onde respostas incorretas têm consequências reais para os usuários, esse trade-off é aceitável e defensável.

### Observações
- Valores "NA" na coluna baseline para Faithfulness: métrica incluída pela primeira vez nesta rodada, sem comparação anterior.
- O judge Amazon Nova Lite produziu scores de `context_precision` sistematicamente mais baixos (~22%) que o Nova Micro para todos os modelos avaliados, sugerindo que o Nova Lite é mais rigoroso na avaliação de relevância dos chunks recuperados.
- Os zeros concentrados em perguntas sobre tabelas confirmam que o chunking é o próximo passo crítico — não o modelo nem o retriever.


---


# Experimento 3 (Corrigido)
**Data:** 04/07/2026

## Multiquery + Reranker

### Hipótese
- Multiquery → melhora **context recall** (mais chances de recuperar o chunk certo com fraseamentos diferentes).
- Reranker → melhora **context precision** (filtra ruído trazido pela busca vetorial/sparse).
- Como consequência, esperados também aumentos em **Answer Relevancy** e **Faithfulness**: no Exp. 2, respostas vazias/recusas vinham de contexto truncado (tabelas); recuperação melhor deve reduzir recusas e invenções.

### Alterações
- Adicionado multiquery retrieval (k = 3)
- Adicionado reranker (top_k = 5)
- Mudança no top_k de documentos retornados por query individual: 5 → 10

### Configuração de recuperação
Retornando 10 documentos por query × 4 (query original + multiquery) = 40 candidatos → **reranker seleciona os top 5**

---

### Resultados do Claude Haiku 4.5, usando Amazon Nova Lite como judge

#### Reranker: `ms-marco-MiniLM-L-6-v2`

| Métrica | Antes | Depois | Δ |
|---|---:|---:|---:|
| Context Precision | 0,5776 | 0,5107 | **-11,58%** |
| Context Recall | 0,7059 | 0,6617 | **-6,26%** |
| Answer Relevancy | 0,2900 | 0,3627 | **+25,07%** |
| Faithfulness | 0,3439 | 0,8924 | **+159,49%** |

#### Reranker: `BAAI/bge-reranker-v2-m3`

| Métrica | Antes | Depois | Δ |
|---|---:|---:|---:|
| Context Precision | 0,5776 | 0,7952 | **+37,67%** |
| Context Recall | 0,7059 | 0,8774 | **+24,30%** |
| Answer Relevancy | 0,2900 | 0,4274 | **+47,38%** |
| Faithfulness | 0,3439 | 0,8611 | **+150,39%** |

---

### Análise

- **A hipótese se confirma de forma consistente apenas com o `BAAI/bge-reranker-v2-m3`**, que melhorou as quatro métricas simultaneamente: Context Precision (+37,67%), Context Recall (+24,30%), Answer Relevancy (+47,38%) e Faithfulness (+150,39%). Isso é coerente com a hipótese original — o multiquery amplia a cobertura de recuperação e o reranker, sendo mais robusto, consegue filtrar bem o ruído entre os 40 candidatos.

- **O `ms-marco-MiniLM-L-6-v2` contraria a hipótese em duas das quatro métricas.** Context Precision (-11,58%) e Context Recall (-6,26%) pioraram em relação à baseline, mesmo com mais candidatos disponíveis para o rerank (40 documentos). Isso sugere que esse reranker específico não está ordenando bem os candidatos vindos do multiquery — provavelmente por ser um modelo mais leve e genérico, menos adequado ao domínio institucional/normativo dos editais, enquanto o BGE-reranker-v2-m3 é maior e treinado em conjuntos mais diversos.

- **O salto em Faithfulness é o resultado mais chamativo do experimento**, em ambos os rerankers (+159,49% e +150,39%). Isso indica que ter candidatos filtrados por relevância — mesmo quando a precisão piora, como no caso do MiniLM — reduz fortemente a tendência do modelo de "inventar" respostas, já que ele está trabalhando com um conjunto de contexto mais bem selecionado do que a busca vetorial/BM25 bruta trazia sozinha.


- **Próximo passo:** fixar BGE-reranker-v2-m3 e testar parent-child chunking (gargalo já identificado no Exp. 2).


