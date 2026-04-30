# Analisis_de_datos_3384

Este repositorio contiene un proceso de limpieza, normalización y estructuración de datos bibliométricos obtenidos de Scopus, enfocado en el análisis del uso de la inteligencia artificial en estudiantes universitarios.

Limpieza de datos

Se implementa un proceso de normalización textual (donde se depuro el texto) que incluye:
Normalizando el texto, en este caso los titulos, los autores y el resumen (todo en minusculas)

Conversión de texto a minúsculas para evitar duplicidades por diferencias de formato
Eliminación de espacios redundantes (inicio, final y múltiples espacios internos)
Sustitución de valores nulos por cadenas vacías
Depuración de caracteres no relevantes para mejorar el análisis semántico

Autores limpios

El tratamiento de autores se realiza en varias etapas:

Tokenización estructural: separación de autores a partir del delimitador ;
Limpieza individual: eliminación de espacios innecesarios, acentos o puntos en cada nombre (de dos a mas espacios, por ejemplo: "Juan______Matias." o "_________Juan _____Mátias " paso ha ser: "Juan Matias"
Identificador a partir del oricid:
Dado que no todos los registros contienen identificadores únicos (ORCID), se aplica una estrategia de normalización basada en similitud textual para:

Detectar autores con nombres equivalentes
Agrupar variantes de un mismo autor
Mejorar la precisión en el conteo de productividad científica

Objetivo de esta limpieza de datos:
-Estandarización de los nombres para conteo de autores por articulo de investigación (cuantas veces aparece un autor en diferentes articulos, por ende es el autor con mas presencia en el corpus o en los datos).
Reducir el ruido semantico como son los signos de puntuación, admiración o de interrogación



La versión 2.0
El código de analisis_datos_scopus_mejorado realiza procesos de limpieza y normalización de datos textuales, depuración de duplicados, desambiguación básica de autores y construcción de métricas bibliométricas relacionadas con productividad, citación y frecuencia de aparición.

Asimismo, el codigo en paython clasifica los artículos en clusters temáticos que son: social, academico, creativo y otro, a partir de la detección de términos y expresiones compuestas relevantes dentro del corpus. Como parte del análisis, se calculan indicadores como porcentaje de presencia por cluster, porcentaje global en el corpus y promedio de menciones por artículo. 
