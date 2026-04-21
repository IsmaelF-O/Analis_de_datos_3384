# =========================================
# 0. LIBRERÍAS
# =========================================
import pandas as pd        # Manipulación de datos
import re                  # Busca y manipulación de texto
import unicodedata         # Normalización de texto. Detecta el Orcid y otros identificadores(evitar duplicados falsos)
from rapidfuzz import fuzz # Compara textos para detectar similitudes (nombres de autores). Es clave cuanodo no se tiene el Orcid 
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer # Para análisis de texto (TF-IDF y frecuencia real) Mide que tan importante es una palabra en un documento en relación a un corpus, y la frecuencia real de palabras en los textos. Es clave para entender que temas son más relevantes en cada categoría de uso.
 
# =========================================
# 1. CARGA DE DATOS
# =========================================
df = pd.read_csv("scopus_3384.csv")
print("Registros iniciales:", len(df))


# =========================================
# 2. LIMPIEZA VECTORIAL
# =========================================
cols = ["Title", "Abstract", "Authors", "Affiliations"]

for col in cols:
    if col in df.columns:
        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )

# =========================================
# 2.1 TEXTO TOTAL
# =========================================
df["texto_total"] = df["Title"] + " " + df["Abstract"]

df["texto_total"] = (
    df["texto_total"]
    .str.replace(r"http\S+", "", regex=True)
    .str.replace(r"[^a-zA-Z\s]", " ", regex=True)
    .str.replace(r"\b\d+\b", "", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)


# =========================================
# 3. FILTRACIÓN
# =========================================
df = df.drop_duplicates(subset=["Title"])
df = df[(df["Title"] != "") & (df["Abstract"] != "")]
df = df[df["texto_total"].str.len() > 80]

palabras_ia = [
    "artificial intelligence", "ai", "chatgpt",
    "machine learning", "deep learning", "large language model"
]

df = df[df["texto_total"].apply(lambda x: any(p in x for p in palabras_ia))]

palabras_poblacion = [
    "student", "students", "university",
    "college", "higher education"
]

df = df[df["texto_total"].apply(lambda x: any(p in x for p in palabras_poblacion))]

print("Después de filtrado:", len(df))


# =========================================
# 4. AUTORES
# =========================================
df["Author_IDs"] = df["Authors"].apply(
    lambda x: [a.strip() for a in x.split(";")] if isinstance(x, str) else []
)

# --- normalización ---
def limpiar_nombre_avanzado(nombre):
    nombre = str(nombre).lower().strip()
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode('utf-8')
    nombre = nombre.replace(".", "")
    nombre = re.sub(r"\s+", " ", nombre)
    return nombre

def son_similares(n1, n2, umbral=85):
    return fuzz.ratio(n1, n2) >= umbral

# extraer autores sin ORCID
autores_sin_orcid = set()

for lista in df["Author_IDs"]:
    for autor in lista:
        limpio = limpiar_nombre_avanzado(autor)

        if limpio == "" or len(limpio) < 3:
            continue

        if not re.match(r"\d{4}-\d{4}-\d{4}-\d{4}", str(autor)):
            autores_sin_orcid.add(limpio)

# mapa de similitud
mapa_autores = {}
autores_unicos = []

for autor in autores_sin_orcid:
    encontrado = False

    for existente in autores_unicos:

        if abs(len(autor) - len(existente)) > 5:
            continue

        if autor.split()[0] != existente.split()[0]:
            continue

        if son_similares(autor, existente):
            mapa_autores[autor] = existente
            encontrado = True
            break

    if not encontrado:
        autores_unicos.append(autor)
        mapa_autores[autor] = autor

# aplicar normalización
def normalizar_autores(lista):
    if not isinstance(lista, list):
        return []

    return list(dict.fromkeys([
        mapa_autores.get(limpiar_nombre_avanzado(a), limpiar_nombre_avanzado(a))
        for a in lista
    ]))

df["Author_IDs"] = df["Author_IDs"].apply(normalizar_autores)


# =========================================
# 5. IDENTIDAD COMPUESTA (CORREGIDO)
# =========================================

# Country seguro
if "Country" in df.columns:
    df["Country"] = df["Country"].fillna("").astype(str)
else:
    df["Country"] = ""

# Affiliations seguro
if "Affiliations" not in df.columns:
    df["Affiliations"] = ""

def identidad_compuesta(row):
    autores = row.get("Author_IDs", [])

    if not isinstance(autores, list):
        return []

    afiliacion = str(row.get("Affiliations", ""))[:20]
    pais = str(row.get("Country", ""))
    year = str(row.get("Year", ""))

    resultado = []

    for autor in autores:
        base = limpiar_nombre_avanzado(autor)
        resultado.append(f"{base}_{afiliacion}_{pais}_{year}")

    return resultado

df["Author_Composite_ID"] = df.apply(identidad_compuesta, axis=1)

# asegurar listas
df["Author_Composite_ID"] = df["Author_Composite_ID"].apply(
    lambda x: x if isinstance(x, list) else []
)


# =========================================
# 6. CLASIFICACIÓN
# =========================================
categorias = {
    "academico": ["assignment", "exam", "classroom", "learning"],
    "creativo": ["design", "art", "creative", "content"],
    "social": ["chat", "interaction", "communication", "community"]
}

def clasificar(texto):
    scores = {k: 0 for k in categorias}

    for cat, palabras in categorias.items():
        for p in palabras:
            if p in texto:
                scores[cat] += 1

    max_cat = max(scores, key=scores.get)

    return max_cat if scores[max_cat] > 0 else "otro"

df["tipo_uso"] = df["texto_total"].apply(clasificar)


# =========================================
# 7. ANÁLISIS TEMPORAL
# =========================================
df["Year"] = pd.to_numeric(df.get("Year", ""), errors="coerce")
df = df.dropna(subset=["Year"])
df["Year"] = df["Year"].astype(int)

print("\nArtículos por año:")
print(df["Year"].value_counts().sort_index())


# =========================================
# 8. TF-IDF
# =========================================
textos_categoria = df.groupby("tipo_uso")["texto_total"].apply(lambda x: " ".join(x))

vectorizer = TfidfVectorizer(max_features=30, stop_words='english')
X = vectorizer.fit_transform(textos_categoria)

df_tfidf = pd.DataFrame(
    X.toarray(),
    index=textos_categoria.index,
    columns=vectorizer.get_feature_names_out()
)

print("\nPalabras más importantes por categoría:")
for cat in df_tfidf.index:
    print(f"\n{cat.upper()}")
    print(df_tfidf.loc[cat].sort_values(ascending=False).head(10))


# =========================================
# 9. FRECUENCIA REAL
# =========================================
vectorizer2 = CountVectorizer(max_features=30, stop_words='english')
X2 = vectorizer2.fit_transform(df["texto_total"])

df_words = pd.DataFrame(
    X2.toarray(),
    columns=vectorizer2.get_feature_names_out()
)

df_words["tipo_uso"] = df["tipo_uso"]

tabla = df_words.groupby("tipo_uso").sum()

print("\nFrecuencia de palabras:")
print(tabla.head())


# =========================================
# 10. AUTORES MÁS PRODUCTIVOS
# =========================================
df_exp = df.explode("Author_Composite_ID")
df_exp = df_exp[df_exp["Author_Composite_ID"] != ""]

print("\nAutores más productivos:")
print(df_exp["Author_Composite_ID"].value_counts().head(10))


# =========================================
# 11. GUARDAR
# =========================================
df.to_csv("dataset_final_limpio.csv", index=False)

print("\nProceso terminado correctamente")



# ahie poner autores mas frecuentes por año, y por tipo de uso, para ver si hay patrones temporales o temáticos en la producción de ciertos autores.
#no es lo mismo autores mas frecuentes a mas prodcutivos, porque un autor puede tener muchos artículos pero no ser el más frecuente en un año o tipo de uso específico. Para analizar esto, podemos hacer lo siguiente: 