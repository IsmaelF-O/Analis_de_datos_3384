# se importa Path para trabajar con rutas de archivos y carpetas.
from pathlib import Path
# se importa re para buscar y limpiar patrones de texto con expresiones regulares.
import re
# se importa unicodedata para normalizar acentos y caracteres especiales.
import unicodedata
# se importa SequenceMatcher para comparar nombres de autores y detectar similitudes.
from difflib import SequenceMatcher
# se importa Counter para contar palabras, terminos y frecuencias.
from collections import Counter
# se importa log para calcular puntajes tipo TF-IDF.
from math import log

# se importa la libreria pandas para analisis de datos en tablas y archivos CSV.
import pandas as pd


# =========================================
# 0. CONFIGURACION
# =========================================
# MEJORA:
# Antes el archivo de entrada estaba "quemado" en una sola linea y era mas
# dificil mover el script a otra carpeta. Ahora dejamos rutas claras y faciles
# de cambiar.
# se obtiene la carpeta donde esta guardado este script.
BASE_DIR = Path(__file__).resolve().parent
# se define la ruta del archivo CSV de Scopus que se va a analizar.
INPUT_FILE = Path(r"C:\Users\Brayan Flores\Downloads\Biometría_44\scopus_3384.csv")
# se define la carpeta donde se guardaran los archivos generados.
OUTPUT_DIR = BASE_DIR / "salidas_scopus"
# se crea la carpeta de salidas si todavia no existe.
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================================
# 1. DICCIONARIOS DE ANALISIS
# =========================================
# MEJORA:
# Separamos los vocabularios en bloques. Esto hace mas facil ampliar el estudio
# y ademas permite ver de forma transparente por que un articulo cae en un
# cluster u otro.
# se define una variable fija que controla una parte del analisis.
PALABRAS_IA = [
    # se agrega este termino a la lista para detectarlo en los articulos.
    "artificial intelligence",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "ai",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "chatgpt",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "generative ai",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "genai",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "machine learning",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "deep learning",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "large language model",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "large language models",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "llm",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "llms",
# se cierra la lista, diccionario o llamada que se abrio antes.
]

# se define una variable fija que controla una parte del analisis.
PALABRAS_POBLACION = [
    # se agrega este termino a la lista para detectarlo en los articulos.
    "student",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "students",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "undergraduate",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "postgraduate",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "college",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "university",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "higher education",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "faculty",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "professor", # se agrega este termino a la lista para detectarlo en los articulos.
    "lecturer", # se agrega este termino a la lista para detectarlo en los articulos.
    "instructors", # se agrega este termino a la lista para detectarlo en los articulos.
]

# se define una variable fija que controla una parte del analisis.
CLUSTERS = {
    # se inicia una lista de valores para usarla en el analisis.
    "social": [
        # se agrega este termino a la lista para detectarlo en los articulos.
        "communication",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "interaction",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "community",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "social",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "collaboration",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "peer",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "network",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "engagement",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "discussion",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "relationship",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "trust",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "ethics",
    # se realiza un paso especifico dentro del flujo del analisis.
    ],
    # se inicia una lista de valores para usarla en el analisis.
    "academico": [
        # se agrega este termino a la lista para detectarlo en los articulos.
        "learning",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "teaching",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "classroom",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "assignment",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "assessment",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "exam",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "course",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "curriculum",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "pedagog",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "feedback",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "study",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "performance",
    # se realiza un paso especifico dentro del flujo del analisis.
    ],
    # se inicia una lista de valores para usarla en el analisis.
    "creativo": [
        # se agrega este termino a la lista para detectarlo en los articulos.
        "creative",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "creativity",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "design",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "content creation",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "writing",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "storytelling",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "brainstorm",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "art",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "image generation",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "multimedia",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "innovation",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "co-creation", # se agrega este termino a la lista para detectarlo en los articulos.
        "collaborative creation", # se agrega este termino a la lista para detectarlo en los articulos.
    # se realiza un paso especifico dentro del flujo del analisis.
    ],
# se cierra la lista, diccionario o llamada que se abrio antes.
}

# MEJORA:
# Esta lista define expresiones tematicas que queremos medir de forma directa.
# Sirve para producir tablas faciles de interpretar con porcentajes por cluster
# y sobre el corpus completo. Puedes ampliarla segun avance tu marco teorico.
# se define una variable fija que controla una parte del analisis.
EXPRESIONES_RELEVANTES = [
    # se agrega este termino a la lista para detectarlo en los articulos.
    "chatgpt",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "generative ai",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "artificial intelligence",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "machine learning",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "deep learning",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "large language model",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "llm",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "facebook",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "meta",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "social media",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "communication",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "interaction",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "community",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "collaboration",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "learning",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "teaching",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "classroom",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "assessment",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "assignment",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "creative",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "creativity",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "design",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "writing",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "content creation",
# se cierra la lista, diccionario o llamada que se abrio antes.
]

# MEJORA:
# Estas expresiones se trataran como conceptos completos. Asi evitamos que
# terminos como "artificial" e "intelligence" se analicen por separado cuando
# en realidad queremos medir la frase "artificial intelligence".
# se define una variable fija que controla una parte del analisis.
EXPRESIONES_COMPUESTAS_PRIORITARIAS = {

    "social": [                 # definimos un cluster de expresiones compuestas relacionadas con lo social.
        "social media",          # se agrega este termino a la lista para detectarlo en los articulos.
        "social interaction",
        "human ai interaction",  # se agrega este termino a la lista para detectarlo en los articulos.
        "technology acceptance",
        "digital literacy",
        "online community",
        "social networking",
        "student perception",       # 
        "social interaction",     # interacción en plataformas digitales
    ],

    "academico": [
        "higher education",
        "academic performance",
        "student engagement",
        "learning outcomes",
        "educational technology",
        "academic integrity",
        "adaptive learning",
        "collaborative learning",
    ],

    "creativo": [
        "content creation",
        "creative writing",
        "digital creativity",
        "ai generated content",
        "multimedia production", # 
        "creative process",
        "prompt engineering", #  
    ]
}
# MEJORA:
# Este conjunto elimina palabras demasiado generales que pueden contaminar
# el cluster "otro". La idea es dejar terminos mas utiles para interpretar
# ese grupo residual.
# se define una variable fija que controla una parte del analisis.
STOPWORDS_OTRO = {
    # se agrega este termino a la lista para detectarlo en los articulos.
    "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "a", "an", "is", "are", "this", "that", "these", "those", "their",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "there", "here", "have", "has", "had", "into", "such", "all", "more",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "most", "many", "much", "some", "any", "each", "other", "also",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "may", "might", "can", "could", "should", "would", "will", "than",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "between", "among", "within", "about", "because", "while", "where",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "which", "whose", "when", "been", "being", "used", "using", "use",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "based", "however", "therefore", "through", "across", "including",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "includes", "include", "toward", "towards", "under", "over",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "student", "students", "university", "education", "higher",
    # se agrega este termino a la lista para detectarlo en los articulos.
    "rights", "reserved", "copyright", "book", "chapter",
# se cierra la lista, diccionario o llamada que se abrio antes.
}


# =========================================
# 2. FUNCIONES DE APOYO
# =========================================
# se crea la funcion normalizar_texto para reutilizar esta parte del proceso.
def normalizar_texto(texto):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Limpia texto libre sin destruir completamente la informacion semantica.

    MEJORA:
    En el script original se eliminaban todos los caracteres fuera de A-Z.
    Eso borra acentos, guiones y parte de la informacion util. Aqui primero
    normalizamos acentos y luego limpiamos con mas cuidado.
    """
    # se revisa una condicion antes de continuar con este bloque.
    if pd.isna(texto):
        # se devuelve el resultado calculado por la funcion.
        return ""

    # se guarda un valor o calculo intermedio para usarlo despues.
    texto = str(texto).lower().strip()
    # se guarda un valor o calculo intermedio para usarlo despues.
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    # se guarda un valor o calculo intermedio para usarlo despues.
    texto = re.sub(r"http\S+|www\.\S+", " ", texto)
    # se guarda un valor o calculo intermedio para usarlo despues.
    texto = re.sub(r"[^a-z0-9\s\-]", " ", texto)
    # se guarda un valor o calculo intermedio para usarlo despues.
    texto = re.sub(r"\b\d+\b", " ", texto)
    # se guarda un valor o calculo intermedio para usarlo despues.
    texto = re.sub(r"\s+", " ", texto)
    # se devuelve el resultado calculado por la funcion.
    return texto.strip()


# se crea la funcion columna_disponible para reutilizar esta parte del proceso.
def columna_disponible(df, candidatas, default=""):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Devuelve la primera columna existente dentro de una lista de nombres
    posibles. Scopus cambia algunos encabezados segun el formato de exportacion.
    """
    # se recorren varios elementos para procesarlos uno por uno.
    for nombre in candidatas:
        # se revisa una condicion antes de continuar con este bloque.
        if nombre in df.columns:
            # se devuelve el resultado calculado por la funcion.
            return nombre
    # se devuelve el resultado calculado por la funcion.
    return default


# se crea la funcion dividir_lista_scopus para reutilizar esta parte del proceso.
def dividir_lista_scopus(valor):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Convierte una celda tipo Scopus "a; b; c" en una lista limpia.
    """
    # se revisa una condicion antes de continuar con este bloque.
    if pd.isna(valor):
        # se devuelve el resultado calculado por la funcion.
        return []

    # se guarda un valor o calculo intermedio para usarlo despues.
    partes = [p.strip() for p in str(valor).split(";")]
    # se devuelve el resultado calculado por la funcion.
    return [p for p in partes if p]


# se crea la funcion limpiar_nombre_autor para reutilizar esta parte del proceso.
def limpiar_nombre_autor(nombre):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Estandariza nombres de autor para evitar duplicados falsos.

    MEJORA:
    Aqui quitamos IDs pegados al nombre, comas, acentos y espacios extra.
    Tambien intentamos pasar de "Perez, Juan" a "juan perez" para que el
    conteo sea mas consistente.
    """
    # se revisa una condicion antes de continuar con este bloque.
    if pd.isna(nombre):
        # se devuelve el resultado calculado por la funcion.
        return ""

    # se guarda un valor o calculo intermedio para usarlo despues.
    nombre = str(nombre)
    # se guarda un valor o calculo intermedio para usarlo despues.
    nombre = re.sub(r"\(\s*\d+\s*\)", "", nombre)
    # se guarda un valor o calculo intermedio para usarlo despues.
    nombre = nombre.replace(".", " ")
    # se guarda un valor o calculo intermedio para usarlo despues.
    nombre = nombre.strip().lower()
    # se guarda un valor o calculo intermedio para usarlo despues.
    nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("utf-8")

    # se revisa una condicion antes de continuar con este bloque.
    if "," in nombre:
        # se guarda un valor o calculo intermedio para usarlo despues.
        partes = [p.strip() for p in nombre.split(",") if p.strip()]
        # se revisa una condicion antes de continuar con este bloque.
        if len(partes) >= 2:
            # se guarda un valor o calculo intermedio para usarlo despues.
            apellido = partes[0]
            # se guarda un valor o calculo intermedio para usarlo despues.
            resto = " ".join(partes[1:])
            # se guarda un valor o calculo intermedio para usarlo despues.
            nombre = f"{resto} {apellido}"

    # se guarda un valor o calculo intermedio para usarlo despues.
    nombre = re.sub(r"[^a-z\s-]", " ", nombre)
    # se guarda un valor o calculo intermedio para usarlo despues.
    nombre = re.sub(r"\s+", " ", nombre)
    # se devuelve el resultado calculado por la funcion.
    return nombre.strip()
#________________________________________________________________________________________________

# se crea la funcion firma_autor para reutilizar esta parte del proceso.
def firma_autor(nombre_normalizado):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Genera una firma corta para agrupar candidatos similares.

    MEJORA:
    En vez de comparar todos contra todos, primero los agrupamos por apellido
    e inicial. Eso reduce falsos positivos y mejora el rendimiento.
    """
    # se revisa una condicion antes de continuar con este bloque.
    if not nombre_normalizado:
        # se devuelve el resultado calculado por la funcion.
        return ""

    # se guarda un valor o calculo intermedio para usarlo despues.
    partes = nombre_normalizado.split()
    # se revisa una condicion antes de continuar con este bloque.
    if not partes:
        # se devuelve el resultado calculado por la funcion.
        return ""

    # se guarda un valor o calculo intermedio para usarlo despues.
    apellido = partes[-1]
    # se guarda un valor o calculo intermedio para usarlo despues.
    inicial = partes[0][0]
    # se devuelve el resultado calculado por la funcion.
    return f"{apellido}_{inicial}"


# se crea la funcion es_orcid para reutilizar esta parte del proceso.
def es_orcid(valor):
    # se devuelve el resultado calculado por la funcion.
    return bool(re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", str(valor).strip()))


# se crea la funcion es_id_scopus para reutilizar esta parte del proceso.
def es_id_scopus(valor):
    # se devuelve el resultado calculado por la funcion.
    return bool(re.fullmatch(r"\d{6,20}", str(valor).strip()))


# se crea la funcion contar_terminos para reutilizar esta parte del proceso.
def contar_terminos(texto, terminos):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Cuenta cuantas palabras o expresiones de una lista aparecen en el texto.

    MEJORA:
    El script original usaba "p in texto", lo que para casos como "ai" podia
    dar falsos positivos dentro de otras palabras. Aqui usamos limites de
    palabra cuando aplica.
    """
    # se revisa una condicion antes de continuar con este bloque.
    if not texto:
        # se devuelve el resultado calculado por la funcion.
        return 0

    # se guarda un valor o calculo intermedio para usarlo despues.
    total = 0
    # se recorren varios elementos para procesarlos uno por uno.
    for termino in terminos:
        # se guarda un valor o calculo intermedio para usarlo despues.
        termino_norm = normalizar_texto(termino)
        # se guarda un valor o calculo intermedio para usarlo despues.
        patron = r"\b" + re.escape(termino_norm).replace(r"\ ", r"\s+") + r"\b"
        # se revisa una condicion antes de continuar con este bloque.
        if re.search(patron, texto):
            # se guarda un valor o calculo intermedio para usarlo despues.
            total += 1
    # se devuelve el resultado calculado por la funcion.
    return total


# se crea la funcion extraer_autores_fila para reutilizar esta parte del proceso.
def extraer_autores_fila(row, col_autores, col_autores_full, col_author_ids):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Une nombres e IDs por posicion para dejar una estructura mas estable.

    MEJORA:
    Antes se trabajaba solo con "Authors" y ademas se llamaba "Author_IDs"
    a una lista que realmente era de nombres. Aqui separamos bien los
    conceptos: nombre visible, nombre limpio, ID de Scopus y clave final.
    """
    # se guarda un valor o calculo intermedio para usarlo despues.
    nombres_preferidos = dividir_lista_scopus(row.get(col_autores_full, "")) if col_autores_full else []
    # se guarda un valor o calculo intermedio para usarlo despues.
    nombres_cortos = dividir_lista_scopus(row.get(col_autores, "")) if col_autores else []
    # se guarda un valor o calculo intermedio para usarlo despues.
    ids_scopus = dividir_lista_scopus(row.get(col_author_ids, "")) if col_author_ids else []

    # se revisa una condicion antes de continuar con este bloque.
    if nombres_preferidos:
        # se guarda un valor o calculo intermedio para usarlo despues.
        nombres = nombres_preferidos
    # se ejecuta este bloque cuando no se cumple la condicion anterior.
    else:
        # se guarda un valor o calculo intermedio para usarlo despues.
        nombres = nombres_cortos

    # se guarda un valor o calculo intermedio para usarlo despues.
    max_len = max(len(nombres), len(ids_scopus), len(nombres_cortos), 0)
    # se guarda un valor o calculo intermedio para usarlo despues.
    autores = []

    # se recorren varios elementos para procesarlos uno por uno.
    for idx in range(max_len):
        # se guarda un valor o calculo intermedio para usarlo despues.
        nombre_raw = nombres[idx] if idx < len(nombres) else ""
        # se revisa una condicion antes de continuar con este bloque.
        if not nombre_raw and idx < len(nombres_cortos):
            # se guarda un valor o calculo intermedio para usarlo despues.
            nombre_raw = nombres_cortos[idx]

        # se guarda un valor o calculo intermedio para usarlo despues.
        scopus_id = ids_scopus[idx] if idx < len(ids_scopus) else ""
        # se guarda un valor o calculo intermedio para usarlo despues.
        nombre_limpio = limpiar_nombre_autor(nombre_raw)

        # se revisa una condicion antes de continuar con este bloque.
        if not nombre_limpio and not scopus_id:
            # se realiza un paso especifico dentro del flujo del analisis.
            continue

        # se realiza un paso especifico dentro del flujo del analisis.
        autores.append(
            # se inicia un diccionario para organizar informacion por categorias.
            {
                # se define una categoria del diccionario y sus terminos asociados.
                "author_name_raw": nombre_raw,
                # se define una categoria del diccionario y sus terminos asociados.
                "author_name_clean": nombre_limpio,
                # se agrega este termino a la lista para detectarlo en los articulos.
                "author_scopus_id": scopus_id if es_id_scopus(scopus_id) else "",
            # se cierra la lista, diccionario o llamada que se abrio antes.
            }
        # se cierra la lista, diccionario o llamada que se abrio antes.
        )

    # se devuelve el resultado calculado por la funcion.
    return autores


# se crea la funcion construir_mapa_autores para reutilizar esta parte del proceso.
def construir_mapa_autores(serie_autores, umbral=92):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Resuelve nombres parecidos cuando no hay ID de Scopus.

    MEJORA:
    1. Damos prioridad al ID de Scopus como identificador estable.
    2. Solo aplicamos fuzzy matching a autores sin ID.
    3. Comparamos dentro de la misma firma para evitar mezclar personas
       distintas que comparten algun termino.
    """
    # se guarda un valor o calculo intermedio para usarlo despues.
    mapa = {}
    # se guarda un valor o calculo intermedio para usarlo despues.
    cubetas = {}

    # se recorren varios elementos para procesarlos uno por uno.
    for autores in serie_autores:
        # se recorren varios elementos para procesarlos uno por uno.
        for autor in autores:
            # se guarda un valor o calculo intermedio para usarlo despues.
            nombre = autor["author_name_clean"]
            # se revisa una condicion antes de continuar con este bloque.
            if not nombre:
                # se realiza un paso especifico dentro del flujo del analisis.
                continue

            # se revisa una condicion antes de continuar con este bloque.
            if autor["author_scopus_id"]:
                # se guarda un valor o calculo intermedio para usarlo despues.
                mapa[nombre] = nombre
                # se realiza un paso especifico dentro del flujo del analisis.
                continue

            # se guarda un valor o calculo intermedio para usarlo despues.
            cubeta = firma_autor(nombre)
            # se ejecuta una funcion o metodo para procesar los datos.
            cubetas.setdefault(cubeta, [])

            # se guarda un valor o calculo intermedio para usarlo despues.
            encontrado = False
            # se recorren varios elementos para procesarlos uno por uno.
            for existente in cubetas[cubeta]:
                # se revisa una condicion antes de continuar con este bloque.
                if abs(len(nombre) - len(existente)) > 6:
                    # se realiza un paso especifico dentro del flujo del analisis.
                    continue
                # se comparan textos para medir que tan parecidos son.
                similitud = SequenceMatcher(None, nombre, existente).ratio() * 100
                # se revisa una condicion antes de continuar con este bloque.
                if similitud >= umbral:
                    # se guarda un valor o calculo intermedio para usarlo despues.
                    mapa[nombre] = existente
                    # se guarda un valor o calculo intermedio para usarlo despues.
                    encontrado = True
                    # se realiza un paso especifico dentro del flujo del analisis.
                    break

            # se revisa una condicion antes de continuar con este bloque.
            if not encontrado:
                # se ejecuta una funcion o metodo para procesar los datos.
                cubetas[cubeta].append(nombre)
                # se guarda un valor o calculo intermedio para usarlo despues.
                mapa[nombre] = nombre

    # se devuelve el resultado calculado por la funcion.
    return mapa


# se crea la funcion enriquecer_autores para reutilizar esta parte del proceso.
def enriquecer_autores(autores, mapa_autores):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Agrega una clave unica de autor y conserva el nombre canonico.
    """
    # se guarda un valor o calculo intermedio para usarlo despues.
    salida = []
    # se recorren varios elementos para procesarlos uno por uno.
    for autor in autores:
        # se guarda un valor o calculo intermedio para usarlo despues.
        nombre_limpio = autor["author_name_clean"]
        # se guarda un valor o calculo intermedio para usarlo despues.
        scopus_id = autor["author_scopus_id"]
        # se guarda un valor o calculo intermedio para usarlo despues.
        nombre_canonico = mapa_autores.get(nombre_limpio, nombre_limpio)

        # se revisa una condicion antes de continuar con este bloque.
        if scopus_id:
            # se guarda un valor o calculo intermedio para usarlo despues.
            author_key = f"scopus:{scopus_id}"
        # se revisa otra condicion cuando la anterior no se cumplio.
        elif nombre_canonico:
            # se guarda un valor o calculo intermedio para usarlo despues.
            author_key = f"name:{nombre_canonico}"
        # se ejecuta este bloque cuando no se cumple la condicion anterior.
        else:
            # se realiza un paso especifico dentro del flujo del analisis.
            continue

        # se realiza un paso especifico dentro del flujo del analisis.
        salida.append(
            # se inicia un diccionario para organizar informacion por categorias.
            {
                # se realiza un paso especifico dentro del flujo del analisis.
                **autor,
                # se define una categoria del diccionario y sus terminos asociados.
                "author_name_canonical": nombre_canonico,
                # se define una categoria del diccionario y sus terminos asociados.
                "author_key": author_key,
            # se cierra la lista, diccionario o llamada que se abrio antes.
            }
        # se cierra la lista, diccionario o llamada que se abrio antes.
        )
    # se devuelve el resultado calculado por la funcion.
    return salida


# se crea la funcion clasificar_cluster para reutilizar esta parte del proceso.
def clasificar_cluster(texto):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Asigna un cluster principal y deja trazabilidad por puntajes.

    MEJORA:
    En lugar de solo devolver una categoria, guardamos el puntaje de cada
    cluster. Eso ayuda mucho para justificar el analisis comparativo.
    """
    # se guarda un valor o calculo intermedio para usarlo despues.
    scores = {cluster: contar_terminos(texto, terminos) for cluster, terminos in CLUSTERS.items()}
    # se guarda un valor o calculo intermedio para usarlo despues.
    max_score = max(scores.values()) if scores else 0

    # se revisa una condicion antes de continuar con este bloque.
    if max_score == 0:
        # se guarda un valor o calculo intermedio para usarlo despues.
        principal = "otro"
    # se ejecuta este bloque cuando no se cumple la condicion anterior.
    else:
        # se guarda un valor o calculo intermedio para usarlo despues.
        ganadores = [nombre for nombre, score in scores.items() if score == max_score]
        # se guarda un valor o calculo intermedio para usarlo despues.
        principal = ganadores[0] if len(ganadores) == 1 else "mixto"

    # se guarda un valor o calculo intermedio para usarlo despues.
    secundarios = [nombre for nombre, score in scores.items() if score > 0]
    # se devuelve el resultado calculado por la funcion.
    return pd.Series(
        # se inicia un diccionario para organizar informacion por categorias.
        {
            # se define una categoria del diccionario y sus terminos asociados.
            "cluster_principal": principal,
            # se agrega este termino a la lista para detectarlo en los articulos.
            "clusters_detectados": ", ".join(secundarios) if secundarios else "ninguno",
            # se define una categoria del diccionario y sus terminos asociados.
            "score_social": scores.get("social", 0),
            # se define una categoria del diccionario y sus terminos asociados.
            "score_academico": scores.get("academico", 0),
            # se define una categoria del diccionario y sus terminos asociados.
            "score_creativo": scores.get("creativo", 0),
        # se cierra la lista, diccionario o llamada que se abrio antes.
        }
    # se cierra la lista, diccionario o llamada que se abrio antes.
    )


# se crea la funcion top_palabras_por_cluster para reutilizar esta parte del proceso.
def top_palabras_por_cluster(df):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Calcula TF-IDF por cluster para identificar lenguaje caracteristico.
    """
    # se agrupan los datos para calcular metricas por categoria.
    textos = df.groupby("cluster_principal")["texto_total"].apply(lambda x: " ".join(x))
    # se guarda un valor o calculo intermedio para usarlo despues.
    textos = textos[textos.index.isin(["social", "academico", "creativo", "mixto"])]

    # se revisa una condicion antes de continuar con este bloque.
    if textos.empty:
        # se devuelve el resultado calculado por la funcion.
        return pd.DataFrame()

    # se inicia un diccionario para organizar informacion por categorias.
    stopwords = {
        # se agrega este termino a la lista para detectarlo en los articulos.
        "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "a", "an", "is", "are", "this", "that", "using", "use", "based",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "students", "student", "university", "education", "higher",
    # se cierra la lista, diccionario o llamada que se abrio antes.
    }
    # se guarda un valor o calculo intermedio para usarlo despues.
    tokens_por_cluster = {}
    # se cuentan apariciones para obtener frecuencias.
    df_por_termino = Counter()

    # se recorren varios elementos para procesarlos uno por uno.
    for cluster, texto in textos.items():
        # se guarda un valor o calculo intermedio para usarlo despues.
        tokens = [t for t in texto.split() if len(t) > 2 and t not in stopwords]
        # se cuentan apariciones para obtener frecuencias.
        conteo = Counter(tokens)
        # se guarda un valor o calculo intermedio para usarlo despues.
        tokens_por_cluster[cluster] = conteo
        # se recorren varios elementos para procesarlos uno por uno.
        for termino in conteo:
            # se guarda un valor o calculo intermedio para usarlo despues.
            df_por_termino[termino] += 1

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_clusters = len(tokens_por_cluster)
    # se guarda un valor o calculo intermedio para usarlo despues.
    filas = {}
    # se recorren varios elementos para procesarlos uno por uno.
    for cluster, conteo in tokens_por_cluster.items():
        # se guarda un valor o calculo intermedio para usarlo despues.
        puntajes = {}
        # se guarda un valor o calculo intermedio para usarlo despues.
        total_tokens = sum(conteo.values()) or 1
        # se recorren varios elementos para procesarlos uno por uno.
        for termino, tf in conteo.items():
            # se guarda un valor o calculo intermedio para usarlo despues.
            idf = log((1 + total_clusters) / (1 + df_por_termino[termino])) + 1
            # se guarda un valor o calculo intermedio para usarlo despues.
            puntajes[termino] = (tf / total_tokens) * idf
        # se guarda un valor o calculo intermedio para usarlo despues.
        top_terminos = dict(sorted(puntajes.items(), key=lambda item: item[1], reverse=True)[:40])
        # se guarda un valor o calculo intermedio para usarlo despues.
        filas[cluster] = top_terminos

    # se devuelve el resultado calculado por la funcion.
    return pd.DataFrame.from_dict(filas, orient="index").fillna(0)


# se crea la funcion frecuencia_real_por_cluster para reutilizar esta parte del proceso.
def frecuencia_real_por_cluster(df):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Calcula frecuencia absoluta de terminos por cluster.
    """
    # se revisa una condicion antes de continuar con este bloque.
    if df.empty:
        # se devuelve el resultado calculado por la funcion.
        return pd.DataFrame()

    # se inicia un diccionario para organizar informacion por categorias.
    stopwords = {
        # se agrega este termino a la lista para detectarlo en los articulos.
        "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "a", "an", "is", "are", "this", "that", "using", "use", "based",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "students", "student", "university", "education", "higher",
    # se cierra la lista, diccionario o llamada que se abrio antes.
    }
    # se guarda un valor o calculo intermedio para usarlo despues.
    filas = []

    # se recorren varios elementos para procesarlos uno por uno.
    for _, row in df.iterrows():
        # se guarda un valor o calculo intermedio para usarlo despues.
        tokens = [t for t in row["texto_total"].split() if len(t) > 2 and t not in stopwords]
        # se cuentan apariciones para obtener frecuencias.
        conteo = Counter(tokens).most_common(40)
        # se guarda un valor o calculo intermedio para usarlo despues.
        fila = {"cluster_principal": row["cluster_principal"]}
        # se ejecuta una funcion o metodo para procesar los datos.
        fila.update(dict(conteo))
        # se ejecuta una funcion o metodo para procesar los datos.
        filas.append(fila)

    # se rellenan valores vacios para evitar errores durante el analisis.
    tabla = pd.DataFrame(filas).fillna(0)
    # se devuelve el resultado calculado por la funcion.
    return tabla.groupby("cluster_principal").sum(numeric_only=True)


# se crea la funcion top_terminos_por_cluster para reutilizar esta parte del proceso.
def top_terminos_por_cluster(df, top_n=20):
    # se agrega este termino a la lista para detectarlo en los articulos.
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
    # se revisa una condicion antes de continuar con este bloque.
    if df.empty:
        # se devuelve el resultado calculado por la funcion.
        return pd.DataFrame()

    # se inicia un diccionario para organizar informacion por categorias.
    stopwords = {
        # se agrega este termino a la lista para detectarlo en los articulos.
        "the", "and", "of", "to", "in", "for", "on", "with", "by", "from",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "a", "an", "is", "are", "this", "that", "using", "use", "based",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "students", "student", "university", "education", "higher", "artificial",
        # se agrega este termino a la lista para detectarlo en los articulos.
        "intelligence",
    # se cierra la lista, diccionario o llamada que se abrio antes.
    }

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_docs = len(df)
    # se cuentan apariciones para obtener frecuencias.
    corpus_doc_freq = Counter()

    # se recorren varios elementos para procesarlos uno por uno.
    for texto in df["texto_total"]:
        # se guarda un valor o calculo intermedio para usarlo despues.
        tokens_unicos = {t for t in texto.split() if len(t) > 2 and t not in stopwords}
        # se ejecuta una funcion o metodo para procesar los datos.
        corpus_doc_freq.update(tokens_unicos)

    # se guarda un valor o calculo intermedio para usarlo despues.
    filas = []
    # se recorren varios elementos para procesarlos uno por uno.
    for cluster, df_cluster in df.groupby("cluster_principal"):
        # se guarda un valor o calculo intermedio para usarlo despues.
        doc_count_cluster = len(df_cluster)
        # se cuentan apariciones para obtener frecuencias.
        token_counter = Counter()
        # se cuentan apariciones para obtener frecuencias.
        doc_freq_cluster = Counter()

        # se recorren varios elementos para procesarlos uno por uno.
        for texto in df_cluster["texto_total"]:
            # se guarda un valor o calculo intermedio para usarlo despues.
            tokens = [t for t in texto.split() if len(t) > 2 and t not in stopwords]
            # se ejecuta una funcion o metodo para procesar los datos.
            token_counter.update(tokens)
            # se ejecuta una funcion o metodo para procesar los datos.
            doc_freq_cluster.update(set(tokens))

        # se guarda un valor o calculo intermedio para usarlo despues.
        total_tokens_cluster = sum(token_counter.values()) or 1
        # se recorren varios elementos para procesarlos uno por uno.
        for termino, frecuencia_total in token_counter.most_common(top_n):
            # se guarda un valor o calculo intermedio para usarlo despues.
            articulos_con_termino_cluster = doc_freq_cluster[termino]
            # se guarda un valor o calculo intermedio para usarlo despues.
            articulos_con_termino_corpus = corpus_doc_freq[termino]
            # se realiza un paso especifico dentro del flujo del analisis.
            filas.append(
                # se inicia un diccionario para organizar informacion por categorias.
                {
                    # se define una categoria del diccionario y sus terminos asociados.
                    "cluster_principal": cluster,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "termino": termino,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "frecuencia_total_cluster": frecuencia_total,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "articulos_cluster_con_termino": articulos_con_termino_cluster,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "porcentaje_articulos_cluster": round((articulos_con_termino_cluster / doc_count_cluster) * 100, 2),
                    # se define una categoria del diccionario y sus terminos asociados.
                    "articulos_corpus_con_termino": articulos_con_termino_corpus,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "porcentaje_articulos_corpus": round((articulos_con_termino_corpus / total_docs) * 100, 2),
                    # se define una categoria del diccionario y sus terminos asociados.
                    "porcentaje_uso_cluster": round((frecuencia_total / total_tokens_cluster) * 100, 2),
                # se cierra la lista, diccionario o llamada que se abrio antes.
                }
            # se cierra la lista, diccionario o llamada que se abrio antes.
            )

    # se devuelve el resultado calculado por la funcion.
    return pd.DataFrame(filas)


# se crea la funcion top_terminos_cluster_otro para reutilizar esta parte del proceso.
def top_terminos_cluster_otro(df, top_n=15):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Devuelve solo terminos interpretables del cluster "otro".

    Columnas:
    - porcentaje_articulos_corpus: porcentaje de articulos del corpus total
      donde aparece el termino
    - frecuencia_por_texto_otro: peso del termino dentro del vocabulario del
      cluster otro
    """
    # se guarda un valor o calculo intermedio para usarlo despues.
    df_otro = df[df["cluster_principal"] == "otro"].copy()
    # se revisa una condicion antes de continuar con este bloque.
    if df_otro.empty:
        # se devuelve el resultado calculado por la funcion.
        return pd.DataFrame()

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_docs_corpus = len(df)
    # se cuentan apariciones para obtener frecuencias.
    contador_total = Counter()
    # se cuentan apariciones para obtener frecuencias.
    docs_corpus = Counter()

    # se recorren varios elementos para procesarlos uno por uno.
    for texto in df_otro["texto_total"]:
        # se inicia una lista de valores para usarla en el analisis.
        tokens = [
            # se ejecuta una funcion o metodo para procesar los datos.
            t for t in texto.split()
            # se revisa una condicion antes de continuar con este bloque.
            if len(t) > 2 and t not in STOPWORDS_OTRO and not t.isdigit()
        # se cierra la lista, diccionario o llamada que se abrio antes.
        ]
        # se ejecuta una funcion o metodo para procesar los datos.
        contador_total.update(tokens)

    # se recorren varios elementos para procesarlos uno por uno.
    for texto in df["texto_total"]:
        # se inicia un diccionario para organizar informacion por categorias.
        tokens_unicos = {
            # se ejecuta una funcion o metodo para procesar los datos.
            t for t in texto.split()
            # se revisa una condicion antes de continuar con este bloque.
            if len(t) > 2 and t not in STOPWORDS_OTRO and not t.isdigit()
        # se cierra la lista, diccionario o llamada que se abrio antes.
        }
        # se ejecuta una funcion o metodo para procesar los datos.
        docs_corpus.update(tokens_unicos)

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_tokens_otro = sum(contador_total.values()) or 1
    # se guarda un valor o calculo intermedio para usarlo despues.
    filas = []
    # se recorren varios elementos para procesarlos uno por uno.
    for termino, frecuencia_total in contador_total.most_common(top_n):
        # se realiza un paso especifico dentro del flujo del analisis.
        filas.append(
            # se inicia un diccionario para organizar informacion por categorias.
            {
                # se define una categoria del diccionario y sus terminos asociados.
                "termino": termino,
                # se define una categoria del diccionario y sus terminos asociados.
                "porcentaje_articulos_corpus": round((docs_corpus[termino] / total_docs_corpus) * 100, 2),
                # se define una categoria del diccionario y sus terminos asociados.
                "frecuencia_por_texto_otro": round((frecuencia_total / total_tokens_otro) * 100, 2),
            # se cierra la lista, diccionario o llamada que se abrio antes.
            }
        # se cierra la lista, diccionario o llamada que se abrio antes.
        )

    # se devuelve el resultado calculado por la funcion.
    return pd.DataFrame(filas)


# se crea la funcion medir_expresiones_relevantes para reutilizar esta parte del proceso.
def medir_expresiones_relevantes(df, expresiones):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Mide expresiones definidas por el investigador en cada cluster.

    MEJORA:
    Las palabras sueltas son utiles, pero a veces necesitas expresiones
    concretas como "chatgpt" o "social media". Esta tabla calcula el
    porcentaje dentro de cada cluster y sobre el corpus total.
    """
    # se revisa una condicion antes de continuar con este bloque.
    if df.empty:
        # se devuelve el resultado calculado por la funcion.
        return pd.DataFrame()

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_docs = len(df)
    # se guarda un valor o calculo intermedio para usarlo despues.
    filas = []

    # se recorren varios elementos para procesarlos uno por uno.
    for expresion in expresiones:
        # se guarda un valor o calculo intermedio para usarlo despues.
        expresion_norm = normalizar_texto(expresion)
        # se guarda un valor o calculo intermedio para usarlo despues.
        patron = r"\b" + re.escape(expresion_norm).replace(r"\ ", r"\s+") + r"\b"

        # se usan funciones de texto para limpiar o buscar informacion en columnas.
        mask_corpus = df["texto_total"].str.contains(patron, regex=True, na=False)
        # se guarda un valor o calculo intermedio para usarlo despues.
        docs_corpus = int(mask_corpus.sum())

        # se recorren varios elementos para procesarlos uno por uno.
        for cluster, df_cluster in df.groupby("cluster_principal"):
            # se usan funciones de texto para limpiar o buscar informacion en columnas.
            mask_cluster = df_cluster["texto_total"].str.contains(patron, regex=True, na=False)
            # se guarda un valor o calculo intermedio para usarlo despues.
            docs_cluster = int(mask_cluster.sum())
            # se guarda un valor o calculo intermedio para usarlo despues.
            total_cluster = len(df_cluster)

            # se realiza un paso especifico dentro del flujo del analisis.
            filas.append(
                # se inicia un diccionario para organizar informacion por categorias.
                {
                    # se define una categoria del diccionario y sus terminos asociados.
                    "cluster_principal": cluster,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "expresion": expresion,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "articulos_cluster_con_expresion": docs_cluster,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "porcentaje_articulos_cluster": round((docs_cluster / total_cluster) * 100, 2) if total_cluster else 0,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "articulos_corpus_con_expresion": docs_corpus,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "porcentaje_articulos_corpus": round((docs_corpus / total_docs) * 100, 2) if total_docs else 0,
                # se cierra la lista, diccionario o llamada que se abrio antes.
                }
            # se cierra la lista, diccionario o llamada que se abrio antes.
            )

    # se devuelve el resultado calculado por la funcion.
    return pd.DataFrame(filas)


# se crea la funcion preparar_texto_para_frases para reutilizar esta parte del proceso.
def preparar_texto_para_frases(texto, expresiones_compuestas):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Convierte frases compuestas en un solo token con guion bajo.

    MEJORA:
    "artificial intelligence" pasa a "artificial_intelligence". Con esto
    el conteo del cluster "otro" respeta el concepto completo.
    """
    # se guarda un valor o calculo intermedio para usarlo despues.
    texto_procesado = texto
    # se recorren varios elementos para procesarlos uno por uno.
    for expresion in expresiones_compuestas:
        # se guarda un valor o calculo intermedio para usarlo despues.
        expresion_norm = normalizar_texto(expresion)
        # se guarda un valor o calculo intermedio para usarlo despues.
        token_unido = expresion_norm.replace(" ", "_")
        # se guarda un valor o calculo intermedio para usarlo despues.
        patron = r"\b" + re.escape(expresion_norm).replace(r"\ ", r"\s+") + r"\b"
        # se guarda un valor o calculo intermedio para usarlo despues.
        texto_procesado = re.sub(patron, token_unido, texto_procesado)
    # se devuelve el resultado calculado por la funcion.
    return texto_procesado


# se crea la funcion top_frases_y_terminos_cluster_otro para reutilizar esta parte del proceso.
def top_frases_y_terminos_cluster_otro(df, top_n=15):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Reporta el cluster "otro" priorizando frases compuestas y terminos utiles.

    Salida:
    - termino_o_frase
    - porcentaje_articulos_corpus
    - frecuencia_por_texto_otro
    """
    # se guarda un valor o calculo intermedio para usarlo despues.
    df_otro = df[df["cluster_principal"] == "otro"].copy()
    # se revisa una condicion antes de continuar con este bloque.
    if df_otro.empty:
        # se devuelve el resultado calculado por la funcion.
        return pd.DataFrame()

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_docs_corpus = len(df)
    # se cuentan apariciones para obtener frecuencias.
    contador_total = Counter()
    # se cuentan apariciones para obtener frecuencias.
    docs_corpus = Counter()

    # se inicia una lista de valores para usarla en el analisis.
    textos_otro = [
        # se ejecuta una funcion o metodo para procesar los datos.
        preparar_texto_para_frases(texto, EXPRESIONES_COMPUESTAS_PRIORITARIAS)
        # se recorren varios elementos para procesarlos uno por uno.
        for texto in df_otro["texto_total"]
    # se cierra la lista, diccionario o llamada que se abrio antes.
    ]
    # se inicia una lista de valores para usarla en el analisis.
    textos_corpus = [
        # se ejecuta una funcion o metodo para procesar los datos.
        preparar_texto_para_frases(texto, EXPRESIONES_COMPUESTAS_PRIORITARIAS)
        # se recorren varios elementos para procesarlos uno por uno.
        for texto in df["texto_total"]
    # se cierra la lista, diccionario o llamada que se abrio antes.
    ]

    # se guarda un valor o calculo intermedio para usarlo despues.
    componentes_bloqueados = set()
    # se recorren varios elementos para procesarlos uno por uno.
    for expresion in EXPRESIONES_COMPUESTAS_PRIORITARIAS:
        # se guarda un valor o calculo intermedio para usarlo despues.
        partes = normalizar_texto(expresion).split()
        # se revisa una condicion antes de continuar con este bloque.
        if len(partes) > 1:
            # se ejecuta una funcion o metodo para procesar los datos.
            componentes_bloqueados.update(partes)

    # se recorren varios elementos para procesarlos uno por uno.
    for texto in textos_otro:
        # se guarda un valor o calculo intermedio para usarlo despues.
        tokens = []
        # se recorren varios elementos para procesarlos uno por uno.
        for token in texto.split():
            # se revisa una condicion antes de continuar con este bloque.
            if len(token) <= 2 or token.isdigit():
                # se realiza un paso especifico dentro del flujo del analisis.
                continue
            # se revisa una condicion antes de continuar con este bloque.
            if token in STOPWORDS_OTRO:
                # se realiza un paso especifico dentro del flujo del analisis.
                continue
            # se revisa una condicion antes de continuar con este bloque.
            if "_" not in token and token in componentes_bloqueados:
                # se realiza un paso especifico dentro del flujo del analisis.
                continue
            # se ejecuta una funcion o metodo para procesar los datos.
            tokens.append(token)
        # se ejecuta una funcion o metodo para procesar los datos.
        contador_total.update(tokens)

    # se recorren varios elementos para procesarlos uno por uno.
    for texto in textos_corpus:
        # se guarda un valor o calculo intermedio para usarlo despues.
        tokens_unicos = set()
        # se recorren varios elementos para procesarlos uno por uno.
        for token in texto.split():
            # se revisa una condicion antes de continuar con este bloque.
            if len(token) <= 2 or token.isdigit():
                # se realiza un paso especifico dentro del flujo del analisis.
                continue
            # se revisa una condicion antes de continuar con este bloque.
            if token in STOPWORDS_OTRO:
                # se realiza un paso especifico dentro del flujo del analisis.
                continue
            # se revisa una condicion antes de continuar con este bloque.
            if "_" not in token and token in componentes_bloqueados:
                # se realiza un paso especifico dentro del flujo del analisis.
                continue
            # se ejecuta una funcion o metodo para procesar los datos.
            tokens_unicos.add(token)
        # se ejecuta una funcion o metodo para procesar los datos.
        docs_corpus.update(tokens_unicos)

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_tokens_otro = sum(contador_total.values()) or 1
    # se guarda un valor o calculo intermedio para usarlo despues.
    filas = []
    # se recorren varios elementos para procesarlos uno por uno.
    for termino, frecuencia_total in contador_total.most_common(top_n):
        # se realiza un paso especifico dentro del flujo del analisis.
        filas.append(
            # se inicia un diccionario para organizar informacion por categorias.
            {
                # se define una categoria del diccionario y sus terminos asociados.
                "termino_o_frase": termino.replace("_", " "),
                # se define una categoria del diccionario y sus terminos asociados.
                "porcentaje_articulos_corpus": round((docs_corpus[termino] / total_docs_corpus) * 100, 2),
                # se define una categoria del diccionario y sus terminos asociados.
                "frecuencia_por_texto_otro": round((frecuencia_total / total_tokens_otro) * 100, 2),
            # se cierra la lista, diccionario o llamada que se abrio antes.
            }
        # se cierra la lista, diccionario o llamada que se abrio antes.
        )

    # se devuelve el resultado calculado por la funcion.
    return pd.DataFrame(filas)


# se crea la funcion medir_expresiones_para_redaccion para reutilizar esta parte del proceso.
def medir_expresiones_para_redaccion(df, expresiones, clusters_objetivo):
    # se agrega este termino a la lista para detectarlo en los articulos.
    """
    Genera una tabla breve para redactar resultados academicos.

    - porcentaje_en_cluster: en que porcentaje de los articulos del cluster
      aparece la expresion al menos una vez
    - porcentaje_global: en que porcentaje del corpus total aparece
    - promedio_por_articulo: cuantas veces aparece en promedio por articulo
      dentro del cluster
    """
    # se revisa una condicion antes de continuar con este bloque.
    if df.empty:
        # se devuelve el resultado calculado por la funcion.
        return pd.DataFrame()

    # se guarda un valor o calculo intermedio para usarlo despues.
    total_docs = len(df)
    # se guarda un valor o calculo intermedio para usarlo despues.
    filas = []

    # se recorren varios elementos para procesarlos uno por uno.
    for expresion in expresiones:
        # se guarda un valor o calculo intermedio para usarlo despues.
        expresion_norm = normalizar_texto(expresion)
        # se guarda un valor o calculo intermedio para usarlo despues.
        patron = r"\b" + re.escape(expresion_norm).replace(r"\ ", r"\s+") + r"\b"
        # se usan funciones de texto para limpiar o buscar informacion en columnas.
        docs_corpus = int(df["texto_total"].str.contains(patron, regex=True, na=False).sum())

        # se recorren varios elementos para procesarlos uno por uno.
        for cluster in clusters_objetivo:
            # se guarda un valor o calculo intermedio para usarlo despues.
            df_cluster = df[df["cluster_principal"] == cluster]
            # se revisa una condicion antes de continuar con este bloque.
            if df_cluster.empty:
                # se realiza un paso especifico dentro del flujo del analisis.
                continue

            # se rellenan valores vacios para evitar errores durante el analisis.
            apariciones = df_cluster["texto_total"].str.count(patron).fillna(0)
            # se guarda un valor o calculo intermedio para usarlo despues.
            total_apariciones = float(apariciones.sum())
            # se guarda un valor o calculo intermedio para usarlo despues.
            articulos_con_expresion = int((apariciones > 0).sum())
            # se guarda un valor o calculo intermedio para usarlo despues.
            total_articulos_cluster = len(df_cluster)

            # se realiza un paso especifico dentro del flujo del analisis.
            filas.append(
                # se inicia un diccionario para organizar informacion por categorias.
                {
                    # se define una categoria del diccionario y sus terminos asociados.
                    "cluster_principal": cluster,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "expresion": expresion,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "porcentaje_en_cluster": round((articulos_con_expresion / total_articulos_cluster) * 100, 2)
                    # se revisa una condicion antes de continuar con este bloque.
                    if total_articulos_cluster
                    # se realiza un paso especifico dentro del flujo del analisis.
                    else 0,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "porcentaje_global": round((docs_corpus / total_docs) * 100, 2) if total_docs else 0,
                    # se define una categoria del diccionario y sus terminos asociados.
                    "promedio_por_articulo": round((total_apariciones / total_articulos_cluster), 2)
                    # se revisa una condicion antes de continuar con este bloque.
                    if total_articulos_cluster
                    # se realiza un paso especifico dentro del flujo del analisis.
                    else 0,
                # se cierra la lista, diccionario o llamada que se abrio antes.
                }
            # se cierra la lista, diccionario o llamada que se abrio antes.
            )

    # se devuelve el resultado calculado por la funcion.
    return pd.DataFrame(filas)


# =========================================
# 3. CARGA Y VALIDACION DE DATOS
# =========================================
# Aqui leemos el CSV exportado desde Scopus. Desde este punto, `df` sera la
# tabla principal sobre la que trabaja todo el analisis.
# se lee el CSV de Scopus y se convierte en una tabla de pandas.
df = pd.read_csv(INPUT_FILE)
# se muestra informacion en pantalla para revisar el avance o los resultados.
print("Registros iniciales:", len(df))

# Validamos que las columnas minimas existan. Si falta una de estas, el resto
# del analisis ya no seria confiable o simplemente fallaria.
# se guarda un valor o calculo intermedio para usarlo despues.
columnas_obligatorias = ["Title", "Abstract", "Year", "Cited by"]
# se guarda un valor o calculo intermedio para usarlo despues.
faltantes = [col for col in columnas_obligatorias if col not in df.columns]
# se revisa una condicion antes de continuar con este bloque.
if faltantes:
    # se detiene el programa y se muestra un mensaje de error.
    raise ValueError(f"Faltan columnas obligatorias en el CSV: {faltantes}")

# Guardamos los nombres reales de columnas de autores porque segun el formato
# de exportacion de Scopus pueden variar o venir vacias.
# se guarda un valor o calculo intermedio para usarlo despues.
col_autores = columna_disponible(df, ["Authors"])
# se guarda un valor o calculo intermedio para usarlo despues.
col_autores_full = columna_disponible(df, ["Author full names"])
# se guarda un valor o calculo intermedio para usarlo despues.
col_author_ids = columna_disponible(df, ["Author(s) ID"])


# =========================================
# 4. LIMPIEZA BASE
# =========================================
# MEJORA:
# Pasamos la limpieza a un bloque explicito para que quede claro que
# columnas se normalizan y con que objetivo.
# Esta parte no clasifica todavia; solo prepara el texto para que el conteo
# de terminos sea mas consistente y menos sensible a mayusculas o ruido.
# se recorren varios elementos para procesarlos uno por uno.
for col in ["Title", "Abstract", "Affiliations", "Author Keywords", "Index Keywords", "Source title"]:
    # se revisa una condicion antes de continuar con este bloque.
    if col in df.columns:
        # se rellenan valores vacios para evitar errores durante el analisis.
        df[col] = df[col].fillna("").astype(str).str.strip()

# Creamos versiones limpias del titulo, resumen y keywords. Estas son las
# columnas que realmente alimentan los filtros y los clusters.
# se aplica una funcion a cada dato o fila de la tabla.
df["title_clean"] = df["Title"].apply(normalizar_texto)
# se aplica una funcion a cada dato o fila de la tabla.
df["abstract_clean"] = df["Abstract"].apply(normalizar_texto)
# se guarda un valor o calculo intermedio para usarlo despues.
df["keywords_clean"] = (
    # se aplica una funcion a cada dato o fila de la tabla.
    df.get("Author Keywords", "").fillna("").astype(str).apply(normalizar_texto)
    # se revisa una condicion antes de continuar con este bloque.
    if "Author Keywords" in df.columns
    # se realiza un paso especifico dentro del flujo del analisis.
    else ""
# se cierra la lista, diccionario o llamada que se abrio antes.
)

# `texto_total` concentra toda la evidencia textual que vamos a analizar.
# Esto evita revisar por separado titulo, abstract y keywords en cada paso.
# se guarda un valor o calculo intermedio para usarlo despues.
df["texto_total"] = (
    # se rellenan valores vacios para evitar errores durante el analisis.
    df["title_clean"].fillna("")
    # se realiza un paso especifico dentro del flujo del analisis.
    + " "
    # se rellenan valores vacios para evitar errores durante el analisis.
    + df["abstract_clean"].fillna("")
    # se realiza un paso especifico dentro del flujo del analisis.
    + " "
    # se ejecuta una funcion o metodo para procesar los datos.
    + (df["keywords_clean"] if isinstance(df["keywords_clean"], pd.Series) else "")
# se usan funciones de texto para limpiar o buscar informacion en columnas.
).str.replace(r"\s+", " ", regex=True).str.strip()

# se guarda un valor o calculo intermedio para usarlo despues.
df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
# se rellenan valores vacios para evitar errores durante el analisis.
df["Cited by"] = pd.to_numeric(df["Cited by"], errors="coerce").fillna(0).astype(int)

# MEJORA:
# Eliminamos duplicados con DOI cuando exista, porque es mas estable que el
# titulo. Si no hay DOI, usamos titulo limpio como respaldo.
# Primero nos quedamos con la version mas citada cuando parece haber
# duplicados, y luego removemos filas repetidas.
# se revisa una condicion antes de continuar con este bloque.
if "DOI" in df.columns:
    # se rellenan valores vacios para evitar errores durante el analisis.
    df["DOI"] = df["DOI"].fillna("").astype(str).str.strip().str.lower()
    # se ordenan los datos para mostrar primero los resultados mas importantes.
    df = df.sort_values(["DOI", "Cited by"], ascending=[True, False])
    # se eliminan registros duplicados para no contarlos dos veces.
    df = df.drop_duplicates(subset=["DOI", "title_clean"], keep="first")
# se ejecuta este bloque cuando no se cumple la condicion anterior.
else:
    # se eliminan registros duplicados para no contarlos dos veces.
    df = df.drop_duplicates(subset=["title_clean"], keep="first")

# Quitamos registros sin anio, sin titulo/resumen util o con texto demasiado
# corto para un analisis tematico razonable.
# se eliminan filas que no tienen datos indispensables.
df = df.dropna(subset=["Year"])
# se convierte la columna al tipo de dato necesario.
df["Year"] = df["Year"].astype(int)
# se guarda un valor o calculo intermedio para usarlo despues.
df = df[(df["title_clean"] != "") & (df["abstract_clean"] != "")]
# se usan funciones de texto para limpiar o buscar informacion en columnas.
df = df[df["texto_total"].str.len() >= 80]

# Estos dos puntajes son la puerta de entrada al corpus final:
# 1. score_ia: evidencia de inteligencia artificial
# 2. score_poblacion: evidencia de poblacion universitaria/academica
# se aplica una funcion a cada dato o fila de la tabla.
df["score_ia"] = df["texto_total"].apply(lambda texto: contar_terminos(texto, PALABRAS_IA))
# se aplica una funcion a cada dato o fila de la tabla.
df["score_poblacion"] = df["texto_total"].apply(lambda texto: contar_terminos(texto, PALABRAS_POBLACION))

# MEJORA:
# El filtro ya no es solo booleano. Primero calculamos puntajes y luego
# decidimos con base en ellos. Eso te deja trazabilidad para justificar
# por que un articulo entro al corpus.
# se guarda un valor o calculo intermedio para usarlo despues.
df = df[(df["score_ia"] > 0) & (df["score_poblacion"] > 0)].copy()
# se muestra informacion en pantalla para revisar el avance o los resultados.
print("Despues del filtrado tematico:", len(df))


# =========================================
# 5. LIMPIEZA Y NORMALIZACION DE AUTORES
# =========================================
# En este punto extraemos una estructura por autor dentro de cada articulo.
# Cada elemento guarda nombre original, nombre limpio e ID de Scopus si existe.
# se aplica una funcion a cada dato o fila de la tabla.
df["authors_struct"] = df.apply(
    # se ejecuta una funcion o metodo para procesar los datos.
    lambda row: extraer_autores_fila(row, col_autores, col_autores_full, col_author_ids),
    # se guarda un valor o calculo intermedio para usarlo despues.
    axis=1,
# se cierra la lista, diccionario o llamada que se abrio antes.
)

# `mapa_autores` intenta resolver variantes del mismo nombre. Si hay
# `Author(s) ID`, se usa como identidad principal. Si no, se prueba similitud
# conservadora entre nombres limpios.
# se guarda un valor o calculo intermedio para usarlo despues.
mapa_autores = construir_mapa_autores(df["authors_struct"])
# se aplica una funcion a cada dato o fila de la tabla.
df["authors_struct"] = df["authors_struct"].apply(lambda autores: enriquecer_autores(autores, mapa_autores))

# MEJORA:
# Guardamos listas resumidas para facilitar inspeccion manual del resultado.
# `authors_canonical` sirve para leer rapido los autores ya normalizados.
# `author_keys` sirve para contar de forma estable a un mismo autor.
# se aplica una funcion a cada dato o fila de la tabla.
df["authors_canonical"] = df["authors_struct"].apply(
    # se realiza un paso especifico dentro del flujo del analisis.
    lambda autores: [a["author_name_canonical"] for a in autores if a["author_name_canonical"]]
# se cierra la lista, diccionario o llamada que se abrio antes.
)
# se aplica una funcion a cada dato o fila de la tabla.
df["author_keys"] = df["authors_struct"].apply(
    # se realiza un paso especifico dentro del flujo del analisis.
    lambda autores: [a["author_key"] for a in autores if a["author_key"]]
# se cierra la lista, diccionario o llamada que se abrio antes.
)
# se aplica una funcion a cada dato o fila de la tabla.
df["num_authors"] = df["author_keys"].apply(len)


# =========================================
# 6. CLUSTERS TEMATICOS
# =========================================
# Aqui asignamos a cada articulo un cluster principal:
# social, academico, creativo, mixto u otro.
# Ademas guardamos los puntajes de cada eje para poder justificar la clasificacion.
# se aplica una funcion a cada dato o fila de la tabla.
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
# se guarda un valor o calculo intermedio para usarlo despues.
filas_autores = []
# se recorren varios elementos para procesarlos uno por uno.
for _, row in df.iterrows():
    # se recorren varios elementos para procesarlos uno por uno.
    for autor in row["authors_struct"]:
        # se realiza un paso especifico dentro del flujo del analisis.
        filas_autores.append(
            # se inicia un diccionario para organizar informacion por categorias.
            {
                # se define una categoria del diccionario y sus terminos asociados.
                "author_key": autor["author_key"],
                # se define una categoria del diccionario y sus terminos asociados.
                "author_name_canonical": autor["author_name_canonical"],
                # se define una categoria del diccionario y sus terminos asociados.
                "author_name_raw": autor["author_name_raw"],
                # se define una categoria del diccionario y sus terminos asociados.
                "author_scopus_id": autor["author_scopus_id"],
                # se define una categoria del diccionario y sus terminos asociados.
                "Title": row["Title"],
                # se define una categoria del diccionario y sus terminos asociados.
                "Year": row["Year"],
                # se define una categoria del diccionario y sus terminos asociados.
                "Cited by": row["Cited by"],
                # se define una categoria del diccionario y sus terminos asociados.
                "cluster_principal": row["cluster_principal"],
                # se define una categoria del diccionario y sus terminos asociados.
                "clusters_detectados": row["clusters_detectados"],
                # se define una categoria del diccionario y sus terminos asociados.
                "score_ia": row["score_ia"],
                # se define una categoria del diccionario y sus terminos asociados.
                "score_social": row["score_social"],
                # se define una categoria del diccionario y sus terminos asociados.
                "score_academico": row["score_academico"],
                # se define una categoria del diccionario y sus terminos asociados.
                "score_creativo": row["score_creativo"],
                # se agrega este termino a la lista para detectarlo en los articulos.
                "EID": row["EID"] if "EID" in df.columns else "",
                # se agrega este termino a la lista para detectarlo en los articulos.
                "DOI": row["DOI"] if "DOI" in df.columns else "",
            # se cierra la lista, diccionario o llamada que se abrio antes.
            }
        # se cierra la lista, diccionario o llamada que se abrio antes.
        )

# se guarda un valor o calculo intermedio para usarlo despues.
df_autores = pd.DataFrame(filas_autores)

# se revisa una condicion antes de continuar con este bloque.
if df_autores.empty:
    # se detiene el programa y se muestra un mensaje de error.
    raise ValueError("No se pudieron extraer autores del corpus filtrado.")


# =========================================
# 8. METRICAS POR AUTOR
# =========================================
# `resumen_autores` consolida lo principal por autor:
# publicaciones, citas, anios activos y afinidad con cada cluster.
# se crea la funcion moda_segura para reutilizar esta parte del proceso.
def moda_segura(series):
    # se eliminan filas que no tienen datos indispensables.
    series = series.dropna()
    # se revisa una condicion antes de continuar con este bloque.
    if series.empty:
        # se devuelve el resultado calculado por la funcion.
        return ""
    # se guarda un valor o calculo intermedio para usarlo despues.
    modos = series.mode()
    # se devuelve el resultado calculado por la funcion.
    return modos.iloc[0] if not modos.empty else ""


# se guarda un valor o calculo intermedio para usarlo despues.
resumen_autores = (
    # se agrupan los datos para calcular metricas por categoria.
    df_autores.groupby("author_key")
    # se calculan resumenes como conteos, promedios o sumas.
    .agg(
        # se guarda un valor o calculo intermedio para usarlo despues.
        author_name=("author_name_canonical", "first"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        author_scopus_id=("author_scopus_id", "first"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        publicaciones=("Title", "count"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        articulos_unicos=("EID", lambda x: x.replace("", pd.NA).nunique() if len(x) else 0),
        # se guarda un valor o calculo intermedio para usarlo despues.
        citas_totales=("Cited by", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        citas_promedio=("Cited by", "mean"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        anios_activos=("Year", "nunique"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        primer_anio=("Year", "min"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        ultimo_anio=("Year", "max"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        cluster_predominante=("cluster_principal", moda_segura),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_ia_total=("score_ia", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_social_total=("score_social", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_academico_total=("score_academico", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_creativo_total=("score_creativo", "sum"),
    # se cierra la lista, diccionario o llamada que se abrio antes.
    )
    # se reinicia el indice para dejar la tabla en formato normal.
    .reset_index()
# se cierra la lista, diccionario o llamada que se abrio antes.
)

# MEJORA:
# "Quienes hablan mas del tema" lo aterrizamos en una metrica interpretable:
# autores con mas publicaciones del corpus IA + educacion y con mas intensidad
# acumulada de terminos relevantes.
# `frecuencia_relativa` muestra el peso del autor dentro del corpus filtrado.
# `impacto_por_articulo` resume su citacion promedio.
# `habla_mas_del_tema` combina presencia y densidad tematica.
# se guarda un valor o calculo intermedio para usarlo despues.
resumen_autores["frecuencia_relativa"] = resumen_autores["publicaciones"] / len(df)
# se guarda un valor o calculo intermedio para usarlo despues.
resumen_autores["impacto_por_articulo"] = (
    # se realiza un paso especifico dentro del flujo del analisis.
    resumen_autores["citas_totales"] / resumen_autores["publicaciones"]
# se ejecuta una funcion o metodo para procesar los datos.
).round(2)
# se guarda un valor o calculo intermedio para usarlo despues.
resumen_autores["habla_mas_del_tema"] = (
    # se realiza un paso especifico dentro del flujo del analisis.
    resumen_autores["publicaciones"] * 0.6 + resumen_autores["score_ia_total"] * 0.4
# se ejecuta una funcion o metodo para procesar los datos.
).round(2)

# Para lectura mas facil, calculamos el cluster con mayor puntaje por autor.
# se inicia una lista de valores para usarla en el analisis.
resumen_autores["tema_mas_representado"] = resumen_autores[
    # se realiza un paso especifico dentro del flujo del analisis.
    ["score_social_total", "score_academico_total", "score_creativo_total"]
# se usan funciones de texto para limpiar o buscar informacion en columnas.
].idxmax(axis=1).str.replace("_total", "", regex=False).str.replace("score_", "", regex=False)

# se ordenan los datos para mostrar primero los resultados mas importantes.
resumen_autores = resumen_autores.sort_values(
    # se realiza un paso especifico dentro del flujo del analisis.
    ["habla_mas_del_tema", "citas_totales", "publicaciones"],
    # se guarda un valor o calculo intermedio para usarlo despues.
    ascending=[False, False, False],
# se cierra la lista, diccionario o llamada que se abrio antes.
)


# =========================================
# 9. FRECUENCIA DE AUTORES
# =========================================
# Estas dos tablas responden preguntas diferentes:
# - frecuencia_autores_anual: en que anos aparece mas cada autor
# - frecuencia_autores_cluster: en que cluster participa mas cada autor
# se guarda un valor o calculo intermedio para usarlo despues.
frecuencia_autores_anual = (
    # se agrupan los datos para calcular metricas por categoria.
    df_autores.groupby(["Year", "author_key", "author_name_canonical"])
    # se ejecuta una funcion o metodo para procesar los datos.
    .size()
    # se reinicia el indice para dejar la tabla en formato normal.
    .reset_index(name="frecuencia")
    # se ordenan los datos para mostrar primero los resultados mas importantes.
    .sort_values(["Year", "frecuencia"], ascending=[True, False])
# se cierra la lista, diccionario o llamada que se abrio antes.
)

# se guarda un valor o calculo intermedio para usarlo despues.
frecuencia_autores_cluster = (
    # se agrupan los datos para calcular metricas por categoria.
    df_autores.groupby(["cluster_principal", "author_key", "author_name_canonical"])
    # se ejecuta una funcion o metodo para procesar los datos.
    .size()
    # se reinicia el indice para dejar la tabla en formato normal.
    .reset_index(name="frecuencia")
    # se ordenan los datos para mostrar primero los resultados mas importantes.
    .sort_values(["cluster_principal", "frecuencia"], ascending=[True, False])
# se cierra la lista, diccionario o llamada que se abrio antes.
)


# =========================================
# 10. AUTORES MAS CITADOS Y MAS PRODUCTIVOS
# =========================================
# se ordenan los datos para mostrar primero los resultados mas importantes.
autores_mas_citados = resumen_autores.sort_values(
    # se realiza un paso especifico dentro del flujo del analisis.
    ["citas_totales", "impacto_por_articulo", "publicaciones"],
    # se guarda un valor o calculo intermedio para usarlo despues.
    ascending=[False, False, False],
# se cierra la lista, diccionario o llamada que se abrio antes.
)

# se ordenan los datos para mostrar primero los resultados mas importantes.
autores_mas_productivos = resumen_autores.sort_values(
    # se realiza un paso especifico dentro del flujo del analisis.
    ["publicaciones", "citas_totales"],
    # se guarda un valor o calculo intermedio para usarlo despues.
    ascending=[False, False],
# se cierra la lista, diccionario o llamada que se abrio antes.
)


# =========================================
# 11. RESUMEN DE CLUSTERS
# =========================================
# Este bloque resume el peso de cada cluster dentro del corpus y prepara
# tablas auxiliares para interpretacion lexical y redaccion de resultados.
# se guarda un valor o calculo intermedio para usarlo despues.
resumen_clusters = (
    # se agrupan los datos para calcular metricas por categoria.
    df.groupby("cluster_principal")
    # se calculan resumenes como conteos, promedios o sumas.
    .agg(
        # se guarda un valor o calculo intermedio para usarlo despues.
        articulos=("Title", "count"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        citas_totales=("Cited by", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        citas_promedio=("Cited by", "mean"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_ia_total=("score_ia", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_social_total=("score_social", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_academico_total=("score_academico", "sum"),
        # se guarda un valor o calculo intermedio para usarlo despues.
        score_creativo_total=("score_creativo", "sum"),
    # se cierra la lista, diccionario o llamada que se abrio antes.
    )
    # se reinicia el indice para dejar la tabla en formato normal.
    .reset_index()
    # se ordenan los datos para mostrar primero los resultados mas importantes.
    .sort_values("articulos", ascending=False)
# se cierra la lista, diccionario o llamada que se abrio antes.
)

# se guarda un valor o calculo intermedio para usarlo despues.
tfidf_clusters = top_palabras_por_cluster(df)
# se guarda un valor o calculo intermedio para usarlo despues.
frecuencia_palabras_clusters = frecuencia_real_por_cluster(df)
# se guarda un valor o calculo intermedio para usarlo despues.
terminos_frecuentes_clusters = top_terminos_por_cluster(df, top_n=25)
# se guarda un valor o calculo intermedio para usarlo despues.
expresiones_relevantes_clusters = medir_expresiones_relevantes(df, EXPRESIONES_RELEVANTES)
# se guarda un valor o calculo intermedio para usarlo despues.
terminos_limpios_otro = top_frases_y_terminos_cluster_otro(df, top_n=15)

# Esta tabla esta pensada para escribir resultados en lenguaje academico:
# porcentaje global + frecuencia relativa por cluster para expresiones clave.
# se guarda un valor o calculo intermedio para usarlo despues.
redaccion_expresiones_clusters = medir_expresiones_para_redaccion(
    # se realiza un paso especifico dentro del flujo del analisis.
    df,
    # se realiza un paso especifico dentro del flujo del analisis.
    EXPRESIONES_COMPUESTAS_PRIORITARIAS + ["chatgpt", "facebook", "meta", "design", "learning", "creative"],
    # se realiza un paso especifico dentro del flujo del analisis.
    ["social", "academico", "creativo"],
# se cierra la lista, diccionario o llamada que se abrio antes.
)


# =========================================
# 12. EXPORTACION DE RESULTADOS
# =========================================
# MEJORA:
# En lugar de guardar un solo CSV final, exportamos salidas tematicas que
# responden directamente a tus preguntas de investigacion.
# La idea es que no tengas que recalcular todo cada vez que quieras revisar
# autores, clusters o expresiones. Cada CSV responde una pregunta concreta.
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
df.to_csv(OUTPUT_DIR / "dataset_limpio_enriquecido.csv", index=False)
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
df_autores.to_csv(OUTPUT_DIR / "tabla_autor_articulo.csv", index=False)
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
resumen_autores.to_csv(OUTPUT_DIR / "resumen_autores.csv", index=False)
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
frecuencia_autores_anual.to_csv(OUTPUT_DIR / "frecuencia_autores_anual.csv", index=False)
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
frecuencia_autores_cluster.to_csv(OUTPUT_DIR / "frecuencia_autores_cluster.csv", index=False)
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
autores_mas_citados.to_csv(OUTPUT_DIR / "autores_mas_citados.csv", index=False)
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
autores_mas_productivos.to_csv(OUTPUT_DIR / "autores_mas_productivos.csv", index=False)
# se guarda esta tabla como archivo CSV en la carpeta de resultados.
resumen_clusters.to_csv(OUTPUT_DIR / "resumen_clusters.csv", index=False)

# se revisa una condicion antes de continuar con este bloque.
if not tfidf_clusters.empty:
    # se guarda esta tabla como archivo CSV en la carpeta de resultados.
    tfidf_clusters.to_csv(OUTPUT_DIR / "tfidf_por_cluster.csv")

# se revisa una condicion antes de continuar con este bloque.
if not frecuencia_palabras_clusters.empty:
    # se guarda esta tabla como archivo CSV en la carpeta de resultados.
    frecuencia_palabras_clusters.to_csv(OUTPUT_DIR / "frecuencia_palabras_por_cluster.csv")

# se revisa una condicion antes de continuar con este bloque.
if not terminos_frecuentes_clusters.empty:
    # se guarda esta tabla como archivo CSV en la carpeta de resultados.
    terminos_frecuentes_clusters.to_csv(OUTPUT_DIR / "terminos_frecuentes_por_cluster.csv", index=False)

# se revisa una condicion antes de continuar con este bloque.
if not expresiones_relevantes_clusters.empty:
    # se guarda esta tabla como archivo CSV en la carpeta de resultados.
    expresiones_relevantes_clusters.to_csv(OUTPUT_DIR / "expresiones_relevantes_por_cluster.csv", index=False)

# se revisa una condicion antes de continuar con este bloque.
if not terminos_limpios_otro.empty:
    # se guarda esta tabla como archivo CSV en la carpeta de resultados.
    terminos_limpios_otro.to_csv(OUTPUT_DIR / "terminos_limpios_cluster_otro.csv", index=False)

# se revisa una condicion antes de continuar con este bloque.
if not redaccion_expresiones_clusters.empty:
    # se guarda esta tabla como archivo CSV en la carpeta de resultados.
    redaccion_expresiones_clusters.to_csv(OUTPUT_DIR / "redaccion_expresiones_clusters.csv", index=False)

# se guarda un valor o calculo intermedio para usarlo despues.
reporte_clusters_lineas = []
# Armamos un reporte de texto rapido para lectura humana. Es util si quieres
# revisar resultados sin abrir los CSV en Excel o pandas.
# se recorren varios elementos para procesarlos uno por uno.
for cluster in ["social", "academico", "creativo", "otro", "mixto"]:
    # se ejecuta una funcion o metodo para procesar los datos.
    reporte_clusters_lineas.append(f"CLUSTER: {cluster.upper()}")

    # se revisa una condicion antes de continuar con este bloque.
    if cluster == "otro":
        # se guarda un valor o calculo intermedio para usarlo despues.
        tabla_cluster = terminos_limpios_otro.head(10)
        # se ejecuta una funcion o metodo para procesar los datos.
        reporte_clusters_lineas.append("Terminos frecuentes del cluster:")
    # se ejecuta este bloque cuando no se cumple la condicion anterior.
    else:
        # se inicia una lista de valores para usarla en el analisis.
        tabla_cluster = expresiones_relevantes_clusters[
            # se guarda un valor o calculo intermedio para usarlo despues.
            expresiones_relevantes_clusters["cluster_principal"] == cluster
        # se inicia una lista de valores para usarla en el analisis.
        ][
            # se inicia una lista de valores para usarla en el analisis.
            [
                # se agrega este termino a la lista para detectarlo en los articulos.
                "expresion",
                # se agrega este termino a la lista para detectarlo en los articulos.
                "porcentaje_articulos_cluster",
                # se agrega este termino a la lista para detectarlo en los articulos.
                "porcentaje_articulos_corpus",
            # se cierra la lista, diccionario o llamada que se abrio antes.
            ]
        # se ordenan los datos para mostrar primero los resultados mas importantes.
        ].sort_values(
            # se realiza un paso especifico dentro del flujo del analisis.
            ["porcentaje_articulos_cluster", "porcentaje_articulos_corpus"],
            # se guarda un valor o calculo intermedio para usarlo despues.
            ascending=[False, False],
        # se ejecuta una funcion o metodo para procesar los datos.
        ).head(10)
        # se ejecuta una funcion o metodo para procesar los datos.
        reporte_clusters_lineas.append("Expresiones mas representativas del cluster:")

    # se revisa una condicion antes de continuar con este bloque.
    if tabla_cluster.empty:
        # se ejecuta una funcion o metodo para procesar los datos.
        reporte_clusters_lineas.append("Sin datos disponibles.")
    # se ejecuta este bloque cuando no se cumple la condicion anterior.
    else:
        # se guarda un valor o calculo intermedio para usarlo despues.
        reporte_clusters_lineas.append(tabla_cluster.to_string(index=False))

    # se ejecuta una funcion o metodo para procesar los datos.
    reporte_clusters_lineas.append("")

# se trabaja con rutas de archivos o carpetas.
(OUTPUT_DIR / "reporte_clusters.txt").write_text("\n".join(reporte_clusters_lineas), encoding="utf-8")


# =========================================
# 13. REPORTE RAPIDO EN CONSOLA
# =========================================
# Este bloque solo imprime un resumen ejecutivo. No cambia los datos, solo te
# deja ver rapidamente si el analisis salio razonable.
# se muestra informacion en pantalla para revisar el avance o los resultados.
print("\nArticulos por anio:")
# se muestra informacion en pantalla para revisar el avance o los resultados.
print(df["Year"].value_counts().sort_index())

# se muestra informacion en pantalla para revisar el avance o los resultados.
print("\nResumen de clusters:")
# se muestra informacion en pantalla para revisar el avance o los resultados.
print(resumen_clusters)

# se muestra informacion en pantalla para revisar el avance o los resultados.
print("\nAutores mas productivos:")
# se muestra informacion en pantalla para revisar el avance o los resultados.
print(autores_mas_productivos[["author_name", "publicaciones", "citas_totales", "tema_mas_representado"]].head(10))

# se muestra informacion en pantalla para revisar el avance o los resultados.
print("\nAutores mas citados:")
# se muestra informacion en pantalla para revisar el avance o los resultados.
print(autores_mas_citados[["author_name", "citas_totales", "impacto_por_articulo", "publicaciones"]].head(10))

# se muestra informacion en pantalla para revisar el avance o los resultados.
print("\nAutores que mas hablan del tema:")
# se muestra informacion en pantalla para revisar el avance o los resultados.
print(resumen_autores[["author_name", "habla_mas_del_tema", "publicaciones", "score_ia_total"]].head(10))

# se recorren varios elementos para procesarlos uno por uno.
for cluster in ["social", "academico", "creativo", "otro"]:
    # se revisa una condicion antes de continuar con este bloque.
    if cluster == "otro":
        # se muestra informacion en pantalla para revisar el avance o los resultados.
        print(f"\nTerminos frecuentes en cluster {cluster}:")
        # se muestra informacion en pantalla para revisar el avance o los resultados.
        print(terminos_limpios_otro.head(10))
    # se ejecuta este bloque cuando no se cumple la condicion anterior.
    else:
        # se muestra informacion en pantalla para revisar el avance o los resultados.
        print(f"\nExpresiones relevantes en cluster {cluster}:")
        # se muestra informacion en pantalla para revisar el avance o los resultados.
        print(
            # se inicia una lista de valores para usarla en el analisis.
            expresiones_relevantes_clusters[
                # se guarda un valor o calculo intermedio para usarlo despues.
                expresiones_relevantes_clusters["cluster_principal"] == cluster
            # se inicia una lista de valores para usarla en el analisis.
            ][
                # se inicia una lista de valores para usarla en el analisis.
                [
                    # se agrega este termino a la lista para detectarlo en los articulos.
                    "expresion",
                    # se agrega este termino a la lista para detectarlo en los articulos.
                    "porcentaje_articulos_cluster",
                    # se agrega este termino a la lista para detectarlo en los articulos.
                    "porcentaje_articulos_corpus",
                # se cierra la lista, diccionario o llamada que se abrio antes.
                ]
            # se ordenan los datos para mostrar primero los resultados mas importantes.
            ].sort_values(
                # se realiza un paso especifico dentro del flujo del analisis.
                ["porcentaje_articulos_cluster", "porcentaje_articulos_corpus"],
                # se guarda un valor o calculo intermedio para usarlo despues.
                ascending=[False, False],
            # se ejecuta una funcion o metodo para procesar los datos.
            ).head(10)
        # se cierra la lista, diccionario o llamada que se abrio antes.
        )

# se revisa una condicion antes de continuar con este bloque.
if not redaccion_expresiones_clusters.empty:
    # se muestra informacion en pantalla para revisar el avance o los resultados.
    print("\nExpresiones compuestas listas para redaccion academica:")
    # se recorren varios elementos para procesarlos uno por uno.
    for cluster in ["social", "academico", "creativo"]:
        # se muestra informacion en pantalla para revisar el avance o los resultados.
        print(f"\nCluster {cluster}:")
        # se muestra informacion en pantalla para revisar el avance o los resultados.
        print(
            # se inicia una lista de valores para usarla en el analisis.
            redaccion_expresiones_clusters[
                # se guarda un valor o calculo intermedio para usarlo despues.
                redaccion_expresiones_clusters["cluster_principal"] == cluster
            # se ordenan los datos para mostrar primero los resultados mas importantes.
            ].sort_values(
                # se realiza un paso especifico dentro del flujo del analisis.
                ["porcentaje_en_cluster", "porcentaje_global", "promedio_por_articulo"],
                # se guarda un valor o calculo intermedio para usarlo despues.
                ascending=[False, False, False],
            # se ejecuta una funcion o metodo para procesar los datos.
            ).head(10)
        # se cierra la lista, diccionario o llamada que se abrio antes.
        )

# se muestra informacion en pantalla para revisar el avance o los resultados.
print(f"\nProceso terminado. Archivos guardados en: {OUTPUT_DIR}")
