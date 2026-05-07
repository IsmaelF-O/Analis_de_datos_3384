from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parent
ARCHIVO = BASE_DIR / "analisis_datos_scopus_mejorado.py"
RESPALDO = BASE_DIR / "analisis_datos_scopus_mejorado_sin_comentarios_backup.py"


def describir_linea(linea):
    texto = linea.strip()

    if texto == "from pathlib import Path":
        return "se importa Path para trabajar con rutas de archivos y carpetas."
    if texto == "import re":
        return "se importa re para buscar y limpiar patrones de texto con expresiones regulares."
    if texto == "import unicodedata":
        return "se importa unicodedata para normalizar acentos y caracteres especiales."
    if texto == "from difflib import SequenceMatcher":
        return "se importa SequenceMatcher para comparar nombres de autores y detectar similitudes."
    if texto == "from collections import Counter":
        return "se importa Counter para contar palabras, terminos y frecuencias."
    if texto == "from math import log":
        return "se importa log para calcular puntajes tipo TF-IDF."
    if texto == "import pandas as pd":
        return "se importa la libreria pandas para analisis de datos en tablas y archivos CSV."
    if texto.startswith("from ") and " import " in texto:
        return "se importa una herramienta especifica que se utilizara en el analisis."
    if texto.startswith("import "):
        return "se importa una libreria necesaria para procesar los datos."
    if texto == "BASE_DIR = Path(__file__).resolve().parent":
        return "se obtiene la carpeta donde esta guardado este script."
    if texto.startswith("INPUT_FILE ="):
        return "se define la ruta del archivo CSV de Scopus que se va a analizar."
    if texto == 'OUTPUT_DIR = BASE_DIR / "salidas_scopus"':
        return "se define la carpeta donde se guardaran los archivos generados."
    if texto == "OUTPUT_DIR.mkdir(exist_ok=True)":
        return "se crea la carpeta de salidas si todavia no existe."
    if re.match(r"^[A-Z_][A-Z0-9_]*\s*=", texto):
        return "se define una variable fija que controla una parte del analisis."
    if texto.startswith("def "):
        nombre = texto.split("(", 1)[0].replace("def ", "").strip()
        return f"se crea la funcion {nombre} para reutilizar esta parte del proceso."
    if texto == "return" or texto.startswith("return "):
        return "se devuelve el resultado calculado por la funcion."
    if texto.startswith("if __name__"):
        return "se comprueba si este archivo se ejecuto directamente."
    if texto.startswith("if "):
        return "se revisa una condicion antes de continuar con este bloque."
    if texto.startswith("elif "):
        return "se revisa otra condicion cuando la anterior no se cumplio."
    if texto == "else:" or texto.startswith("else:"):
        return "se ejecuta este bloque cuando no se cumple la condicion anterior."
    if texto.startswith("for "):
        return "se recorren varios elementos para procesarlos uno por uno."
    if texto.startswith("while "):
        return "se repite el bloque mientras la condicion sea verdadera."
    if texto.startswith("try:"):
        return "se intenta ejecutar un bloque que podria generar un error."
    if texto.startswith("except "):
        return "se controla el error para que el programa no falle sin explicacion."
    if texto.startswith("raise "):
        return "se detiene el programa y se muestra un mensaje de error."
    if texto.startswith("with "):
        return "se abre un recurso temporal y se cierra automaticamente al terminar."
    if texto.startswith("print("):
        return "se muestra informacion en pantalla para revisar el avance o los resultados."
    if ".to_csv(" in texto:
        return "se guarda esta tabla como archivo CSV en la carpeta de resultados."
    if ".read_csv(" in texto or texto.startswith("pd.read_csv("):
        return "se lee el CSV de Scopus y se convierte en una tabla de pandas."
    if ".groupby(" in texto:
        return "se agrupan los datos para calcular metricas por categoria."
    if ".agg(" in texto:
        return "se calculan resumenes como conteos, promedios o sumas."
    if ".sort_values(" in texto:
        return "se ordenan los datos para mostrar primero los resultados mas importantes."
    if ".reset_index(" in texto:
        return "se reinicia el indice para dejar la tabla en formato normal."
    if ".apply(" in texto:
        return "se aplica una funcion a cada dato o fila de la tabla."
    if ".fillna(" in texto:
        return "se rellenan valores vacios para evitar errores durante el analisis."
    if ".astype(" in texto:
        return "se convierte la columna al tipo de dato necesario."
    if ".drop_duplicates(" in texto:
        return "se eliminan registros duplicados para no contarlos dos veces."
    if ".dropna(" in texto:
        return "se eliminan filas que no tienen datos indispensables."
    if ".str." in texto:
        return "se usan funciones de texto para limpiar o buscar informacion en columnas."
    if texto.startswith("re."):
        return "se usan expresiones regulares para limpiar o detectar texto."
    if texto.startswith("pd."):
        return "se usa pandas para crear o transformar tablas de datos."
    if "Counter(" in texto:
        return "se cuentan apariciones para obtener frecuencias."
    if "SequenceMatcher(" in texto:
        return "se comparan textos para medir que tan parecidos son."
    if "Path(" in texto or "OUTPUT_DIR" in texto:
        return "se trabaja con rutas de archivos o carpetas."
    if texto.endswith("["):
        return "se inicia una lista de valores para usarla en el analisis."
    if texto.endswith("{"):
        return "se inicia un diccionario para organizar informacion por categorias."
    if texto in {"]", "},", "}", ")", "),"}:
        return "se cierra la lista, diccionario o llamada que se abrio antes."
    if re.match(r"^[\"'].*[\"'],?$", texto):
        return "se agrega este termino a la lista para detectarlo en los articulos."
    if re.match(r"^[\"'][^\"']+[\"']\s*:", texto):
        return "se define una categoria del diccionario y sus terminos asociados."
    if "=" in texto:
        return "se guarda un valor o calculo intermedio para usarlo despues."
    if texto.endswith(")") or texto.endswith("),"):
        return "se ejecuta una funcion o metodo para procesar los datos."
    return "se realiza un paso especifico dentro del flujo del analisis."


def ya_esta_comentado(lineas):
    return any("# Explicacion:" in linea for linea in lineas[:80])


def comentar_archivo():
    origen = RESPALDO if RESPALDO.exists() else ARCHIVO
    contenido = origen.read_text(encoding="utf-8")
    lineas = contenido.splitlines()

    if origen == ARCHIVO and not RESPALDO.exists():
        RESPALDO.write_text(contenido, encoding="utf-8")

    nuevas_lineas = []
    dentro_triple = False
    token_triple = None
    comentarios_agregados = 0

    for linea in lineas:
        texto = linea.strip()

        if dentro_triple:
            nuevas_lineas.append(linea)
            if token_triple in texto and texto.count(token_triple) % 2 == 1:
                dentro_triple = False
                token_triple = None
            continue

        if texto == "" or texto.startswith("#"):
            nuevas_lineas.append(linea)
            continue

        indentacion = linea[: len(linea) - len(linea.lstrip())]
        nuevas_lineas.append(f"{indentacion}# {describir_linea(linea)}")
        nuevas_lineas.append(linea)
        comentarios_agregados += 1

        if '"""' in texto or "'''" in texto:
            token = '"""' if '"""' in texto else "'''"
            if texto.count(token) % 2 == 1:
                dentro_triple = True
                token_triple = token

    ARCHIVO.write_text("\n".join(nuevas_lineas) + "\n", encoding="utf-8")
    print(f"Comentarios agregados: {comentarios_agregados}")
    print(f"Respaldo creado: {RESPALDO}")


if __name__ == "__main__":
    comentar_archivo()
