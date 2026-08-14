import re
from pathlib import Path
from statistics import mean, median, stdev

# Caminho da pasta com os .md
PASTA = "pdfs_reunidos"

# Detecta blocos de tabela Markdown
table_line = re.compile(r'^\s*\|.*\|\s*$')

tabelas = []
qtd_tabelas_grandes = 0

for md_file in Path(PASTA).rglob("*.md"):
    with open(md_file, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    tabela_atual = []

    for linha in linhas:
        if table_line.match(linha):
            tabela_atual.append(linha)
        else:
            if len(tabela_atual) >= 2:  # considera apenas tabelas com pelo menos cabeçalho + separador
                texto = "".join(tabela_atual)
                tabelas.append(len(texto))
            tabela_atual = []

            if len(tabela_atual) >= 2200:
                pass
    # Caso o arquivo termine com uma tabela
    if len(tabela_atual) >= 2:
        texto = "".join(tabela_atual)
        tabelas.append(len(texto))


for tabela in tabelas:
    if tabela >+ 2200:
        qtd_tabelas_grandes = qtd_tabelas_grandes +1

print("aa", qtd_tabelas_grandes)

if not tabelas:
    print("Nenhuma tabela encontrada.")
else:
    print(f"Tabelas encontradas: {len(tabelas)}")
    print(f"tabelas maiores q 2200 caracteres: {qtd_tabelas_grandes}")
    print(f"Média: {mean(tabelas):.2f} caracteres")
    print(f"Mediana: {median(tabelas):.2f} caracteres")
    print(f"Desvio padrão: {stdev(tabelas):.2f} caracteres" if len(tabelas) > 1 else "Desvio padrão: N/A")
    print(f"Menor: {min(tabelas)} caracteres")
    print(f"Maior: {max(tabelas)} caracteres")