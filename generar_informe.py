#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import hashlib
import socket
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional
import numpy as np
from sklearn.cluster import KMeans

import requests
import whois
import dns.resolver
import dnstwist  # si luego lo usáis para generar dominios

from genera_dominios import generate_registered_candidates
from scoring import score_domain

# Timeout global de sockets (WHOIS, DNS, HTTP)
socket.setdefaulttimeout(3)


# -------- WHOIS --------

def empty_whois_data() -> dict:
    return {
        "creation_date": None,
        "country": None,
        "uses_privacy": False,
        "whois_incomplete": False,
    }

def calculate_simple_global_risk(scores: list) -> float:
    """Función de respaldo que usa la partición simple (>= 61) si K-Means falla."""
    if not scores: 
        return 0.0
    high_risk_count = sum(1 for score in scores if score >= 61)
    global_risk_score = (high_risk_count / len(scores)) * 100
    return round(global_risk_score, 2)

def calculate_global_risk(scores: list) -> tuple:
    """
    Calcula el riesgo global basándose en clustering K-Means sobre los scores.
    El riesgo global es la proporción de dominios en el clúster de más alto riesgo.
    """
    if not scores:
        return 0.0, {}

    # Los scores se agrupan en K=3 clusters (Bajo, Medio, Alto)
    X = np.array(scores).reshape(-1, 1)

    try:
        # 1. Aplicar K-Means con K=3
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10, max_iter=300)
        kmeans.fit(X)

        # 2. Identificar el clúster de MÁS alto riesgo
        # Los centroides nos dan la puntuación media de cada grupo
        centroids = kmeans.cluster_centers_.flatten()
        
        # Encontrar el índice del clúster con el centroide más alto
        highest_risk_cluster_index = np.argmax(centroids)

        # 3. Contar dominios en ese clúster
        labels = kmeans.labels_
        high_risk_count = np.sum(labels == highest_risk_cluster_index)
        total_count = len(scores)

        # 4. Calcular el Riesgo Global (Proporción de dominios de Alto Riesgo)
        global_risk_score = (high_risk_count / total_count) * 100
        
        # 5. Mapear etiquetas de clúster para explicabilidad
        sorted_centroid_indices = np.argsort(centroids)
        cluster_mapping = {}
        cluster_mapping[sorted_centroid_indices[0]] = "Bajo"  # Centroide más bajo
        cluster_mapping[sorted_centroid_indices[1]] = "Medio" # Centroide intermedio
        cluster_mapping[sorted_centroid_indices[2]] = "Alto"  # Centroide más alto

        return round(global_risk_score, 2), cluster_mapping
        
    except ValueError as e:
        # Esto ocurre si hay muy pocos datos para 3 clusters.
        print(f"Advertencia: K-Means falló con {len(scores)} puntos. Usando partición simple. {e}")
        # Retorna el cálculo simple si K-Means falla
        return calculate_simple_global_risk(scores), {}


def get_whois_data(domain: str) -> dict:
    """Devuelve info WHOIS simplificada para un dominio, con timeout corto."""
    data = empty_whois_data()
    try:
        # timeout pequeño para que NO se quede colgado
        w = whois.whois(domain, timeout=3)

        creation_date = getattr(w, "creation_date", None)
        if isinstance(creation_date, list) and creation_date:
            creation_date = creation_date[0]
        data["creation_date"] = creation_date

        country = getattr(w, "country", None)
        if isinstance(country, list) and country:
            country = country[0]
        data["country"] = country

        # Heurística de privacidad/incompleto
        raw_text = str(w).lower()
        privacy_keywords = ["privacy", "whoisguard", "contact privacy", "gdpr masking"]
        uses_privacy = any(k in raw_text for k in privacy_keywords)

        key_fields = [
            getattr(w, "name", None),
            getattr(w, "org", None),
            getattr(w, "registrant_name", None),
        ]
        non_empty = [f for f in key_fields if f]
        whois_incomplete = len(non_empty) <= 1

        data["uses_privacy"] = uses_privacy
        data["whois_incomplete"] = whois_incomplete

    except Exception:
        # Si WHOIS falla o hace timeout, devolvemos datos vacíos y seguimos
        pass

    return data


# -------- DNS --------

def get_dns_data(domain: str) -> dict:
    """Devuelve IP principal y registros MX (si existen)."""
    dns_data = {
        "ip": None,
        "mx_records": []
    }

    resolver = dns.resolver.Resolver()

    # IP (A)
    try:
        answers = resolver.resolve(domain, "A")
        ips = [rdata.to_text() for rdata in answers]
        if ips:
            dns_data["ip"] = ips[0]
    except Exception:
        pass

    # MX
    try:
        answers = resolver.resolve(domain, "MX")
        mx = [rdata.exchange.to_text() for rdata in answers]
        dns_data["mx_records"] = mx
    except Exception:
        pass

    return dns_data


# -------- HTTP / CONTENIDO / FAVICON --------

def empty_http_data() -> dict:
    return {
        "final_url": None,
        "final_domain": None,
        "status_code": None,
        "has_https": False,
        "has_hsts": False,
        "has_csp": False,
        "has_form": False,
        "has_login_form": False,
        "brand_mentions": 0,
        "is_parked": False,
        "suspicious_redirect": False,
        "favicon_hash": None,
        "likely_legit_third_party": False,
        "owned_by_brand": False,   # marcado si redirige al dominio oficial
    }


def get_http_data(domain: str, brand_name: str) -> dict:
    """Obtiene señales HTTP/TLS y contenido básico para el dominio."""
    data = empty_http_data()

    # Intentamos primero HTTPS y luego HTTP
    resp = None
    for scheme in ("https://", "http://"):
        url = scheme + domain
        try:
            resp = requests.get(
                url,
                timeout=4,
                allow_redirects=True,
                headers={"User-Agent": "TyposquatHunter/1.0"}
            )
            break
        except Exception:
            continue

    if not resp:
        return data

    data["status_code"] = resp.status_code
    data["final_url"] = resp.url

    parsed = urlparse(resp.url)
    final_domain = parsed.hostname or domain
    data["final_domain"] = final_domain
    data["has_https"] = parsed.scheme == "https"

    headers = {k.lower(): v for k, v in resp.headers.items()}
    data["has_hsts"] = "strict-transport-security" in headers
    data["has_csp"] = "content-security-policy" in headers

    # Procesamos contenido de texto (limitamos para no explotar memoria)
    try:
        text = resp.text.lower()
    except Exception:
        text = ""

    brand = brand_name.lower()
    data["brand_mentions"] = text.count(brand)

    data["has_form"] = "<form" in text
    data["has_login_form"] = ("password" in text) or ("login" in text) or ("iniciar sesión" in text)

    parked_keywords = [
        "domain for sale",
        "buy this domain",
        "este dominio está en venta",
        "parkingcrew",
        "sedo parking",
        "this domain may be for sale"
    ]
    data["is_parked"] = any(k in text for k in parked_keywords)

    suspicious_keywords = ["crypto", "bitcoin", "casino", "betting", "porn", "xxx"]
    shorteners = ["bit.ly", "t.co", "tinyurl.com", "goo.gl"]
    final_url_lower = (data["final_url"] or "").lower()
    if any(k in final_url_lower for k in suspicious_keywords + shorteners):
        data["suspicious_redirect"] = True

    # Heurística muy sencilla de "tercero legítimo"
    third_party_keywords = ["github", "gitlab", "wikipedia", "docs", "readthedocs"]
    if any(k in final_url_lower for k in third_party_keywords) and data["brand_mentions"] == 0:
        data["likely_legit_third_party"] = True

    # Favicon
    try:
        fav_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
        fav_resp = requests.get(
            fav_url,
            timeout=4,
            headers={"User-Agent": "TyposquatHunter/1.0"}
        )
        if fav_resp.ok and fav_resp.content:
            data["favicon_hash"] = hashlib.md5(fav_resp.content).hexdigest()
    except Exception:
        pass

    return data


# -------- Utilidades HTML / dominio --------

def risk_class(score: int) -> str:
    """Clasifica el score en low/med/high para aplicar estilos CSS."""
    if score < 30:
        return "risk-low"
    elif score < 60:
        return "risk-med"
    else:
        return "risk-high"


def suggest_action(score: int, whois_data: dict, dns_data: dict) -> str:
    """Texto de recomendación de acción según score y datos."""
    if whois_data.get("creation_date") is None and dns_data.get("ip") is None:
        return "Posible dominio libre: se recomienda registro defensivo."

    if score >= 60:
        return "Alto riesgo: revisar contenido y considerar denuncia al registrador/hosting."
    elif score >= 30:
        return "Riesgo medio: monitorizar y revisar periódicamente."
    else:
        return "Riesgo bajo: monitorizar de forma pasiva."


def format_date(dt: datetime) -> str:
    if not isinstance(dt, datetime):
        return "-"
    return dt.strftime("%Y-%m-%d")


def normalize_brand_domain(hostname: Optional[str]) -> Optional[str]:
    """
    Normaliza un hostname para compararlo a nivel de marca:
    - quita 'www.'
    - se queda con los dos últimos labels (google.com, ewala.com, etc.)
    """
    if not hostname:
        return None

    host = hostname.lower().strip()

    if host.startswith("www."):
        host = host[4:]

    parts = host.split(".")
    if len(parts) >= 2:
        host = ".".join(parts[-2:])

    return host


def build_rows(base_domain: str, candidates: list, base_http_data: dict):
    """
    Construye las filas HTML y devuelve:
      - ordered_rows_html: filas <tr> ordenadas por score (desc)
      - all_scores: lista de scores numéricos para calcular riesgo global
    """
    all_results = []
    all_scores = []

    brand = base_domain.split(".")[0].lower()
    base_norm = normalize_brand_domain(base_domain)

    for domain in candidates:
        # 1) DNS
        dns_data = get_dns_data(domain)

        if dns_data.get("ip") or dns_data.get("mx_records"):
            whois_data = get_whois_data(domain)
        else:
            whois_data = empty_whois_data()

        # 2) HTTP / contenido
        http_data = get_http_data(domain, brand)

        # Dominio defensivo: redirige al mismo dominio de marca
        final_dom = http_data.get("final_domain")
        final_norm = normalize_brand_domain(final_dom)
        if final_norm and base_norm and final_norm == base_norm:
            http_data["owned_by_brand"] = True

        # 3) Scoring
        score, reasons = score_domain(
            base_domain,
            domain,
            whois_data,
            dns_data,
            http_data,
            base_http_data,
        )

        all_scores.append(score)

        result = {
            "domain": domain,
            "score": score,
            "ip": dns_data.get("ip") or "-",
            "creation_date": format_date(whois_data.get("creation_date")),
            "country": whois_data.get("country") or "-",
            "css_class": risk_class(score),
            "action": suggest_action(score, whois_data, dns_data),
            "reasons": reasons,
        }
        all_results.append(result)

    # Ordenamos por score descendente
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Construimos el HTML final de filas
    ordered_rows_html = ""
    for r in all_results:
        signals_html = "<br>".join(r["reasons"]) if r["reasons"] else "-"
        row = f"""
        <tr class="{r['css_class']}">
          <td>{r['domain']}</td>
          <td>{r['score']}</td>
          <td>{r['ip']}</td>
          <td>{r['creation_date']}</td>
          <td>{r['country']}</td>
          <td>{r['action']}</td>
          <td>{signals_html}</td>
        </tr>
        """
        ordered_rows_html += row

    return ordered_rows_html, all_scores


# -------- main --------

def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_informe.py dominio.com")
        sys.exit(1)

    base_domain = sys.argv[1].strip()
    brand = base_domain.split(".")[0]

    print(f"[+] Generando candidatos para: {base_domain}")
    candidates = generate_registered_candidates(base_domain)
    print(f"[+] Se han generado {len(candidates)} dominios candidatos.")

    print("[+] Analizando dominio base para extraer favicon y señales de marca...")
    base_http_data = get_http_data(base_domain, brand)

    print("[+] Recopilando WHOIS/DNS/HTTP y calculando scores...")
    table_rows_html, all_scores = build_rows(base_domain, candidates, base_http_data)

    # Riesgo global
    global_risk_score = calculate_global_risk(all_scores)
    print(f"[+] Riesgo Global (porcentaje de dominios de Alto Riesgo): {global_risk_score}%")

    # Leer la plantilla HTML
    with open("reporte.html", "r", encoding="utf-8") as f:
        template = f.read()

    # Reemplazar marcador del dominio base y el riesgo global
    html = template.replace("{{ base_domain }}", base_domain)
    html = html.replace("{{ global_risk_score }}", str(global_risk_score))

    # Insertar filas en la tabla donde está el comentario
    marker = "<!-- Aquí iteras en tu script e insertas filas -->"
    if marker in html:
        html = html.replace(marker, table_rows_html)
    else:
        html = html.replace("</table>", table_rows_html + "\n  </table>")

    output_file = "informe_" + base_domain.replace(".", "_") + ".html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[+] Informe generado: {output_file}")
    print("[+] Ábrelo en tu navegador para la demo.")


if __name__ == "__main__":
    main()
