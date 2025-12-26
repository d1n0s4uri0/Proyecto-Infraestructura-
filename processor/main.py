import json
import os
import pandas as pd
from unidecode import unidecode

KEYWORDS = [
    "inflacion", "dolar", "economia", "colcap",
    "crisis", "bolsa", "pib"
]

INPUT_PATH = "data/raw"
OUTPUT_PATH = "data/processed"

os.makedirs(OUTPUT_PATH, exist_ok=True)

def clean_text(text):
    text = unidecode(text.lower())
    return text

rows = []

for file in os.listdir(INPUT_PATH):
    if file.endswith(".jsonl"):
        with open(os.path.join(INPUT_PATH, file), "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                text = clean_text(doc["text"])

                hits = sum(text.count(k) for k in KEYWORDS)

                rows.append({
                    "date": doc["date"],
                    "doc_id": doc["id"],
                    "keyword_hits": hits
                })

df = pd.DataFrame(rows)

output_file = os.path.join(OUTPUT_PATH, "results.csv")
df.to_csv(output_file, index=False)

print("Processor terminado. Archivo generado:", output_file)
