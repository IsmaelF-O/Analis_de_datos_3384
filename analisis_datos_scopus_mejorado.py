from pathlib import Path
import re
import unicodedata
from difflib import SequenceMatcher
from collections import Counter
from math import log

import pandas as pd


# =========================================
# 0. CONFIGURACION
# =========================================
# MEJORA:
# Antes el archivo de entrada estaba "quemado" en una sola linea y era mas
# dificil mover el script a otra carpeta. Ahora dejamos rutas claras y faciles
# de cambiar.
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = Path(r"C:\Users\Brayan Flores\Downloads\Biometría_44\scopus_3384.csv")
OUTPUT_DIR = BASE_DIR / "salidas_scopus"
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================================
# 1. DICCIONARIOS DE ANALISIS
# =========================================
# MEJORA:
# Separamos los vocabularios en bloques. Esto hace mas facil ampliar el estudio
# y ademas permite ver de forma transparente por que un articulo cae en un
# cluster u otro.
PALABRAS_IA = [
    "artificial intelligence",
    "ai",
    "chatgpt",
    "generative ai",
    "genai",
    "machine learning",
    "deep learning",
    "large language model",
    "large language models",
    "llm",
    "llms",
]

PALABRAS_POBLACION = [
    "student",
    "students",
    "undergraduate",
    "postgraduate",
    "college",
    "university",
    "higher education",
    "faculty",
    "teacher",
    "teachers",
    "academic staff",
]

CLUSTERS = {
    "social": [
        "communication",
        "interaction",
        "community",
        "social",
        "collaboration",
        "peer",
        "network",
        "engagement",
        "discussion",
        "relationship",
        "trust",
        "ethics",
    ],
    "academico": [
        "learning",
        "teaching",
        "classroom",
        "assignment",
        "assessment",
        "exam",
        "course",
        "curriculum",
        "pedagog",
        "feedback",
        "study",
        "performance",
    ],
    "creativo": [
        "creative",
        "creativity",
        "design",
        "content creation",
        "writing",
        "storytelling",
        "brainstorm",
        "art",
        "image generation",
        "multimedia",
        "innovation",
        "co-creation",
    ],
}

# MEJORA:
# Esta lista define expresiones tematicas que queremos medir de forma directa.
# Sirve para producir tablas faciles de interpretar con porcentajes por cluster
# y sobre el corpus completo. Puedes ampliarla segun avance tu marco teorico.
EXPRESIONES_RELEVANTES = [
    "chatgpt",
    "generative ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "large language model",
    "llm",
    "facebook",
    "meta",
    "social media",
    "communication",
    "interaction",
    "community",
    "collaboration",
    "learning",
    "teaching",
    "classroom",
    "assessment",
    "assignment",
    "creative",
    "creativity",
    "design",
    "writing",
    "content creation",
]

# MEJORA:
# Estas expresiones se trataran como conceptos completos. Asi evitamos que
# terminos como "artificial" e "intelligence" se analicen por separado cuando
# en realidad queremos medir la frase "artificial intelligence".
EXPRESIONES_COMPUESTAS_PRIORITARIAS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "large language model",
    "large language models",
    "generative ai",
    "social media",
    "higher education",
    "content creation",
]

# MEJORA:
# Este conjunto elimina palabras demasiado generales que pueden contaminar
# el cluster "otro". La idea es dejar terminos mas utiles para interpretar
# ese grupo residual.
STOPWORDS_OTRO = {
    "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
    "a", "an", "is", "are", "this", "that", "these", "those", "their",
    "there", "here", "have", "has", "had", "into", "such", "all", "more",
    "most", "many", "much", "some", "any", "each", "other", "also",
    "may", "might", "can", "could", "should", "would", "will", "than",
    "between", "among", "within", "about", "because", "while", "where",
    "which", "whose", "when", "been", "being", "used", "using", "use",
    "based", "however", "therefore", "through", "across", "including",
    "includes", "include", "toward", "towards", "under", "over",
    "student", "students", "university", "education", "higher",
    "rights", "reserved", "copyright", "book", "chapter",
}


# =========================================
# 2. FUNCIONES DE APOYO
# =========================================
def normalizar_texto(texto):
    """
    Limpia texto libre sin destruir completamente la informacion semantica.

    MEJORA:
    En el script original se eliminaban todos los caracteres fuera de A-Z.
    Eso borra acentos, guiones y parte de la informacion util. Aqui primero
    normalizamos acentos y luego limpiamos con mas cuidado.
    """
    if pd.isna(texto):
        return ""

    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"http\S+|www\.\S+", " ", texto)
    texto = re.sub(r"[^a-z0-9\s\-]", " ", texto)
    texto = re.sub(r"\b\d+\b", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def columna_disponible(df, candidatas, default=""):
    """
    Devuelve la primera columna existente dentro de una lista de nombres
    posibles. Scopus cambia algunos encabezados segun el formato de exportacion.
    """
    for nombre in candidatas:
        if nombre in df.columns:
            return nombre
    return default


def dividir_lista_scopus(valor):
    """
    Convierte una celda tipo Scopus "a; b; c" en una lista limpia.
    """
    if pd.isna(valor):
        return []

    partes = [p.strip() for p in str(valor).split(";")]
    return [p for p in partes if p]


def limpiar_nombre_autor(nombre):
    """
    Estandariza nombres de autor para evitar duplicados falsos.

    MEJORA:
    Aqui quitamos IDs pegados al nombre, comas, acentos y espacios extra.
    Tambien intentamos pasar de "Perez, Juan" a "juan perez" para que el
    conteo sea mas consistente.
    """
    if pd.isna(nombre):
        return ""

    nombre = str(nombre)
    nombre = re.sub(r"\(\s*\d+\s*\)", "", nombre)
    nombre = nombre.replace(".", " ")
    nombre = nombre.strip().lower()
    nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("utf-8")

    if "," in nombre:
        partes = [p.strip() for p in nombre.split(",") if p.strip()]
        if len(partes) >= 2:
            apellido = partes[0]
            resto = " ".join(partes[1:])
            nombre = f"{resto} {apellido}"

    nombre = re.sub(r"[^a-z\s-]", " ", nombre)
    nombre = re.sub(r"\s+", " ", nombre)
    return nombre.strip()


def firma_autor(nombre_normalizado):
    """
    Genera una firma corta para agrupar candidatos similares.

    MEJORA:
    En vez de comparar todos contra todos, primero los agrupamos por apellido
    e inicial. Eso reduce falsos positivos y mejora el rendimiento.
    """
    if not nombre_normalizado:
        return ""

    partes = nombre_normalizado.split()
    if not partes:
        return ""

    apellido = partes[-1]
    inicial = partes[0][0]
    return f"{apellido}_{inicial}"


def es_orcid(valor):
    return bool(re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", str(valor).strip()))


def es_id_scopus(valor):
    return bool(re.fullmatch(r"\d{6,20}", str(valor).strip()))


def contar_terminos(texto, terminos):
    """
    Cuenta cuantas palabras o expresiones de una lista aparecen en el texto.

    MEJORA:
    El script original usaba "p in texto", lo que para casos como "ai" podia
    dar falsos positivos dentro de otras palabras. Aqui usamos limites de
    palabra cuando aplica.
    """
    if not texto:
        return 0

    total = 0
    for termino in terminos:
        termino_norm = normalizar_texto(termino)
        patron = r"\b" + re.escape(termino_norm).replace(r"\ ", r"\s+") + r"\b"
        if re.search(patron, texto):
            total += 1
    return total


def extraer_autores_fila(row, col_autores, col_autores_full, col_author_ids):
    """
    Une nombres e IDs por posicion para dejar una estructura mas estable.

    MEJORA:
    Antes se trabajaba solo con "Authors" y ademas se llamaba "Author_IDs"
    a una lista que realmente era de nombres. Aqui separamos bien los
    conceptos: nombre visible, nombre limpio, ID de Scopus y clave final.
    """
    nombres_preferidos = dividir_lista_scopus(row.get(col_autores_full, "")) if col_autores_full else []
    nombres_cortos = dividir_lista_scopus(row.get(col_autores, "")) if col_autores else []
    ids_scopus = dividir_lista_scopus(row.get(col_author_ids, "")) if col_author_ids else []

    if nombres_preferidos:
        nombres = nombres_preferidos
    else:
        nombres = nombres_cortos

    max_len = max(len(nombres), len(ids_scopus), len(nombres_cortos), 0)
    autores = []

    for idx in range(max_len):
        nombre_raw = nombres[idx] if idx < len(nombres) else ""
        if not nombre_raw and idx < len(nombres_cortos):
            nombre_raw = nombres_cortos[idx]

        scopus_id = ids_scopus[idx] if idx < len(ids_scopus) else ""
        nombre_limpio = limpiar_nombre_autor(nombre_raw)

        if not nombre_limpio and not scopus_id:
            continue

        autores.append(
            {
                "author_name_raw": nombre_raw,
                "author_name_clean": nombre_limpio,
                "author_scopus_id": scopus_id if es_id_scopus(scopus_id) else "",
            }
        )

    return autores


def construir_mapa_autores(serie_autores, umbral=92):
    """
    Resuelve nombres parecidos cuando no hay ID de Scopus.

    MEJORA:
    1. Damos prioridad al ID de Scopus como identificador estable.
    2. Solo aplicamos fuzzy matching a autores sin ID.
    3. Comparamos dentro de la misma firma para evitar mezclar personas
       distintas que comparten algun termino.
    """
    mapa = {}
    cubetas = {}

    for autores in serie_autores:
        for autor in autores:
            nombre = autor["author_name_clean"]
            if not nombre:
                continue

            if autor["author_scopus_id"]:
                mapa[nombre] = nombre
                continue

            cubeta = firma_autor(nombre)
            cubetas.setdefault(cubeta, [])

            encontrado = False
            for existente in cubetas[cubeta]:
                if abs(len(nombre) - len(existente)) > 6:
                    continue
                similitud = SequenceMatcher(None, nombre, existente).ratio() * 100
                if similitud >= umbral:
                    mapa[nombre] = existente
                    encontrado = True
                    break

            if not encontrado:
                cubetas[cubeta].append(nombre)
                mapa[nombre] = nombre

    return mapa


def enriquecer_autores(autores, mapa_autores):
    """
    Agrega una clave unica de autor y conserva el nombre canonico.
    """
    salida = []
    for autor in autores:
        nombre_limpio = autor["author_name_clean"]
        scopus_id = autor["author_scopus_id"]
        nombre_canonico = mapa_autores.get(nombre_limpio, nombre_limpio)

        if scopus_id:
            author_key = f"scopus:{scopus_id}"
        elif nombre_canonico:
            author_key = f"name:{nombre_canonico}"
        else:
            continue

        salida.append(
            {
                **autor,
                "author_name_canonical": nombre_canonico,
                "author_key": author_key,
            }
        )
    return salida


def clasificar_cluster(texto):
    """
    Asigna un cluster principal y deja trazabilidad por puntajes.

    MEJORA:
    En lugar de solo devolver una categoria, guardamos el puntaje de cada
    cluster. Eso ayuda mucho para justificar el analisis comparativo.
    """
    scores = {cluster: contar_terminos(texto, terminos) for cluster, terminos in CLUSTERS.items()}
    max_score = max(scores.values()) if scores else 0

    if max_score == 0:
        principal = "otro"
    else:
        ganadores = [nombre for nombre, score in scores.items() if score == max_score]
        principal = ganadores[0] if len(ganadores) == 1 else "mixto"

    secundarios = [nombre for nombre, score in scores.items() if score > 0]
    return pd.Series(
        {
            "cluster_principal": principal,
            "clusters_detectados": ", ".join(secundarios) if secundarios else "ninguno",
            "score_social": scores.get("social", 0),
            "score_academico": scores.get("academico", 0),
            "score_creativo": scores.get("creativo", 0),
        }
    )


def top_palabras_por_cluster(df):
    """
    Calcula TF-IDF por cluster para identificar lenguaje caracteristico.
    """
    textos = df.groupby("cluster_principal")["texto_total"].apply(lambda x: " ".join(x))
    textos = textos[textos.index.isin(["social", "academico", "creativo", "mixto"])]

    if textos.empty:
        return pd.DataFrame()

    stopwords = {
        "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
        "a", "an", "is", "are", "this", "that", "using", "use", "based",
        "students", "student", "university", "education", "higher",
    }
    tokens_por_cluster = {}
    df_por_termino = Counter()

    for cluster, texto in textos.items():
        tokens = [t for t in texto.split() if len(t) > 2 and t not in stopwords]
        conteo = Counter(tokens)
        tokens_por_cluster[cluster] = conteo
        for termino in conteo:
            df_por_termino[termino] += 1

    total_clusters = len(tokens_por_cluster)
    filas = {}
    for cluster, conteo in tokens_por_cluster.items():
        puntajes = {}
        total_tokens = sum(conteo.values()) or 1
        for termino, tf in conteo.items():
            idf = log((1 + total_clusters) / (1 + df_por_termino[termino])) + 1
            puntajes[termino] = (tf / total_tokens) * idf
        top_terminos = dict(sorted(puntajes.items(), key=lambda item: item[1], reverse=True)[:40])
        filas[cluster] = top_terminos

    return pd.DataFrame.from_dict(filas, orient="index").fillna(0)


def frecuencia_real_por_cluster(df):
    """
    Calcula frecuencia absoluta de terminos por cluster.
    """
    if df.empty:
        return pd.DataFrame()

    stopwords = {
        "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
        "a", "an", "is", "are", "this", "that", "using", "use", "based",
        "students", "student", "university", "education", "higher",
    }
    filas = []

    for _, row in df.iterrows():
        tokens = [t for t in row["texto_total"].split() if len(t) > 2 and t not in stopwords]
        conteo = Counter(tokens).most_common(40)
        fila = {"cluster_principal": row["cluster_principal"]}
        fila.update(dict(conteo))
        filas.append(fila)

    tabla = pd.DataFrame(filas).fillna(0)
    return tabla.groupby("cluster_principal").sum(numeric_only=True)


def top_terminos_por_cluster(df, top_n=20):
    """
    Extrae palabras frecuentes por cluster con porcentajes interpretables.

    MEJORA:
    No solo contamos palabras totales. Tambien calculamos:
    1. porcentaje de articulos del cluster donde aparece el termino
    2. porcentaje de articulos del corpus completo donde aparece el termino

    Con esto puedes reportar frases como:
    "chatgpt aparece en 56% de los articulos del cluster social y en 21%
    del corpus completo".
    """
    if df.empty:
        return pd.DataFrame()

    stopwords = {
        "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
        "a", "an", "is", "are", "this", "that", "using", "use", "based",
        "students", "student", "university", "education", "higher", "artificial",
        "intelligence",
    }

    total_docs = len(df)
    corpus_doc_freq = Counter()

    for texto in df["texto_total"]:
        tokens_unicos = {t for t in texto.split() if len(t) > 2 and t not in stopwords}
        corpus_doc_freq.update(tokens_unicos)

    filas = []
    for cluster, df_cluster in df.groupby("cluster_principal"):
        doc_count_cluster = len(df_cluster)
        token_counter = Counter()
        doc_freq_cluster = Counter()

        for texto in df_cluster["texto_total"]:
            tokens = [t for t in texto.split() if len(t) > 2 and t not in stopwords]
            token_counter.update(tokens)
            doc_freq_cluster.update(set(tokens))

        total_tokens_cluster = sum(token_counter.values()) or 1
        for termino, frecuencia_total in token_counter.most_common(top_n):
            articulos_con_termino_cluster = doc_freq_cluster[termino]
            articulos_con_termino_corpus = corpus_doc_freq[termino]
            filas.append(
                {
                    "cluster_principal": cluster,
                    "termino": termino,
                    "frecuencia_total_cluster": frecuencia_total,
                    "articulos_cluster_con_termino": articulos_con_termino_cluster,
                    "porcentaje_articulos_cluster": round((articulos_con_termino_cluster / doc_count_cluster) * 100, 2),
                    "articulos_corpus_con_termino": articulos_con_termino_corpus,
                    "porcentaje_articulos_corpus": round((articulos_con_termino_corpus / total_docs) * 100, 2),
                    "porcentaje_uso_cluster": round((frecuencia_total / total_tokens_cluster) * 100, 2),
                }
            )

    return pd.DataFrame(filas)


def top_terminos_cluster_otro(df, top_n=15):
    """
    Devuelve solo terminos interpretables del cluster "otro".

    Columnas:
    - porcentaje_articulos_corpus: porcentaje de articulos del corpus total
      donde aparece el termino
    - frecuencia_por_texto_otro: peso del termino dentro del vocabulario del
      cluster otro
    """
    df_otro = df[df["cluster_principal"] == "otro"].copy()
    if df_otro.empty:
        return pd.DataFrame()

    total_docs_corpus = len(df)
    contador_total = Counter()
    docs_corpus = Counter()

    for texto in df_otro["texto_total"]:
        tokens = [
            t for t in texto.split()
            if len(t) > 2 and t not in STOPWORDS_OTRO and not t.isdigit()
        ]
        contador_total.update(tokens)

    for texto in df["texto_total"]:
        tokens_unicos = {
            t for t in texto.split()
            if len(t) > 2 and t not in STOPWORDS_OTRO and not t.isdigit()
        }
        docs_corpus.update(tokens_unicos)

    total_tokens_otro = sum(contador_total.values()) or 1
    filas = []
    for termino, frecuencia_total in contador_total.most_common(top_n):
        filas.append(
            {
                "termino": termino,
                "porcentaje_articulos_corpus": round((docs_corpus[termino] / total_docs_corpus) * 100, 2),
                "frecuencia_por_texto_otro": round((frecuencia_total / total_tokens_otro) * 100, 2),
            }
        )

    return pd.DataFrame(filas)


def medir_expresiones_relevantes(df, expresiones):
    """
    Mide expresiones definidas por el investigador en cada cluster.

    MEJORA:
    Las palabras sueltas son utiles, pero a veces necesitas expresiones
    concretas como "chatgpt" o "social media". Esta tabla calcula el
    porcentaje dentro de cada cluster y sobre el corpus total.
    """
    if df.empty:
        return pd.DataFrame()

    total_docs = len(df)
    filas = []

    for expresion in expresiones:
        expresion_norm = normalizar_texto(expresion)
        patron = r"\b" + re.escape(expresion_norm).replace(r"\ ", r"\s+") + r"\b"

        mask_corpus = df["texto_total"].str.contains(patron, regex=True, na=False)
        docs_corpus = int(mask_corpus.sum())

        for cluster, df_cluster in df.groupby("cluster_principal"):
            mask_cluster = df_cluster["texto_total"].str.contains(patron, regex=True, na=False)
            docs_cluster = int(mask_cluster.sum())
            total_cluster = len(df_cluster)

            filas.append(
                {
                    "cluster_principal": cluster,
                    "expresion": expresion,
                    "articulos_cluster_con_expresion": docs_cluster,
                    "porcentaje_articulos_cluster": round((docs_cluster / total_cluster) * 100, 2) if total_cluster else 0,
                    "articulos_corpus_con_expresion": docs_corpus,
                    "porcentaje_articulos_corpus": round((docs_corpus / total_docs) * 100, 2) if total_docs else 0,
                }
            )

    return pd.DataFrame(filas)


def preparar_texto_para_frases(texto, expresiones_compuestas):
    """
    Convierte frases compuestas en un solo token con guion bajo.

    MEJORA:
    "artificial intelligence" pasa a "artificial_intelligence". Con esto
    el conteo del cluster "otro" respeta el concepto completo.
    """
    texto_procesado = texto
    for expresion in expresiones_compuestas:
        expresion_norm = normalizar_texto(expresion)
        token_unido = expresion_norm.replace(" ", "_")
        patron = r"\b" + re.escape(expresion_norm).replace(r"\ ", r"\s+") + r"\b"
        texto_procesado = re.sub(patron, token_unido, texto_procesado)
    return texto_procesado


def top_frases_y_terminos_cluster_otro(df, top_n=15):
    """
    Reporta el cluster "otro" priorizando frases compuestas y terminos utiles.

    Salida:
    - termino_o_frase
    - porcentaje_articulos_corpus
    - frecuencia_por_texto_otro
    """
    df_otro = df[df["cluster_principal"] == "otro"].copy()
    if df_otro.empty:
        return pd.DataFrame()

    total_docs_corpus = len(df)
    contador_total = Counter()
    docs_corpus = Counter()

    textos_otro = [
        preparar_texto_para_frases(texto, EXPRESIONES_COMPUESTAS_PRIORITARIAS)
        for texto in df_otro["texto_total"]
    ]
    textos_corpus = [
        preparar_texto_para_frases(texto, EXPRESIONES_COMPUESTAS_PRIORITARIAS)
        for texto in df["texto_total"]
    ]

    componentes_bloqueados = set()
    for expresion in EXPRESIONES_COMPUESTAS_PRIORITARIAS:
        partes = normalizar_texto(expresion).split()
        if len(partes) > 1:
            componentes_bloqueados.update(partes)

    for texto in textos_otro:
        tokens = []
        for token in texto.split():
            if len(token) <= 2 or token.isdigit():
                continue
            if token in STOPWORDS_OTRO:
                continue
            if "_" not in token and token in componentes_bloqueados:
                continue
            tokens.append(token)
        contador_total.update(tokens)

    for texto in textos_corpus:
        tokens_unicos = set()
        for token in texto.split():
            if len(token) <= 2 or token.isdigit():
                continue
            if token in STOPWORDS_OTRO:
                continue
            if "_" not in token and token in componentes_bloqueados:
                continue
            tokens_unicos.add(token)
        docs_corpus.update(tokens_unicos)

    total_tokens_otro = sum(contador_total.values()) or 1
    filas = []
    for termino, frecuencia_total in contador_total.most_common(top_n):
        filas.append(
            {
                "termino_o_frase": termino.replace("_", " "),
                "porcentaje_articulos_corpus": round((docs_corpus[termino] / total_docs_corpus) * 100, 2),
                "frecuencia_por_texto_otro": round((frecuencia_total / total_tokens_otro) * 100, 2),
            }
        )

    return pd.DataFrame(filas)


def medir_expresiones_para_redaccion(df, expresiones, clusters_objetivo):
    """
    Genera una tabla breve para redactar resultados academicos.

    - porcentaje_en_cluster: en que porcentaje de los articulos del cluster
      aparece la expresion al menos una vez
    - porcentaje_global: en que porcentaje del corpus total aparece
    - promedio_por_articulo: cuantas veces aparece en promedio por articulo
      dentro del cluster
    """
    if df.empty:
        return pd.DataFrame()

    total_docs = len(df)
    filas = []

    for expresion in expresiones:
        expresion_norm = normalizar_texto(expresion)
        patron = r"\b" + re.escape(expresion_norm).replace(r"\ ", r"\s+") + r"\b"
        docs_corpus = int(df["texto_total"].str.contains(patron, regex=True, na=False).sum())

        for cluster in clusters_objetivo:
            df_cluster = df[df["cluster_principal"] == cluster]
            if df_cluster.empty:
                continue

            apariciones = df_cluster["texto_total"].str.count(patron).fillna(0)
            total_apariciones = float(apariciones.sum())
            articulos_con_expresion = int((apariciones > 0).sum())
            total_articulos_cluster = len(df_cluster)

            filas.append(
                {
                    "cluster_principal": cluster,
                    "expresion": expresion,
                    "porcentaje_en_cluster": round((articulos_con_expresion / total_articulos_cluster) * 100, 2)
                    if total_articulos_cluster
                    else 0,
                    "porcentaje_global": round((docs_corpus / total_docs) * 100, 2) if total_docs else 0,
                    "promedio_por_articulo": round((total_apariciones / total_articulos_cluster), 2)
                    if total_articulos_cluster
                    else 0,
                }
            )

    return pd.DataFrame(filas)


# =========================================
# 3. CARGA Y VALIDACION DE DATOS
# =========================================
# Aqui leemos el CSV exportado desde Scopus. Desde este punto, `df` sera la
# tabla principal sobre la que trabaja todo el analisis.
df = pd.read_csv(INPUT_FILE)
print("Registros iniciales:", len(df))

# Validamos que las columnas minimas existan. Si falta una de estas, el resto
# del analisis ya no seria confiable o simplemente fallaria.
columnas_obligatorias = ["Title", "Abstract", "Year", "Cited by"]
faltantes = [col for col in columnas_obligatorias if col not in df.columns]
if faltantes:
    raise ValueError(f"Faltan columnas obligatorias en el CSV: {faltantes}")

# Guardamos los nombres reales de columnas de autores porque segun el formato
# de exportacion de Scopus pueden variar o venir vacias.
col_autores = columna_disponible(df, ["Authors"])
col_autores_full = columna_disponible(df, ["Author full names"])
col_author_ids = columna_disponible(df, ["Author(s) ID"])


# =========================================
# 4. LIMPIEZA BASE
# =========================================
# MEJORA:
# Pasamos la limpieza a un bloque explicito para que quede claro que
# columnas se normalizan y con que objetivo.
# Esta parte no clasifica todavia; solo prepara el texto para que el conteo
# de terminos sea mas consistente y menos sensible a mayusculas o ruido.
for col in ["Title", "Abstract", "Affiliations", "Author Keywords", "Index Keywords", "Source title"]:
    if col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

# Creamos versiones limpias del titulo, resumen y keywords. Estas son las
# columnas que realmente alimentan los filtros y los clusters.
df["title_clean"] = df["Title"].apply(normalizar_texto)
df["abstract_clean"] = df["Abstract"].apply(normalizar_texto)
df["keywords_clean"] = (
    df.get("Author Keywords", "").fillna("").astype(str).apply(normalizar_texto)
    if "Author Keywords" in df.columns
    else ""
)

# `texto_total` concentra toda la evidencia textual que vamos a analizar.
# Esto evita revisar por separado titulo, abstract y keywords en cada paso.
df["texto_total"] = (
    df["title_clean"].fillna("")
    + " "
    + df["abstract_clean"].fillna("")
    + " "
    + (df["keywords_clean"] if isinstance(df["keywords_clean"], pd.Series) else "")
).str.replace(r"\s+", " ", regex=True).str.strip()

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df["Cited by"] = pd.to_numeric(df["Cited by"], errors="coerce").fillna(0).astype(int)

# MEJORA:
# Eliminamos duplicados con DOI cuando exista, porque es mas estable que el
# titulo. Si no hay DOI, usamos titulo limpio como respaldo.
# Primero nos quedamos con la version mas citada cuando parece haber
# duplicados, y luego removemos filas repetidas.
if "DOI" in df.columns:
    df["DOI"] = df["DOI"].fillna("").astype(str).str.strip().str.lower()
    df = df.sort_values(["DOI", "Cited by"], ascending=[True, False])
    df = df.drop_duplicates(subset=["DOI", "title_clean"], keep="first")
else:
    df = df.drop_duplicates(subset=["title_clean"], keep="first")

# Quitamos registros sin anio, sin titulo/resumen util o con texto demasiado
# corto para un analisis tematico razonable.
df = df.dropna(subset=["Year"])
df["Year"] = df["Year"].astype(int)
df = df[(df["title_clean"] != "") & (df["abstract_clean"] != "")]
df = df[df["texto_total"].str.len() >= 80]

# Estos dos puntajes son la puerta de entrada al corpus final:
# 1. score_ia: evidencia de inteligencia artificial
# 2. score_poblacion: evidencia de poblacion universitaria/academica
df["score_ia"] = df["texto_total"].apply(lambda texto: contar_terminos(texto, PALABRAS_IA))
df["score_poblacion"] = df["texto_total"].apply(lambda texto: contar_terminos(texto, PALABRAS_POBLACION))

# MEJORA:
# El filtro ya no es solo booleano. Primero calculamos puntajes y luego
# decidimos con base en ellos. Eso te deja trazabilidad para justificar
# por que un articulo entro al corpus.
df = df[(df["score_ia"] > 0) & (df["score_poblacion"] > 0)].copy()
print("Despues del filtrado tematico:", len(df))


# =========================================
# 5. LIMPIEZA Y NORMALIZACION DE AUTORES
# =========================================
# En este punto extraemos una estructura por autor dentro de cada articulo.
# Cada elemento guarda nombre original, nombre limpio e ID de Scopus si existe.
df["authors_struct"] = df.apply(
    lambda row: extraer_autores_fila(row, col_autores, col_autores_full, col_author_ids),
    axis=1,
)

# `mapa_autores` intenta resolver variantes del mismo nombre. Si hay
# `Author(s) ID`, se usa como identidad principal. Si no, se prueba similitud
# conservadora entre nombres limpios.
mapa_autores = construir_mapa_autores(df["authors_struct"])
df["authors_struct"] = df["authors_struct"].apply(lambda autores: enriquecer_autores(autores, mapa_autores))

# MEJORA:
# Guardamos listas resumidas para facilitar inspeccion manual del resultado.
# `authors_canonical` sirve para leer rapido los autores ya normalizados.
# `author_keys` sirve para contar de forma estable a un mismo autor.
df["authors_canonical"] = df["authors_struct"].apply(
    lambda autores: [a["author_name_canonical"] for a in autores if a["author_name_canonical"]]
)
df["author_keys"] = df["authors_struct"].apply(
    lambda autores: [a["author_key"] for a in autores if a["author_key"]]
)
df["num_authors"] = df["author_keys"].apply(len)


# =========================================
# 6. CLUSTERS TEMATICOS
# =========================================
# Aqui asignamos a cada articulo un cluster principal:
# social, academico, creativo, mixto u otro.
# Ademas guardamos los puntajes de cada eje para poder justificar la clasificacion.
df = pd.concat([df, df["texto_total"].apply(clasificar_cluster)], axis=1)


# =========================================
# 7. TABLA EXPANDIDA DE AUTORES
# =========================================
# MEJORA:
# Creamos una tabla a nivel autor-articulo. Esto resuelve de una vez el
# conteo de frecuencia, citas por autor, frecuencia anual y presencia
# por cluster.
# Esta transformacion es clave: pasamos de "un articulo con varios autores"
# a "una fila por autor dentro de cada articulo".
filas_autores = []
for _, row in df.iterrows():
    for autor in row["authors_struct"]:
        filas_autores.append(
            {
                "author_key": autor["author_key"],
                "author_name_canonical": autor["author_name_canonical"],
                "author_name_raw": autor["author_name_raw"],
                "author_scopus_id": autor["author_scopus_id"],
                "Title": row["Title"],
                "Year": row["Year"],
                "Cited by": row["Cited by"],
                "cluster_principal": row["cluster_principal"],
                "clusters_detectados": row["clusters_detectados"],
                "score_ia": row["score_ia"],
                "score_social": row["score_social"],
                "score_academico": row["score_academico"],
                "score_creativo": row["score_creativo"],
                "EID": row["EID"] if "EID" in df.columns else "",
                "DOI": row["DOI"] if "DOI" in df.columns else "",
            }
        )

df_autores = pd.DataFrame(filas_autores)

if df_autores.empty:
    raise ValueError("No se pudieron extraer autores del corpus filtrado.")


# =========================================
# 8. METRICAS POR AUTOR
# =========================================
# `resumen_autores` consolida lo principal por autor:
# publicaciones, citas, anios activos y afinidad con cada cluster.
def moda_segura(series):
    series = series.dropna()
    if series.empty:
        return ""
    modos = series.mode()
    return modos.iloc[0] if not modos.empty else ""


resumen_autores = (
    df_autores.groupby("author_key")
    .agg(
        author_name=("author_name_canonical", "first"),
        author_scopus_id=("author_scopus_id", "first"),
        publicaciones=("Title", "count"),
        articulos_unicos=("EID", lambda x: x.replace("", pd.NA).nunique() if len(x) else 0),
        citas_totales=("Cited by", "sum"),
        citas_promedio=("Cited by", "mean"),
        anios_activos=("Year", "nunique"),
        primer_anio=("Year", "min"),
        ultimo_anio=("Year", "max"),
        cluster_predominante=("cluster_principal", moda_segura),
        score_ia_total=("score_ia", "sum"),
        score_social_total=("score_social", "sum"),
        score_academico_total=("score_academico", "sum"),
        score_creativo_total=("score_creativo", "sum"),
    )
    .reset_index()
)

# MEJORA:
# "Quienes hablan mas del tema" lo aterrizamos en una metrica interpretable:
# autores con mas publicaciones del corpus IA + educacion y con mas intensidad
# acumulada de terminos relevantes.
# `frecuencia_relativa` muestra el peso del autor dentro del corpus filtrado.
# `impacto_por_articulo` resume su citacion promedio.
# `habla_mas_del_tema` combina presencia y densidad tematica.
resumen_autores["frecuencia_relativa"] = resumen_autores["publicaciones"] / len(df)
resumen_autores["impacto_por_articulo"] = (
    resumen_autores["citas_totales"] / resumen_autores["publicaciones"]
).round(2)
resumen_autores["habla_mas_del_tema"] = (
    resumen_autores["publicaciones"] * 0.6 + resumen_autores["score_ia_total"] * 0.4
).round(2)

# Para lectura mas facil, calculamos el cluster con mayor puntaje por autor.
resumen_autores["tema_mas_representado"] = resumen_autores[
    ["score_social_total", "score_academico_total", "score_creativo_total"]
].idxmax(axis=1).str.replace("_total", "", regex=False).str.replace("score_", "", regex=False)

resumen_autores = resumen_autores.sort_values(
    ["habla_mas_del_tema", "citas_totales", "publicaciones"],
    ascending=[False, False, False],
)


# =========================================
# 9. FRECUENCIA DE AUTORES
# =========================================
# Estas dos tablas responden preguntas diferentes:
# - frecuencia_autores_anual: en que anos aparece mas cada autor
# - frecuencia_autores_cluster: en que cluster participa mas cada autor
frecuencia_autores_anual = (
    df_autores.groupby(["Year", "author_key", "author_name_canonical"])
    .size()
    .reset_index(name="frecuencia")
    .sort_values(["Year", "frecuencia"], ascending=[True, False])
)

frecuencia_autores_cluster = (
    df_autores.groupby(["cluster_principal", "author_key", "author_name_canonical"])
    .size()
    .reset_index(name="frecuencia")
    .sort_values(["cluster_principal", "frecuencia"], ascending=[True, False])
)


# =========================================
# 10. AUTORES MAS CITADOS Y MAS PRODUCTIVOS
# =========================================
autores_mas_citados = resumen_autores.sort_values(
    ["citas_totales", "impacto_por_articulo", "publicaciones"],
    ascending=[False, False, False],
)

autores_mas_productivos = resumen_autores.sort_values(
    ["publicaciones", "citas_totales"],
    ascending=[False, False],
)


# =========================================
# 11. RESUMEN DE CLUSTERS
# =========================================
# Este bloque resume el peso de cada cluster dentro del corpus y prepara
# tablas auxiliares para interpretacion lexical y redaccion de resultados.
resumen_clusters = (
    df.groupby("cluster_principal")
    .agg(
        articulos=("Title", "count"),
        citas_totales=("Cited by", "sum"),
        citas_promedio=("Cited by", "mean"),
        score_ia_total=("score_ia", "sum"),
        score_social_total=("score_social", "sum"),
        score_academico_total=("score_academico", "sum"),
        score_creativo_total=("score_creativo", "sum"),
    )
    .reset_index()
    .sort_values("articulos", ascending=False)
)

tfidf_clusters = top_palabras_por_cluster(df)
frecuencia_palabras_clusters = frecuencia_real_por_cluster(df)
terminos_frecuentes_clusters = top_terminos_por_cluster(df, top_n=25)
expresiones_relevantes_clusters = medir_expresiones_relevantes(df, EXPRESIONES_RELEVANTES)
terminos_limpios_otro = top_frases_y_terminos_cluster_otro(df, top_n=15)

# Esta tabla esta pensada para escribir resultados en lenguaje academico:
# porcentaje global + frecuencia relativa por cluster para expresiones clave.
redaccion_expresiones_clusters = medir_expresiones_para_redaccion(
    df,
    EXPRESIONES_COMPUESTAS_PRIORITARIAS + ["chatgpt", "facebook", "meta", "design", "learning", "creative"],
    ["social", "academico", "creativo"],
)


# =========================================
# 12. EXPORTACION DE RESULTADOS
# =========================================
# MEJORA:
# En lugar de guardar un solo CSV final, exportamos salidas tematicas que
# responden directamente a tus preguntas de investigacion.
# La idea es que no tengas que recalcular todo cada vez que quieras revisar
# autores, clusters o expresiones. Cada CSV responde una pregunta concreta.
df.to_csv(OUTPUT_DIR / "dataset_limpio_enriquecido.csv", index=False)
df_autores.to_csv(OUTPUT_DIR / "tabla_autor_articulo.csv", index=False)
resumen_autores.to_csv(OUTPUT_DIR / "resumen_autores.csv", index=False)
frecuencia_autores_anual.to_csv(OUTPUT_DIR / "frecuencia_autores_anual.csv", index=False)
frecuencia_autores_cluster.to_csv(OUTPUT_DIR / "frecuencia_autores_cluster.csv", index=False)
autores_mas_citados.to_csv(OUTPUT_DIR / "autores_mas_citados.csv", index=False)
autores_mas_productivos.to_csv(OUTPUT_DIR / "autores_mas_productivos.csv", index=False)
resumen_clusters.to_csv(OUTPUT_DIR / "resumen_clusters.csv", index=False)

if not tfidf_clusters.empty:
    tfidf_clusters.to_csv(OUTPUT_DIR / "tfidf_por_cluster.csv")

if not frecuencia_palabras_clusters.empty:
    frecuencia_palabras_clusters.to_csv(OUTPUT_DIR / "frecuencia_palabras_por_cluster.csv")

if not terminos_frecuentes_clusters.empty:
    terminos_frecuentes_clusters.to_csv(OUTPUT_DIR / "terminos_frecuentes_por_cluster.csv", index=False)

if not expresiones_relevantes_clusters.empty:
    expresiones_relevantes_clusters.to_csv(OUTPUT_DIR / "expresiones_relevantes_por_cluster.csv", index=False)

if not terminos_limpios_otro.empty:
    terminos_limpios_otro.to_csv(OUTPUT_DIR / "terminos_limpios_cluster_otro.csv", index=False)

if not redaccion_expresiones_clusters.empty:
    redaccion_expresiones_clusters.to_csv(OUTPUT_DIR / "redaccion_expresiones_clusters.csv", index=False)

reporte_clusters_lineas = []
# Armamos un reporte de texto rapido para lectura humana. Es util si quieres
# revisar resultados sin abrir los CSV en Excel o pandas.
for cluster in ["social", "academico", "creativo", "otro", "mixto"]:
    reporte_clusters_lineas.append(f"CLUSTER: {cluster.upper()}")

    if cluster == "otro":
        tabla_cluster = terminos_limpios_otro.head(10)
        reporte_clusters_lineas.append("Terminos frecuentes del cluster:")
    else:
        tabla_cluster = expresiones_relevantes_clusters[
            expresiones_relevantes_clusters["cluster_principal"] == cluster
        ][
            [
                "expresion",
                "porcentaje_articulos_cluster",
                "porcentaje_articulos_corpus",
            ]
        ].sort_values(
            ["porcentaje_articulos_cluster", "porcentaje_articulos_corpus"],
            ascending=[False, False],
        ).head(10)
        reporte_clusters_lineas.append("Expresiones mas representativas del cluster:")

    if tabla_cluster.empty:
        reporte_clusters_lineas.append("Sin datos disponibles.")
    else:
        reporte_clusters_lineas.append(tabla_cluster.to_string(index=False))

    reporte_clusters_lineas.append("")

(OUTPUT_DIR / "reporte_clusters.txt").write_text("\n".join(reporte_clusters_lineas), encoding="utf-8")


# =========================================
# 13. REPORTE RAPIDO EN CONSOLA
# =========================================
# Este bloque solo imprime un resumen ejecutivo. No cambia los datos, solo te
# deja ver rapidamente si el analisis salio razonable.
print("\nArticulos por anio:")
print(df["Year"].value_counts().sort_index())

print("\nResumen de clusters:")
print(resumen_clusters)

print("\nAutores mas productivos:")
print(autores_mas_productivos[["author_name", "publicaciones", "citas_totales", "tema_mas_representado"]].head(10))

print("\nAutores mas citados:")
print(autores_mas_citados[["author_name", "citas_totales", "impacto_por_articulo", "publicaciones"]].head(10))

print("\nAutores que mas hablan del tema:")
print(resumen_autores[["author_name", "habla_mas_del_tema", "publicaciones", "score_ia_total"]].head(10))

for cluster in ["social", "academico", "creativo", "otro"]:
    if cluster == "otro":
        print(f"\nTerminos frecuentes en cluster {cluster}:")
        print(terminos_limpios_otro.head(10))
    else:
        print(f"\nExpresiones relevantes en cluster {cluster}:")
        print(
            expresiones_relevantes_clusters[
                expresiones_relevantes_clusters["cluster_principal"] == cluster
            ][
                [
                    "expresion",
                    "porcentaje_articulos_cluster",
                    "porcentaje_articulos_corpus",
                ]
            ].sort_values(
                ["porcentaje_articulos_cluster", "porcentaje_articulos_corpus"],
                ascending=[False, False],
            ).head(10)
        )

if not redaccion_expresiones_clusters.empty:
    print("\nExpresiones compuestas listas para redaccion academica:")
    for cluster in ["social", "academico", "creativo"]:
        print(f"\nCluster {cluster}:")
        print(
            redaccion_expresiones_clusters[
                redaccion_expresiones_clusters["cluster_principal"] == cluster
            ].sort_values(
                ["porcentaje_en_cluster", "porcentaje_global", "promedio_por_articulo"],
                ascending=[False, False, False],
            ).head(10)
        )

print(f"\nProceso terminado. Archivos guardados en: {OUTPUT_DIR}")
