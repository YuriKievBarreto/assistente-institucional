import os
from langchain_core.documents import Document
import os
import pymupdf4llm  
from docx import Document

class ConversorRAGMarkdown:
    def __init__(self, pasta_data_lake):
        self.pasta_base = pasta_data_lake

    def converter_docx_para_md(self, caminho_arquivo):
      
        try:
            doc = Document(caminho_arquivo)
            linhas_md = []
            
            for paragrafo in doc.paragraphs:
                texto = paragrafo.text.strip()
                if not texto:
                    continue
                    
                estilo = paragrafo.style.name.lower()
                
                # Mapeia estilos de Título do Word para Markdown
                if 'heading 1' in estilo or 'título 1' in estilo:
                    linhas_md.append(f"\n# {texto}\n")
                elif 'heading 2' in estilo or 'título 2' in estilo:
                    linhas_md.append(f"\n## {texto}\n")
                elif 'heading 3' in estilo or 'título 3' in estilo:
                    linhas_md.append(f"\n### {texto}\n")
                # Mapeia listas
                elif 'list bullet' in estilo or 'lista' in estilo:
                    linhas_md.append(f"* {texto}")
                else:
                   
                    if len(paragrafo.runs) > 0 and all(run.bold for run in paragrafo.runs if run.text.strip()):
                        linhas_md.append(f"**{texto}**")
                    else:
                        linhas_md.append(texto)
            
            return "\n".join(linhas_md)
        except Exception as e:
            print(f" [ERRO DOCX] {caminho_arquivo}: {e}")
            return ""

    def converter_pdf_para_md(self, caminho_arquivo):
        
        try:
            # O to_markdown analisa tamanhos de fonte e formata como #, ##, e | Tabelas |
            texto_md = pymupdf4llm.to_markdown(caminho_arquivo)
            
            # Heurística para detectar PDF Escaneado (Imagem)
            # Se o pymupdf4llm retornar muito pouco texto para um arquivo grande
            tamanho_arquivo_kb = os.path.getsize(caminho_arquivo) / 1024
            if tamanho_arquivo_kb > 100 and len(texto_md.strip()) < 200:
                return "[ALERTA: PDF ESCANEADO_NECESSITA_OCR]"
                
            return texto_md
            
        except Exception as e:
            print(f" [ERRO PDF] {caminho_arquivo}: {e}")
            return ""

    def processar_datalake(self):
        """Varre o Data Lake e gera as versões MD para inserção no Qdrant."""
        print(f"Iniciando conversão de documentos para Markdown na pasta: {self.pasta_base}\n")
        
        for raiz, _, arquivos in os.walk(self.pasta_base):
            for arquivo in arquivos:
                caminho_completo = os.path.join(raiz, arquivo)
                nome_base, ext = os.path.splitext(caminho_completo)
                ext = ext.lower()

                if ext not in ['.pdf', '.docx']:
                    continue
                    
             
                caminho_md_destino = f"{nome_base}.md"
                
               
                if os.path.exists(caminho_md_destino):
                    continue 

                print(f"Convertendo: {arquivo}...")
                
                texto_md = ""
                if ext == '.pdf':
                    texto_md = self.converter_pdf_para_md(caminho_completo)
                elif ext == '.docx':
                    texto_md = self.converter_docx_para_md(caminho_completo)

               
                if texto_md == "[ALERTA: PDF ESCANEADO_NECESSITA_OCR]":
                    print(f"  -> ⚠️ ALERTA: É apenas imagem. Necessita OCR.")
                    with open(caminho_md_destino, 'w', encoding='utf-8') as f:
                        f.write("> [Este documento é escaneado e requer OCR. Contexto inacessível via texto direto.]")
                    continue

              
                if texto_md and len(texto_md) > 50:
                    with open(caminho_md_destino, 'w', encoding='utf-8') as f:
                        f.write(texto_md)
                    print(f"  -> ✅ MD Gerado!")
                else:
                    print(f"  -> ❌ Falha na extração ou arquivo vazio.")

# Para executar:
if __name__ == "__main__":
    extrator = ConversorRAGMarkdown("pdfs_ifpb_completos/editais/ensino")
    extrator.processar_datalake()