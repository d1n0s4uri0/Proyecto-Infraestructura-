import pandas as pd
import os
import matplotlib.pyplot as plt

# Rutas
PROCESSED_PATH = "data/processed/results.csv"
COLCAP_PATH = "data/indicators/COLCAP.csv"
OUTPUT_PATH = "data/aggregated"
PLOTS_PATH = "data/aggregated/plots"

os.makedirs(OUTPUT_PATH, exist_ok=True)
os.makedirs(PLOTS_PATH, exist_ok=True)

# 1. Leer resultados del processor
news_df = pd.read_csv(PROCESSED_PATH)

# 2. Agrupar por fecha
daily_news = (
    news_df
    .groupby("date", as_index=False)
    .agg(
        docs_count=("doc_id", "count"),
        total_keyword_hits=("keyword_hits", "sum")
    )
)

# 3. Leer COLCAP
colcap_df = pd.read_csv(COLCAP_PATH)

# 4. Unir por fecha
merged = pd.merge(daily_news, colcap_df, on="date", how="inner")

# 5. Guardar CSV combinado
merged_output = os.path.join(OUTPUT_PATH, "merged_daily.csv")
merged.to_csv(merged_output, index=False)

# 6. Correlaciones
corr_hits = merged["total_keyword_hits"].corr(merged["colcap_close"])
corr_docs = merged["docs_count"].corr(merged["colcap_close"])

with open(os.path.join(OUTPUT_PATH, "metrics.txt"), "w") as f:
    f.write(f"Correlación keyword_hits vs COLCAP: {corr_hits}\n")
    f.write(f"Correlación docs_count vs COLCAP: {corr_docs}\n")

# =========================
# 📊 GRÁFICAS
# =========================

# Gráfica 1: Keywords por día
plt.figure()
plt.plot(merged["date"], merged["total_keyword_hits"])
plt.title("Frecuencia de palabras clave por día")
plt.xlabel("Fecha")
plt.ylabel("Total keywords")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_PATH, "keywords_por_dia.png"))
plt.close()

# Gráfica 2: COLCAP por día
plt.figure()
plt.plot(merged["date"], merged["colcap_close"])
plt.title("Índice COLCAP por día")
plt.xlabel("Fecha")
plt.ylabel("Valor COLCAP")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_PATH, "colcap_por_dia.png"))
plt.close()

# Gráfica 3: Relación keywords vs COLCAP
plt.figure()
plt.scatter(merged["total_keyword_hits"], merged["colcap_close"])
plt.title("Relación entre noticias económicas y COLCAP")
plt.xlabel("Total keywords")
plt.ylabel("COLCAP")
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_PATH, "keywords_vs_colcap.png"))
plt.close()

print("Analyzer completo con gráficas")
print("Resultados en:", OUTPUT_PATH)
print("Gráficas en:", PLOTS_PATH)

