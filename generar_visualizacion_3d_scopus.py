from __future__ import annotations

from ast import literal_eval
from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import random
import re

import pandas as pd


BASE_DIR = Path(r"C:\Users\Brayan Flores\OneDrive\Documentos\New project")
DATASET_PATH = BASE_DIR / "salidas_scopus" / "dataset_limpio_enriquecido.csv"
OUTPUT_HTML = BASE_DIR / "salidas_scopus" / "visualizacion_clusters_3d.html"


CLUSTER_CONFIG = {
    "social": {"center": (-360, -20, 120), "color": "#4ea8de"},
    "academico": {"center": (0, 190, -40), "color": "#7b6dff"},
    "creativo": {"center": (330, -10, 90), "color": "#ff7ca8"},
    "otro": {"center": (0, -280, -120), "color": "#f1c453"},
    "mixto": {"center": (0, 0, 260), "color": "#5fd2a2"},
}

CLUSTER_TERMS = {
    "social": [
        "communication", "interaction", "community", "social", "collaboration",
        "peer", "network", "engagement", "discussion", "relationship", "trust",
        "ethics", "social media", "human ai interaction", "perceptions",
        "digital literacy", "social networking", "technological acceptance",
    ],
    "academico": [
        "learning", "teaching", "classroom", "assignment", "assessment", "exam",
        "course", "curriculum", "pedagog", "feedback", "study", "performance",
        "academic integrity", "educational technology", "academic writing",
        "higher education", "adaptive learning", "adaptative learning",
        "self learning", "pedagogical strategies", "plagiarism detection",
    ],
    "creativo": [
        "creative", "creativity", "design", "content creation", "writing",
        "storytelling", "brainstorm", "art", "image generation", "multimedia",
        "innovation", "co-creation", "generative design", "creative writing",
        "digital creativity", "ai generated content", "multimedia production",
        "creative process", "creative proccess", "prompt engineering",
        "collaborative creativity",
    ],
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "using",
    "use", "used", "are", "was", "were", "have", "has", "had", "higher",
    "education", "students", "student", "university", "artificial",
    "intelligence", "study", "based", "analysis", "approach", "toward",
    "towards", "through", "their", "these", "those", "such", "learning",
}


def terminos_detectados(texto: str, terminos: list[str], limite: int = 8) -> list[str]:
    texto = f" {texto_limpio(texto).lower()} "
    encontrados = []
    for termino in terminos:
        patron = r"\b" + re.escape(termino.lower()).replace(r"\ ", r"\s+") + r"\b"
        if re.search(patron, texto):
            encontrados.append(termino)
    return encontrados[:limite]


def explicar_cluster(row: pd.Series, cluster: str, terms_detected: list[str]) -> str:
    scores = {
        "social": int(row.get("score_social", 0)),
        "academico": int(row.get("score_academico", 0)),
        "creativo": int(row.get("score_creativo", 0)),
    }
    if cluster == "mixto":
        ganadores = [nombre for nombre, score in scores.items() if score > 0]
        return (
            "Pertenece al cluster mixto porque combina evidencia de varios ejes: "
            + ", ".join(f"{nombre}={scores[nombre]}" for nombre in ganadores)
            + "."
        )
    if cluster == "otro":
        return (
            "Pertenece al cluster otro porque no se detectaron suficientes terminos "
            "de los ejes social, academico o creativo."
        )
    terminos = ", ".join(terms_detected) if terms_detected else "terminos relacionados del diccionario tematico"
    return (
        f"Pertenece al cluster {cluster} porque el texto contiene {terminos}. "
        f"Puntajes: social={scores['social']}, academico={scores['academico']}, creativo={scores['creativo']}."
    )


def lista_desde_celda(valor) -> list[str]:
    if pd.isna(valor):
        return []
    if isinstance(valor, list):
        return [str(x).strip() for x in valor if str(x).strip()]
    texto = str(valor).strip()
    if not texto or texto.lower() == "nan":
        return []
    try:
        convertido = literal_eval(texto)
        if isinstance(convertido, list):
            return [str(x).strip() for x in convertido if str(x).strip()]
    except Exception:
        pass
    return [x.strip() for x in texto.split(";") if x.strip()]


def texto_limpio(valor) -> str:
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    return "" if texto.lower() == "nan" else texto


def resumen_corto(texto: str, max_len: int = 280) -> str:
    texto = texto_limpio(texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    if not texto:
        return "No disponible"
    if len(texto) <= max_len:
        return texto
    return texto[:max_len].rsplit(" ", 1)[0] + "..."


def top_terms_from_text(row: pd.Series, n: int = 6) -> list[str]:
    keywords = texto_limpio(row.get("Author Keywords", ""))
    if keywords:
        terms = [k.strip() for k in keywords.split(";") if k.strip()]
        if terms:
            return terms[:n]

    text = f"{texto_limpio(row.get('title_clean', ''))} {texto_limpio(row.get('keywords_clean', ''))}"
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
    tokens = [t for t in tokens if t not in STOPWORDS]
    return [word for word, _ in Counter(tokens).most_common(n)]


def contar_frase_en_texto(texto: str, termino: str) -> int:
    texto = texto_limpio(texto).lower()
    termino = texto_limpio(termino).lower()
    if not texto or not termino:
        return 0
    patron = r"\b" + re.escape(termino).replace(r"\ ", r"\s+") + r"\b"
    return len(re.findall(patron, texto))


def calcular_presencia_cluster(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    presencia: dict[str, dict[str, float]] = {}
    for cluster, subset in df.groupby("cluster_principal"):
        textos = [texto_limpio(texto).lower() for texto in subset["texto_total"].fillna("").astype(str).tolist()]
        token_sets = [set(re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", texto)) for texto in textos]
        total = len(textos) or 1
        candidatos = set()
        for _, row in subset.iterrows():
            candidatos.update(top_terms_from_text(row, n=8))
            for terminos in CLUSTER_TERMS.values():
                candidatos.update(terminos_detectados(row.get("texto_total", ""), terminos, limite=20))
        presencia[str(cluster)] = {}
        for termino in candidatos:
            termino_norm = termino.lower()
            if " " in termino_norm:
                docs_con_termino = sum(1 for texto in textos if termino_norm in texto)
            else:
                docs_con_termino = sum(1 for tokens in token_sets if termino_norm in tokens)
            presencia[str(cluster)][termino.lower()] = round((docs_con_termino / total) * 100, 1)
    return presencia


def terminos_destacados_articulo(row: pd.Series, cluster: str, cluster_terms: list[str], presencia_cluster: dict) -> list[dict]:
    texto = texto_limpio(row.get("texto_total", ""))
    candidatos = list(dict.fromkeys(cluster_terms + top_terms_from_text(row, n=8)))
    destacados = []
    for termino in candidatos:
        frecuencia = contar_frase_en_texto(texto, termino)
        if frecuencia <= 0:
            continue
        destacados.append(
            {
                "term": termino,
                "article_frequency": frecuencia,
                "cluster_presence": presencia_cluster.get(cluster, {}).get(termino.lower(), 0),
                "classification_term": termino in cluster_terms,
            }
        )
    destacados.sort(
        key=lambda item: (
            item["classification_term"],
            item["article_frequency"],
            item["cluster_presence"],
        ),
        reverse=True,
    )
    return destacados[:8]


def calcular_autores_destacados_por_cluster(df: pd.DataFrame) -> dict[str, list[dict]]:
    acumulado: dict[str, dict[str, dict]] = defaultdict(dict)
    for _, row in df.iterrows():
        cluster = str(row.get("cluster_principal", "otro"))
        citas = int(row.get("Cited by", 0)) if pd.notna(row.get("Cited by")) else 0
        for autor in lista_desde_celda(row.get("authors_canonical", [])):
            if not autor:
                continue
            dato = acumulado[cluster].setdefault(
                autor,
                {"author": autor, "publications": 0, "citations": 0},
            )
            dato["publications"] += 1
            dato["citations"] += citas

    salida = {}
    for cluster, autores in acumulado.items():
        ordenados = sorted(
            autores.values(),
            key=lambda item: (item["publications"], item["citations"]),
            reverse=True,
        )
        salida[cluster] = ordenados[:6]
    return salida


def build_nodes(df: pd.DataFrame) -> tuple[list[dict], dict]:
    rng = random.Random(44)
    cluster_stats = {}
    nodes = []
    counts = df["cluster_principal"].value_counts().to_dict()
    presencia_cluster = calcular_presencia_cluster(df)
    autores_destacados_cluster = calcular_autores_destacados_por_cluster(df)

    for cluster, count in counts.items():
        subset = df[df["cluster_principal"] == cluster]
        cluster_stats[cluster] = {
            "articles": int(count),
            "avg_citations": round(float(subset["Cited by"].mean()), 2) if not subset.empty else 0,
            "top_authors": autores_destacados_cluster.get(cluster, []),
        }

    cluster_offsets = {cluster: 0 for cluster in CLUSTER_CONFIG}

    for _, row in df.iterrows():
        cluster = str(row.get("cluster_principal", "otro"))
        config = CLUSTER_CONFIG.get(cluster, CLUSTER_CONFIG["otro"])
        cx, cy, cz = config["center"]
        idx = cluster_offsets.get(cluster, 0)
        cluster_offsets[cluster] = idx + 1

        angle = idx * 0.41
        radius = 45 + (idx % 18) * 11
        spiral = (idx // 18) * 20

        x = cx + math.cos(angle) * radius + rng.uniform(-18, 18)
        y = cy + math.sin(angle) * radius + rng.uniform(-18, 18)
        z = cz + spiral + rng.uniform(-22, 22)

        autores = lista_desde_celda(row.get("authors_canonical", []))
        keywords = [k.strip() for k in texto_limpio(row.get("Author Keywords", "")).split(";") if k.strip()][:8]
        terms = top_terms_from_text(row)
        doi = texto_limpio(row.get("DOI", "")) or "No disponible"
        texto_total = texto_limpio(row.get("texto_total", ""))
        detected_by_cluster = {
            nombre: terminos_detectados(texto_total, terminos)
            for nombre, terminos in CLUSTER_TERMS.items()
        }
        cluster_terms = detected_by_cluster.get(cluster, [])
        if cluster == "mixto":
            cluster_terms = sorted({term for terms_list in detected_by_cluster.values() for term in terms_list})[:10]
        cluster_reason = explicar_cluster(row, cluster, cluster_terms)
        highlight_terms = terminos_destacados_articulo(row, cluster, cluster_terms, presencia_cluster)

        nodes.append(
            {
                "id": len(nodes),
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
                "cluster": cluster,
                "color": config["color"],
                "size": max(4, min(14, 4 + int(row.get("Cited by", 0)) // 10)),
                "title": texto_limpio(row.get("Title", "Sin titulo")) or "Sin titulo",
                "year": int(row["Year"]) if pd.notna(row.get("Year")) else None,
                "citations": int(row.get("Cited by", 0)) if pd.notna(row.get("Cited by")) else 0,
                "authors": autores[:4],
                "all_authors": autores,
                "keywords": keywords,
                "important_terms": terms,
                "cluster_terms": cluster_terms,
                "highlight_terms": highlight_terms,
                "detected_by_cluster": detected_by_cluster,
                "cluster_reason": cluster_reason,
                "cluster_top_authors": autores_destacados_cluster.get(cluster, []),
                "abstract_short": resumen_corto(texto_limpio(row.get("Abstract", ""))),
                "doi": doi,
                "link": texto_limpio(row.get("Link", "")) or "No disponible",
                "source_title": texto_limpio(row.get("Source title", "")),
                "score_ia": int(row.get("score_ia", 0)),
                "score_poblacion": int(row.get("score_poblacion", 0)),
                "score_social": int(row.get("score_social", 0)),
                "score_academico": int(row.get("score_academico", 0)),
                "score_creativo": int(row.get("score_creativo", 0)),
            }
        )

    return nodes, cluster_stats


def build_edges(nodes: list[dict]) -> list[dict]:
    cluster_groups: dict[str, list[int]] = defaultdict(list)
    author_groups: dict[str, list[int]] = defaultdict(list)
    keyword_groups: dict[str, list[int]] = defaultdict(list)
    edges: dict[tuple[int, int], dict] = {}

    for node in nodes:
        cluster_groups[node["cluster"]].append(node["id"])
        for author in node["authors"]:
            author_groups[author].append(node["id"])
        for keyword in node["keywords"][:4]:
            keyword_groups[keyword.lower()].append(node["id"])

    def add_edge(a: int, b: int, relation: str, weight: float) -> None:
        if a == b:
            return
        key = tuple(sorted((a, b)))
        existing = edges.get(key)
        if existing is None or weight > existing["weight"]:
            edges[key] = {"source": key[0], "target": key[1], "relation": relation, "weight": weight}

    for cluster, ids in cluster_groups.items():
        ids = ids[:220]
        for i in range(len(ids) - 1):
            add_edge(ids[i], ids[i + 1], f"cluster:{cluster}", 0.3)
        for i in range(0, len(ids), 12):
            if i + 6 < len(ids):
                add_edge(ids[i], ids[i + 6], f"cluster:{cluster}", 0.2)

    for ids in author_groups.values():
        if len(ids) < 2:
            continue
        ids = ids[:12]
        for i in range(len(ids) - 1):
            add_edge(ids[i], ids[i + 1], "autor", 0.95)

    for ids in keyword_groups.values():
        if len(ids) < 2:
            continue
        ids = ids[:10]
        for i in range(len(ids) - 1):
            add_edge(ids[i], ids[i + 1], "keyword", 0.65)

    return list(edges.values())


def build_html(nodes: list[dict], cluster_stats: dict, edges: list[dict]) -> str:
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    stats_json = json.dumps(cluster_stats, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    total_nodes = len(nodes)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mapa 3D Bibliométrico</title>
  <style>
    :root {{
      --bg: #0b1018;
      --panel: rgba(14, 19, 30, 0.92);
      --line: rgba(120, 138, 163, 0.18);
      --text: #eef4fb;
      --muted: #9cb0c7;
      --chip: rgba(255,255,255,0.06);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--text);
      font-family: "Segoe UI", system-ui, sans-serif;
      overflow: hidden;
      background:
        radial-gradient(circle at 20% 20%, rgba(80,100,255,.20), transparent 30%),
        radial-gradient(circle at 80% 18%, rgba(0,210,255,.14), transparent 28%),
        radial-gradient(circle at 50% 80%, rgba(255,124,168,.12), transparent 30%),
        linear-gradient(180deg, #0e1420 0%, #090d14 100%);
    }}
    #app {{
      display: grid;
      grid-template-columns: 1fr 410px;
      height: 100vh;
    }}
    #left {{
      position: relative;
      overflow: hidden;
    }}
    canvas {{
      width: 100%;
      height: 100%;
      display: block;
      cursor: grab;
    }}
    #toolbar {{
      position: absolute;
      top: 18px;
      left: 18px;
      z-index: 5;
      background: rgba(13, 18, 28, 0.7);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 18px;
      padding: 14px 16px;
      width: 360px;
      max-height: calc(100vh - 36px);
      overflow-y: auto;
      backdrop-filter: blur(18px);
      box-shadow: 0 18px 46px rgba(0,0,0,.32);
    }}
    #toolbar::-webkit-scrollbar {{
      width: 7px;
    }}
    #toolbar::-webkit-scrollbar-thumb {{
      background: rgba(255,255,255,0.18);
      border-radius: 999px;
    }}
    #toolbar h1 {{
      font-size: 18px;
      margin: 0 0 8px 0;
      letter-spacing: .02em;
    }}
    #toolbar p {{
      color: var(--muted);
      font-size: 13px;
      margin: 0 0 10px 0;
      line-height: 1.5;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }}
    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      color: var(--text);
    }}
    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      box-shadow: 0 0 18px currentColor;
    }}
    .line-key {{
      margin-top: 10px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 12px;
    }}
    .controls {{
      margin-top: 12px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .controls button {{
      background: rgba(255,255,255,0.05);
      color: var(--text);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 999px;
      padding: 7px 12px;
      font-size: 12px;
      cursor: pointer;
    }}
    .controls button:hover {{
      background: rgba(255,255,255,0.10);
    }}
    .controls button.active {{
      background: rgba(142,208,255,0.18);
      border-color: rgba(142,208,255,0.42);
    }}
    .details-toggle {{
      margin-top: 10px;
      width: 100%;
      background: rgba(142,208,255,0.12);
      color: var(--text);
      border: 1px solid rgba(142,208,255,0.28);
      border-radius: 10px;
      padding: 8px 10px;
      cursor: pointer;
      font-size: 12px;
      text-align: left;
    }}
    .toolbar-details.collapsed {{
      display: none;
    }}
    .filters {{
      margin-top: 12px;
      display: grid;
      gap: 8px;
    }}
    .filters input {{
      width: 100%;
      background: rgba(255,255,255,0.06);
      color: var(--text);
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 10px;
      padding: 9px 10px;
      outline: none;
      font-size: 13px;
    }}
    .filter-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }}
    .filter-row button {{
      background: rgba(255,255,255,0.04);
      color: var(--text);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      cursor: pointer;
    }}
    .filter-row button.active {{
      background: rgba(142,208,255,0.18);
      border-color: rgba(142,208,255,0.42);
    }}
    .metrics {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 7px;
    }}
    .metric {{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 10px;
      padding: 7px 8px;
      font-size: 12px;
      color: var(--muted);
    }}
    .metric strong {{
      display: block;
      color: var(--text);
      font-size: 16px;
      line-height: 1.15;
    }}
    #tooltip {{
      position: absolute;
      z-index: 10;
      pointer-events: none;
      min-width: 180px;
      max-width: 320px;
      background: rgba(5, 8, 14, 0.92);
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 12px;
      padding: 10px 12px;
      color: var(--text);
      font-size: 12px;
      line-height: 1.45;
      display: none;
      box-shadow: 0 14px 34px rgba(0,0,0,.35);
    }}
    #panel {{
      border-left: 1px solid rgba(255,255,255,0.06);
      background: linear-gradient(180deg, rgba(16,22,35,.95), rgba(8,12,18,.97));
      padding: 22px 20px;
      overflow-y: auto;
      backdrop-filter: blur(20px);
    }}
    #panel h2 {{
      margin: 0 0 10px 0;
      font-size: 24px;
      line-height: 1.25;
    }}
    #panel h3 {{
      margin: 18px 0 8px 0;
      font-size: 13px;
      color: #dce4ee;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    #panel p, #panel li {{
      font-size: 14px;
      line-height: 1.58;
      color: var(--text);
    }}
    #panel .muted {{
      color: var(--muted);
    }}
    .badge {{
      display: inline-block;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 12px;
      margin-right: 8px;
      margin-bottom: 8px;
      border: 1px solid rgba(255,255,255,0.08);
      background: var(--chip);
    }}
    .meta {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 12px;
    }}
    .card {{
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 16px;
      padding: 12px;
    }}
    .authors-list, .terms-list {{
      padding-left: 18px;
      margin: 8px 0 0 0;
    }}
    a {{
      color: #8ed0ff;
      text-decoration: none;
    }}
    .note {{
      font-size: 12px;
      color: var(--muted);
      margin-top: 12px;
    }}
    .method-box {{
      margin-top: 12px;
      background: rgba(142,208,255,0.08);
      border: 1px solid rgba(142,208,255,0.18);
      border-radius: 12px;
      padding: 10px 12px;
      color: var(--text);
    }}
    .method-box h3 {{
      margin: 0 0 6px 0;
      font-size: 12px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .method-box p, .method-box li {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      margin: 4px 0;
    }}
    @media (max-width: 1100px) {{
      #app {{ grid-template-columns: 1fr; }}
      #panel {{
        position: absolute;
        right: 0;
        top: 0;
        width: min(430px, 92vw);
        height: 100vh;
      }}
    }}
  </style>
</head>
<body>
  <div id="app">
    <div id="left">
      <canvas id="scene"></canvas>
      <div id="toolbar">
        <h1>Mapa 3D Bibliométrico</h1>
        <p>Arrastra para rotar, usa la rueda para acercar o alejar y haz clic en una bolita para abrir la ficha del artículo. Cada color representa un cluster y cada ficha explica por qué el artículo pertenece a ese grupo.</p>
        <div class="controls">
          <button id="toggleMotion">Pausar movimiento</button>
          <button id="resetView">Recentrar vista</button>
          <button id="zoomIn">Acercar</button>
          <button id="zoomOut">Alejar</button>
          <button data-focus="social">Ver social</button>
          <button data-focus="academico">Ver académico</button>
          <button data-focus="creativo">Ver creativo</button>
          <button data-focus="mixto">Ver mixto</button>
          <button data-focus="otro">Ver otro</button>
          <button id="showAuthors">Top autores</button>
          <button id="showArticles">Top artículos</button>
          <button id="toggleStrongLinks">Solo conexiones fuertes</button>
          <button id="fullscreenBtn">Pantalla completa</button>
          <button id="exportPng">Exportar PNG</button>
          <button id="downloadCsv">Descargar CSV visible</button>
        </div>
        <button id="toggleDetails" class="details-toggle">▼ Mostrar filtros, métricas y metodología</button>
        <div id="toolbarDetails" class="toolbar-details collapsed">
          <div class="legend">
            <span class="legend-item"><span class="dot" style="background:#4ea8de;color:#4ea8de"></span>Social</span>
            <span class="legend-item"><span class="dot" style="background:#7b6dff;color:#7b6dff"></span>Académico</span>
            <span class="legend-item"><span class="dot" style="background:#ff7ca8;color:#ff7ca8"></span>Creativo</span>
            <span class="legend-item"><span class="dot" style="background:#f1c453;color:#f1c453"></span>Otro</span>
            <span class="legend-item"><span class="dot" style="background:#5fd2a2;color:#5fd2a2"></span>Mixto</span>
          </div>
          <div class="line-key">
            <span>Línea tenue: mismo cluster</span>
            <span>Línea media: palabra clave compartida</span>
            <span>Línea fuerte: autor compartido</span>
          </div>
          <div class="filters">
            <input id="searchBox" type="search" placeholder="Buscar artículo, autor, palabra clave o DOI" />
            <div class="filter-row" id="yearFilters"></div>
            <div class="filter-row">
              <button class="active" data-cluster-toggle="social">Social</button>
              <button class="active" data-cluster-toggle="academico">Académico</button>
              <button class="active" data-cluster-toggle="creativo">Creativo</button>
              <button class="active" data-cluster-toggle="mixto">Mixto</button>
              <button class="active" data-cluster-toggle="otro">Otro</button>
            </div>
            <div class="metrics" id="metrics"></div>
          </div>
          <div class="method-box">
            <h3>Corpus visualizado</h3>
            <p>De 3384 registros iniciales, el mapa muestra {total_nodes} artículos después del filtrado temático.</p>
            <ul>
              <li>Se conservaron registros con año, título y resumen válidos.</li>
              <li>Se eliminaron duplicados por DOI o título limpio.</li>
              <li>Se exigió texto suficiente para análisis temático.</li>
              <li>Se conservaron solo artículos con evidencia de IA y población académica/universitaria.</li>
            </ul>
          </div>
        </div>
      </div>
      <div id="tooltip"></div>
    </div>
    <aside id="panel">
      <h2>Selecciona un artículo</h2>
      <p class="muted">Al seleccionar un nodo verás título, autores relevantes, palabras clave, términos importantes, resumen, DOI y la razón de clasificación por cluster.</p>
      <div id="panel-content"></div>
    </aside>
  </div>

  <script>
    const nodes = {nodes_json};
    const clusterStats = {stats_json};
    const edges = {edges_json};
    const canvas = document.getElementById("scene");
    const ctx = canvas.getContext("2d");
    const tooltip = document.getElementById("tooltip");
    const panelContent = document.getElementById("panel-content");
    const toggleMotionBtn = document.getElementById("toggleMotion");
    const resetViewBtn = document.getElementById("resetView");
    const zoomInBtn = document.getElementById("zoomIn");
    const zoomOutBtn = document.getElementById("zoomOut");
    const focusButtons = document.querySelectorAll("[data-focus]");
    const searchBox = document.getElementById("searchBox");
    const yearFilters = document.getElementById("yearFilters");
    const clusterToggleButtons = document.querySelectorAll("[data-cluster-toggle]");
    const metricsEl = document.getElementById("metrics");
    const showAuthorsBtn = document.getElementById("showAuthors");
    const showArticlesBtn = document.getElementById("showArticles");
    const toggleStrongLinksBtn = document.getElementById("toggleStrongLinks");
    const fullscreenBtn = document.getElementById("fullscreenBtn");
    const exportPngBtn = document.getElementById("exportPng");
    const downloadCsvBtn = document.getElementById("downloadCsv");
    const toggleDetailsBtn = document.getElementById("toggleDetails");
    const toolbarDetails = document.getElementById("toolbarDetails");

    let width = 0;
    let height = 0;
    let cameraZ = 980;
    let targetCameraZ = 980;
    let zoomLevel = 1.0;
    let targetZoomLevel = 1.0;
    let rotY = -0.52;
    let rotX = 0.32;
    let targetRotY = -0.52;
    let targetRotX = 0.32;
    let velocityY = 0.0039;
    let velocityX = 0.00095;
    let autoMotion = true;
    let drag = false;
    let lastX = 0;
    let lastY = 0;
    let projected = [];
    let projectedById = new Map();
    let hoveredNode = null;
    let selectedNode = null;
    let selectedYear = "todos";
    let searchQuery = "";
    let strongLinksOnly = false;
    let visibleClusters = new Set(["social", "academico", "creativo", "mixto", "otro"]);
    const years = [...new Set(nodes.map(node => node.year).filter(Boolean))].sort((a, b) => a - b);
    const stars = Array.from({{ length: 180 }}, (_, i) => ({{
      x: (i * 73) % 997 / 997,
      y: (i * 97) % 991 / 991,
      r: ((i * 17) % 9) / 10 + 0.4,
      a: ((i * 29) % 8) / 10 + 0.2,
    }}));

    function resize() {{
      width = canvas.clientWidth = canvas.parentElement.clientWidth;
      height = canvas.clientHeight = canvas.parentElement.clientHeight;
      canvas.width = width * devicePixelRatio;
      canvas.height = height * devicePixelRatio;
      ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    }}

    function rotatePoint(x, y, z) {{
      const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
      let dx = x * cosY - z * sinY;
      let dz = x * sinY + z * cosY;
      let dy = y * cosX - dz * sinX;
      dz = y * sinX + dz * cosX;
      return {{ x: dx, y: dy, z: dz }};
    }}

    function project(node) {{
      const p = rotatePoint(node.x, node.y, node.z);
      const scale = cameraZ / (cameraZ + p.z + 620);
      const zoomedScale = scale * zoomLevel;
      return {{
        ...node,
        sx: width / 2 + p.x * zoomedScale,
        sy: height / 2 + p.y * zoomedScale,
        scale: zoomedScale,
        depth: p.z,
        r: Math.max(2.8, node.size * zoomedScale),
      }};
    }}

    function textForSearch(node) {{
      return [
        node.title,
        node.doi,
        node.source_title,
        node.cluster,
        node.cluster_reason,
        ...(node.authors || []),
        ...(node.all_authors || []),
        ...(node.keywords || []),
        ...(node.important_terms || []),
        ...(node.cluster_terms || []),
      ].join(" ").toLowerCase();
    }}

    function nodeMatchesFilters(node) {{
      if (!visibleClusters.has(node.cluster)) return false;
      if (selectedYear !== "todos" && Number(node.year) !== Number(selectedYear)) return false;
      if (searchQuery && !textForSearch(node).includes(searchQuery)) return false;
      return true;
    }}

    function getVisibleNodes() {{
      return nodes.filter(nodeMatchesFilters);
    }}

    function renderMetrics() {{
      const visible = getVisibleNodes();
      const citations = visible.reduce((sum, node) => sum + (node.citations || 0), 0);
      const topNode = [...visible].sort((a, b) => b.citations - a.citations)[0];
      const byCluster = visible.reduce((acc, node) => {{
        acc[node.cluster] = (acc[node.cluster] || 0) + 1;
        return acc;
      }}, {{}});
      const dominantCluster = Object.entries(byCluster).sort((a, b) => b[1] - a[1])[0];
      metricsEl.innerHTML = `
        <div class="metric"><strong>${{visible.length}}</strong>artículos visibles</div>
        <div class="metric"><strong>${{citations}}</strong>citas acumuladas</div>
        <div class="metric"><strong>${{dominantCluster ? dominantCluster[0] : "N/A"}}</strong>cluster dominante</div>
        <div class="metric"><strong>${{topNode ? topNode.citations : 0}}</strong>citas del artículo top</div>
      `;
    }}

    function drawBackground() {{
      const g = ctx.createRadialGradient(width * 0.5, height * 0.45, 40, width * 0.5, height * 0.45, width * 0.6);
      g.addColorStop(0, "rgba(59, 77, 120, 0.22)");
      g.addColorStop(1, "rgba(9, 13, 20, 0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, width, height);

      for (const star of stars) {{
        ctx.beginPath();
        ctx.fillStyle = `rgba(210,230,255,${{star.a}})`;
        ctx.arc(star.x * width, star.y * height, star.r, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}

    function drawClusterLabels() {{
      Object.entries(clusterStats).forEach(([cluster, info]) => {{
        if (!visibleClusters.has(cluster)) return;
        const base = getVisibleNodes().find(n => n.cluster === cluster);
        if (!base) return;
        const p = project({{ ...base, x: base.x * 0.92, y: base.y * 0.92, z: base.z * 0.92, size: 0 }});
        ctx.save();
        ctx.font = "600 15px Segoe UI";
        ctx.fillStyle = "#dfe8f2";
        ctx.fillText(`${{cluster.toUpperCase()}} (${{info.articles}})`, p.sx + 12, p.sy - 12);
        ctx.restore();
      }});
    }}

    function edgeStyle(edge, activeNode) {{
      let stroke = "rgba(140, 155, 180, 0.18)";
      let width = 0.8;
      if (edge.relation === "keyword") {{
        stroke = "rgba(129, 202, 255, 0.24)";
        width = 1.05;
      }}
      if (edge.relation === "autor") {{
        stroke = "rgba(255, 255, 255, 0.34)";
        width = 1.45;
      }}
      if (activeNode && (edge.source === activeNode.id || edge.target === activeNode.id)) {{
        stroke = "rgba(255,255,255,0.62)";
        width += 1.25;
      }}
      return {{ stroke, width }};
    }}

    function draw() {{
      ctx.clearRect(0, 0, width, height);
      drawBackground();
      const visibleNodes = getVisibleNodes();
      projected = visibleNodes.map(project).sort((a, b) => a.depth - b.depth);
      projectedById = new Map(projected.map(node => [node.id, node]));

      for (const edge of edges) {{
        if (strongLinksOnly && edge.relation !== "autor" && edge.relation !== "keyword") continue;
        const a = projectedById.get(edge.source);
        const b = projectedById.get(edge.target);
        if (!a || !b) continue;
        const style = edgeStyle(edge, selectedNode || hoveredNode);
        ctx.beginPath();
        ctx.strokeStyle = style.stroke;
        ctx.lineWidth = style.width;
        ctx.moveTo(a.sx, a.sy);
        ctx.lineTo(b.sx, b.sy);
        ctx.stroke();
      }}

      drawClusterLabels();

      for (const p of projected) {{
        const glow = ctx.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, p.r * 3.6);
        glow.addColorStop(0, `${{p.color}}aa`);
        glow.addColorStop(1, `${{p.color}}00`);
        ctx.beginPath();
        ctx.fillStyle = glow;
        ctx.arc(p.sx, p.sy, p.r * 3.2, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.88;
        ctx.arc(p.sx, p.sy, p.r, 0, Math.PI * 2);
        ctx.fill();

        if ((selectedNode && selectedNode.id === p.id) || (hoveredNode && hoveredNode.id === p.id)) {{
          ctx.beginPath();
          ctx.globalAlpha = 1;
          ctx.lineWidth = selectedNode && selectedNode.id === p.id ? 2.4 : 1.5;
          ctx.strokeStyle = "#ffffff";
          ctx.arc(p.sx, p.sy, p.r + 3, 0, Math.PI * 2);
          ctx.stroke();
        }}
      }}
      ctx.globalAlpha = 1;
    }}

    function animate() {{
      if (!drag && autoMotion) {{
        targetRotY += velocityY;
        targetRotX += velocityX;
        if (targetRotX > 0.58 || targetRotX < 0.08) velocityX *= -1;
      }}
      cameraZ += (targetCameraZ - cameraZ) * 0.16;
      zoomLevel += (targetZoomLevel - zoomLevel) * 0.18;
      rotY += (targetRotY - rotY) * 0.14;
      rotX += (targetRotX - rotX) * 0.14;
      draw();
      requestAnimationFrame(animate);
    }}

    function hitTest(mx, my) {{
      for (let i = projected.length - 1; i >= 0; i--) {{
        const p = projected[i];
        const dx = mx - p.sx;
        const dy = my - p.sy;
        if (dx * dx + dy * dy <= (p.r + 4) * (p.r + 4)) return p;
      }}
      return null;
    }}

    function escapeHtml(text) {{
      return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function renderPanel(node) {{
      if (!node) {{
        panelContent.innerHTML = "";
        return;
      }}

      const authors = (node.authors || []).map(a => `<li>${{escapeHtml(a)}}</li>`).join("") || "<li>No disponibles</li>";
      const clusterAuthors = (node.cluster_top_authors || []).map(author => `
        <li>
          <strong>${{escapeHtml(author.author)}}</strong><br>
          <span class="muted">${{author.publications}} publicaciones en este cluster | ${{author.citations}} citas acumuladas</span>
        </li>
      `).join("") || "<li>No disponibles</li>";
      const keywords = (node.keywords || []).length
        ? node.keywords.map(k => `<span class="badge">${{escapeHtml(k)}}</span>`).join("")
        : `<span class="badge">No disponibles</span>`;
      const terms = (node.highlight_terms || []).map(item => `
        <li>
          <strong>${{escapeHtml(item.term)}}</strong>
          ${{item.classification_term ? '<span class="badge">clasifica</span>' : ''}}<br>
          <span class="muted">${{item.article_frequency}} apariciones en este artículo | presente en ${{item.cluster_presence}}% del cluster</span>
        </li>
      `).join("") || "<li>No disponibles</li>";
      const clusterTerms = (node.cluster_terms || []).length
        ? node.cluster_terms.map(t => `<span class="badge">${{escapeHtml(t)}}</span>`).join("")
        : `<span class="badge">No se detectaron terminos dominantes</span>`;

      panelContent.innerHTML = `
        <span class="badge" style="background:${{node.color}}22;border-color:${{node.color}}77;">${{escapeHtml(node.cluster)}}</span>
        <span class="badge">${{node.year ?? "Sin anio"}}</span>
        <span class="badge">${{node.citations}} citas</span>
        <h2>${{escapeHtml(node.title)}}</h2>
        <p class="muted">${{escapeHtml(node.source_title || "Fuente no disponible")}}</p>

        <div class="meta">
          <div class="card">
            <h3>Autores relevantes</h3>
            <ul class="authors-list">${{authors}}</ul>
          </div>
          <div class="card">
            <h3>DOI del artículo</h3>
            <p>${{node.doi !== "No disponible" ? escapeHtml(node.doi) : "No disponible"}}</p>
          </div>
        </div>

        <h3>Palabras clave</h3>
        <div>${{keywords}}</div>

        <h3>Palabras mas importantes</h3>
        <ul class="terms-list">${{terms}}</ul>

        <h3>Autores destacados del cluster</h3>
        <ul class="authors-list">${{clusterAuthors}}</ul>

        <h3>Resumen del artículo</h3>
        <p>${{escapeHtml(node.abstract_short)}}</p>

        <h3>Lectura del cluster</h3>
        <p>${{escapeHtml(node.cluster_reason)}}</p>
        <div>${{clusterTerms}}</div>
        <p>
          IA: <strong>${{node.score_ia}}</strong><br>
          Poblacion academica: <strong>${{node.score_poblacion}}</strong><br>
          Social: <strong>${{node.score_social}}</strong><br>
          Academico: <strong>${{node.score_academico}}</strong><br>
          Creativo: <strong>${{node.score_creativo}}</strong>
        </p>

        <h3>Registro fuente</h3>
        <p>${{node.link && node.link !== "No disponible" ? `<a href="${{escapeHtml(node.link)}}" target="_blank" rel="noreferrer">Abrir registro en Scopus</a>` : "No disponible"}}</p>

        <p class="note">Nota metodologica: el dataset de Scopus no trae DOI individual por autor. Por eso aqui se muestra el DOI del articulo y los autores mas relevantes asociados al registro.</p>
      `;
    }}

    function showTooltip(node, x, y) {{
      if (!node) {{
        tooltip.style.display = "none";
        return;
      }}
      tooltip.innerHTML = `<strong>${{escapeHtml(node.title)}}</strong><br>${{escapeHtml(node.cluster)}} | ${{node.year ?? "Sin anio"}} | ${{node.citations}} citas<br>${{escapeHtml(node.cluster_reason)}}`;
      tooltip.style.left = `${{x + 14}}px`;
      tooltip.style.top = `${{y + 14}}px`;
      tooltip.style.display = "block";
    }}

    canvas.addEventListener("mousedown", (e) => {{
      drag = true;
      lastX = e.clientX;
      lastY = e.clientY;
      canvas.style.cursor = "grabbing";
    }});

    window.addEventListener("mouseup", () => {{
      drag = false;
      canvas.style.cursor = "grab";
    }});

    window.addEventListener("mousemove", (e) => {{
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      if (drag) {{
        const dx = e.clientX - lastX;
        const dy = e.clientY - lastY;
        targetRotY += dx * 0.006;
        targetRotX += dy * 0.006;
        velocityY = dx * 0.00032;
        velocityX = dy * 0.00014;
        targetRotX = Math.max(-1.2, Math.min(1.2, targetRotX));
        lastX = e.clientX;
        lastY = e.clientY;
        return;
      }}

      hoveredNode = hitTest(mx, my);
      showTooltip(hoveredNode, mx, my);
    }});

    canvas.addEventListener("mouseleave", () => {{
      hoveredNode = null;
      tooltip.style.display = "none";
    }});

    canvas.addEventListener("click", (e) => {{
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      selectedNode = hitTest(mx, my);
      renderPanel(selectedNode);
    }});

    canvas.addEventListener("dblclick", (e) => {{
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const node = hitTest(mx, my);
      if (!node) return;
      selectedNode = node;
      renderPanel(selectedNode);
      targetZoomLevel = Math.min(6.5, targetZoomLevel + 0.85);
      targetRotY += (node.sx - width / 2) * -0.0009;
      targetRotX += (node.sy - height / 2) * -0.0009;
      targetRotX = Math.max(-1.1, Math.min(1.1, targetRotX));
    }});

    canvas.addEventListener("wheel", (e) => {{
      e.preventDefault();
      targetZoomLevel += e.deltaY * -0.0022;
      targetZoomLevel = Math.max(0.45, Math.min(8.5, targetZoomLevel));
    }}, {{ passive: false }});

    toggleMotionBtn.addEventListener("click", () => {{
      autoMotion = !autoMotion;
      toggleMotionBtn.textContent = autoMotion ? "Pausar movimiento" : "Reanudar movimiento";
    }});

    resetViewBtn.addEventListener("click", () => {{
      rotY = -0.52;
      rotX = 0.32;
      targetRotY = -0.52;
      targetRotX = 0.32;
      velocityY = 0.0039;
      velocityX = 0.00095;
      cameraZ = 980;
      targetCameraZ = 980;
      zoomLevel = 1.0;
      targetZoomLevel = 1.0;
    }});

    zoomInBtn.addEventListener("click", () => {{
      targetZoomLevel = Math.min(8.5, targetZoomLevel + 0.45);
    }});

    zoomOutBtn.addEventListener("click", () => {{
      targetZoomLevel = Math.max(0.45, targetZoomLevel - 0.45);
    }});

    function focusCluster(cluster) {{
      if (!visibleClusters.has(cluster)) {{
        visibleClusters.add(cluster);
        document.querySelector(`[data-cluster-toggle="${{cluster}}"]`)?.classList.add("active");
      }}
      const group = nodes.filter(node => node.cluster === cluster && nodeMatchesFilters(node));
      if (!group.length) return;
      const avg = group.reduce((acc, node) => {{
        acc.x += node.x;
        acc.y += node.y;
        acc.z += node.z;
        return acc;
      }}, {{ x: 0, y: 0, z: 0 }});
      avg.x /= group.length;
      avg.y /= group.length;
      avg.z /= group.length;
      targetZoomLevel = 2.1;
      targetRotY = Math.atan2(avg.x, avg.z + 1) * -1;
      targetRotX = Math.max(-0.8, Math.min(0.8, avg.y / -520));
      selectedNode = group[0];
      renderPanel(selectedNode);
    }}

    focusButtons.forEach(button => {{
      button.addEventListener("click", () => focusCluster(button.dataset.focus));
    }});

    function setupYearFilters() {{
      yearFilters.innerHTML = `<button class="active" data-year="todos">Todos los años</button>` +
        years.map(year => `<button data-year="${{year}}">${{year}}</button>`).join("");
      yearFilters.querySelectorAll("[data-year]").forEach(button => {{
        button.addEventListener("click", () => {{
          selectedYear = button.dataset.year;
          yearFilters.querySelectorAll("[data-year]").forEach(btn => btn.classList.toggle("active", btn === button));
          selectedNode = null;
          renderPanel(null);
          renderMetrics();
        }});
      }});
    }}

    searchBox.addEventListener("input", () => {{
      searchQuery = searchBox.value.trim().toLowerCase();
      selectedNode = null;
      renderPanel(null);
      renderMetrics();
    }});

    clusterToggleButtons.forEach(button => {{
      button.addEventListener("click", () => {{
        const cluster = button.dataset.clusterToggle;
        if (visibleClusters.has(cluster)) {{
          visibleClusters.delete(cluster);
          button.classList.remove("active");
        }} else {{
          visibleClusters.add(cluster);
          button.classList.add("active");
        }}
        selectedNode = null;
        renderPanel(null);
        renderMetrics();
      }});
    }});

    function renderTopAuthors() {{
      const visible = getVisibleNodes();
      const authors = new Map();
      for (const node of visible) {{
        for (const author of node.all_authors || node.authors || []) {{
          const current = authors.get(author) || {{ author, publications: 0, citations: 0, clusters: new Set() }};
          current.publications += 1;
          current.citations += node.citations || 0;
          current.clusters.add(node.cluster);
          authors.set(author, current);
        }}
      }}
      const rows = [...authors.values()]
        .sort((a, b) => b.publications - a.publications || b.citations - a.citations)
        .slice(0, 15)
        .map(author => `
          <li>
            <strong>${{escapeHtml(author.author)}}</strong><br>
            <span class="muted">${{author.publications}} publicaciones visibles | ${{author.citations}} citas | clusters: ${{escapeHtml([...author.clusters].join(", "))}}</span>
          </li>
        `).join("") || "<li>No hay autores visibles con los filtros actuales.</li>";
      panelContent.innerHTML = `
        <h2>Top autores visibles</h2>
        <p class="muted">Este listado cambia según el año, cluster o búsqueda activa.</p>
        <ul class="authors-list">${{rows}}</ul>
      `;
    }}

    showAuthorsBtn.addEventListener("click", renderTopAuthors);

    function renderTopArticles() {{
      const rows = getVisibleNodes()
        .sort((a, b) => b.citations - a.citations || (b.score_ia || 0) - (a.score_ia || 0))
        .slice(0, 15)
        .map(node => `
          <li>
            <strong>${{escapeHtml(node.title)}}</strong><br>
            <span class="muted">${{node.year ?? "Sin año"}} | ${{escapeHtml(node.cluster)}} | ${{node.citations}} citas | IA=${{node.score_ia}}</span>
          </li>
        `).join("") || "<li>No hay artículos visibles con los filtros actuales.</li>";
      panelContent.innerHTML = `
        <h2>Top artículos visibles</h2>
        <p class="muted">Ordenados por citas y, en empate, por intensidad de términos de IA.</p>
        <ul class="terms-list">${{rows}}</ul>
      `;
    }}

    showArticlesBtn.addEventListener("click", renderTopArticles);

    toggleStrongLinksBtn.addEventListener("click", () => {{
      strongLinksOnly = !strongLinksOnly;
      toggleStrongLinksBtn.classList.toggle("active", strongLinksOnly);
      toggleStrongLinksBtn.textContent = strongLinksOnly ? "Ver todas las conexiones" : "Solo conexiones fuertes";
    }});

    fullscreenBtn.addEventListener("click", async () => {{
      if (!document.fullscreenElement) {{
        await document.documentElement.requestFullscreen();
        fullscreenBtn.textContent = "Salir de pantalla completa";
      }} else {{
        await document.exitFullscreen();
        fullscreenBtn.textContent = "Pantalla completa";
      }}
    }});

    exportPngBtn.addEventListener("click", () => {{
      draw();
      const link = document.createElement("a");
      link.href = canvas.toDataURL("image/png");
      link.download = "mapa_3d_bibliometrico.png";
      link.click();
    }});

    function downloadVisibleCsv() {{
      const visible = getVisibleNodes();
      const headers = ["title", "year", "cluster", "citations", "authors", "doi", "cluster_reason"];
      const lines = [headers.join(",")];
      for (const node of visible) {{
        const row = [
          node.title,
          node.year ?? "",
          node.cluster,
          node.citations,
          (node.all_authors || node.authors || []).join("; "),
          node.doi,
          node.cluster_reason,
        ].map(value => `"${{String(value ?? "").replaceAll('"', '""')}}"`);
        lines.push(row.join(","));
      }}
      const blob = new Blob([lines.join("\\n")], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "articulos_visibles_mapa_3d.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}

    downloadCsvBtn.addEventListener("click", downloadVisibleCsv);

    toggleDetailsBtn.addEventListener("click", () => {{
      const collapsed = toolbarDetails.classList.toggle("collapsed");
      toggleDetailsBtn.textContent = collapsed
        ? "▼ Mostrar filtros, métricas y metodología"
        : "▲ Ocultar filtros, métricas y metodología";
    }});

    window.addEventListener("resize", () => {{
      resize();
    }});

    setupYearFilters();
    renderMetrics();
    resize();
    animate();
  </script>
</body>
</html>
"""


def main() -> None:
    df = pd.read_csv(DATASET_PATH)
    nodes, cluster_stats = build_nodes(df)
    edges = build_edges(nodes)
    html = build_html(nodes, cluster_stats, edges)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Visualizacion 3D guardada en: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
