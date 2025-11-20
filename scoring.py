from datetime import datetime
from Levenshtein import distance as levenshtein_distance


def score_domain(base_domain, candidate, whois_data, dns_data, http_data, base_http_data):
    """
    Calcula el score 0–100 y devuelve también la lista de señales activas.

    Señales y pesos (como en el documento del reto):

      +20  Very similar domain (distance ≤2 / homograph)
      +10  Cheap/unusual TLD for the brand
      +10  Recent domain (<6 months) or WHOIS change
      +5   WHOIS privacy / incomplete WHOIS data
      +5   Recent valid certificate with minimal SANs      (*aprox: HTTPS activo*)
      +15  Page with form/login but no CSP/HSTS
      +10  Favicon hash identical/similar to official
      +10  Suspicious redirects (crypto/ads/shorteners)
      +10  Brand evidence (logo/text)
      -10  Benign signals (parked page/banner)
      -20  Clearly used by a legitimate third party
    """

    score = 0
    reasons = []

    name_base, _, _ = base_domain.partition(".")
    name_cand, _, tld_cand = candidate.partition(".")

    # ---------- 1) Very similar domain (distance ≤2)  (+20) ----------
    dist = levenshtein_distance(name_base, name_cand)
    if dist <= 2:
        score += 20
        reasons.append(f"Nombre muy similar al original (distancia Levenshtein = {dist})")

    # --- Dominio defensivo de la propia marca (redirige al oficial) ---
    # Si este flag viene a True desde generar_informe.py, cortamos aquí.
    if http_data.get("owned_by_brand"):
        reasons.append("Dominio defensivo registrado por la propia marca (redirige al sitio oficial)")
        return 0, reasons

    # ---------- 2) Cheap / unusual TLD for the brand  (+10) ----------
    suspicious_tlds = {
        "xyz", "top", "click", "link", "info",
        "online", "icu", "kim", "shop"
    }
    if tld_cand.lower() in suspicious_tlds:
        score += 10
        reasons.append(f"TLD poco habitual o barato para la marca (.{tld_cand})")

    # ---------- 3) Recent domain (<6 months)          (+10) ----------
    created = whois_data.get("creation_date")
    if isinstance(created, datetime):
        days = (datetime.utcnow() - created).days
        if days < 180:
            score += 10
            reasons.append(f"Dominio muy reciente ({days} días desde la creación)")

    # ---------- 4) WHOIS privacy / incomplete         (+5) ----------
    if whois_data.get("uses_privacy") or whois_data.get("whois_incomplete"):
        score += 5
        reasons.append("WHOIS con privacidad activada o datos incompletos")

    # ---------- 5) Recent valid certificate           (+5) ----------
    # Aproximación: si responde por HTTPS asumimos cert válido.
    if http_data.get("has_https"):
        score += 5
        reasons.append("Sitio con certificado TLS válido (HTTPS activo)")

    # ---------- 6) Form/login sin CSP/HSTS            (+15) ----------
    has_form = http_data.get("has_form")
    has_login_form = http_data.get("has_login_form")
    has_csp = http_data.get("has_csp")
    has_hsts = http_data.get("has_hsts")

    if (has_login_form or has_form) and not (has_csp or has_hsts):
        score += 15
        reasons.append("Formulario o login sin cabeceras de protección CSP/HSTS")

    # ---------- 7) Favicon igual al oficial           (+10) ----------
    fav_base = base_http_data.get("favicon_hash")
    fav_cand = http_data.get("favicon_hash")
    if fav_base and fav_cand and fav_base == fav_cand:
        score += 10
        reasons.append("Favicon idéntico o muy similar al del sitio oficial")

    # ---------- 8) Suspicious redirects               (+10) ----------
    if http_data.get("suspicious_redirect"):
        score += 10
        reasons.append("Redirecciones sospechosas (crypto/ads/shorteners)")

    # ---------- 9) Brand evidence                     (+10) ----------
    brand = name_base.lower()
    brand_mentions = http_data.get("brand_mentions", 0)
    if brand_mentions >= 1:
        score += 10
        reasons.append(f"Evidencia de marca en el contenido (menciona '{brand}' {brand_mentions} veces)")

    # ---------- 10) Benign signals (parked)           (-10) ----------
    if http_data.get("is_parked"):
        score -= 10
        reasons.append("Página aparentemente aparcada / en venta (señal benigna)")

    # ---------- 11) Legit third party                 (-20) ----------
    if http_data.get("likely_legit_third_party"):
        score -= 20
        reasons.append("Parece un dominio legítimo de un tercero (otra marca / proyecto OSS)")

    # Normalizamos al rango 0–100
    if score < 0:
        score = 0
    if score > 100:
        score = 100

    # nota: podemos añadir más criterios adelante
    return score, reasons
