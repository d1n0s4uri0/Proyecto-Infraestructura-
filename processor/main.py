import json
import os
import pandas as pd

KEYWORDS = [
    # Macroeconomía
    "inflacion", "ipc", "pib", "crecimiento", "recesion",
    "desempleo", "consumo",

    # Política monetaria
    "tasa de interes", "tasas",
    "banco de la republica", "fed",

    # Mercados
    "bolsa", "acciones", "mercado",
    "colcap", "volatilidad",

    # Tipo de cambio
    "dolar", "trm", "divisas",

    # Commodities
    "petroleo", "brent", "oro",

    # Finanzas y riesgo
    "banco", "credito", "inversion",
    "crisis", "riesgo"
]

INPUT_PATH = "data/raw"
OUTPUT_PATH = "data/processed"

os.makedirs(OUTPUT_PATH, exist_ok=True)

def clean_text(text: str) -> str:
    import re
    import unicodedata
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_test_data_file(path: str = os.path.join("data", "raw", "test_data.json")) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error cargando datos de prueba {path}: {e}")
        return []

rows = []

try:
    files = [f for f in os.listdir(INPUT_PATH) if f.endswith(".jsonl")]
except FileNotFoundError:
    print(f"Input path {INPUT_PATH} no existe; usando datos de prueba si están disponibles.")
    files = []
except Exception as e:
    print(f"Error listando {INPUT_PATH}: {e}")
    files = []

if files:
    for file in files:
        path = os.path.join(INPUT_PATH, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        doc = json.loads(line)
                        text = clean_text(doc.get("text", ""))
                        hits = sum(text.count(k) for k in KEYWORDS)
                        rows.append({
                            "date": doc.get("date"),
                            "doc_id": doc.get("id"),
                            "keyword_hits": hits
                        })
                    except Exception as e:
                        print(f"Error procesando línea en {file}: {e}")
        except FileNotFoundError:
            print(f"Archivo no encontrado: {path}")
        except Exception as e:
            print(f"Error leyendo {path}: {e}")
else:
    test_data = load_test_data_file(os.path.join(INPUT_PATH, "test_data.json"))
    if not test_data:
        print("No se encontraron archivos .jsonl ni datos de prueba. Nada para procesar.")
    else:
        for doc in test_data:
            try:
                text = clean_text(doc.get("text", ""))
                hits = sum(text.count(k) for k in KEYWORDS)
                rows.append({
                    "date": doc.get("date"),
                    "doc_id": doc.get("id", None),
                    "keyword_hits": hits
                })
            except Exception as e:
                print(f"Error procesando documento de prueba: {e}")

if not rows:
    print("No se generaron filas; finalizando sin crear archivo.")
else:
    try:
        df = pd.DataFrame(rows)
        output_file = os.path.join(OUTPUT_PATH, "results.csv")
        df.to_csv(output_file, index=False)
        print("Processor terminado. Archivo generado:", output_file)
    except Exception as e:
        print(f"Error escribiendo resultado: {e}")
