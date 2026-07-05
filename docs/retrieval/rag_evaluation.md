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
- Chunks muito grandes reduzem a qualidade das respostas. ##mexer nisso

---

# Experimento 1
**Data:** 03/07/2026

## Hybrid Search + melhoria no Chunking

### Alterações

- Adicionado BM25
- Hybrid Search (0.6 BM25 / 0.4 Dense) ##mexer nisso
- Artigos nunca são divididos entre chunks

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


# Experimento 3
**Data:** 04/07/2026

## Multiquery + Reranker

## Hipótese:
Esperada **melhora no context recall** através do multiquery -  perguntas com fraseamento diferente do documento original passam a ter mais chance de recuperar o chunk certo

Esperada **melhora context precision** - Reranker filtra os candidatos trazidos pelo multiquery, removendo ruído que a busca vetorial/sparse trouxe só por similaridade superficial

### Alterações

- adicionado multiquery retrieval(k = 3)
- adicionado reranker(top_k = 5)
- 

### Resultados do Claude Haiku 4.5 usando amazon nova lite como judge
## retornando 10 documentos por query x 4 vindos da multiquery = 40 -> *reranker seleciona top 5*


| Métrica | Antes | Depois | Δ |
|---|---:|---:|---:|
| Context Precision | 0,5776 | 0,6112 | **+5,8%** |
| Context Recall | 0,7059 | 0,8039 | **+13,9%** |
| Answer Relevancy | 0,2900 | 0,3135 | **+8,1%** |
| Faithfulness | 0,5861 | 0,5468 | **-6,7%** |

### Análise
- **Hipótese confirmada para Context Recall e Context Precision**: ambas as métricas melhoraram, com destaque para o ganho de recall (+13,9%), o maior entre todas as métricas avaliadas.
- 
- **Bug identificado e corrigido durante o experimento**: a implementação inicial do multiquery não incluía a pergunta original do usuário na busca — apenas as 3 variações geradas pelo LLM eram usadas para recuperação. Isso causou uma **piora** temporária nas métricas em uma rodada intermediária (Context Precision: -1,6%, Context Recall: -6,2%, Faithfulness: -10,4% vs. baseline). Após corrigir para incluir a query original no conjunto de buscas (`queries = [query] + variacoes`), os resultados acima foram obtidos, confirmando que a query original é uma fonte de recall mais confiável que reformulações isoladas do LLM.
- 
- **Answer Relevancy melhorou (+8,1%)**, indicando que o contexto mais preciso recuperado contribuiu, ainda que indiretamente, para respostas mais alinhadas à pergunta.
- 
- **Faithfulness piorou (-6,7%) mesmo com ganhos de recall/precision**. Isso é consistente com uma limitação observada em experimentos anteriores: o Ragas decompõe a resposta em múltiplas afirmações, e frases explicativas geradas pelo RAG (ex: "isso significa que...") são frequentemente classificadas como não-atribuíveis ao contexto, mesmo quando semanticamente corretas. Esse comportamento não está diretamente ligado à qualidade do retrieval, e sim ao estilo de resposta do modelo gerador — sugerindo que ganhos futuros em Faithfulness dependem mais de ajuste de prompt (respostas mais diretas, menos elaborativas) do que de mudanças no pipeline de recuperação

