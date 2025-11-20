import itertools
import dnstwist

COMMON_TLDS = [".com", ".net", ".org", ".io", ".shop", ".online"]

def generate_candidates(base_domain: str):
    name, _, tld = base_domain.partition(".")
    candidates = set()
    
    try: #dnstwist es herramienta OSINT estandar para generar homografos
        fuzzed_domains = dnstwist.fuzz(base_domain)
        for entry in fuzzed_domains:
            domain_name = entry.get('domain-name')
            punycode_name = entry.get('punycode')
            
            if domain_name:
                candidates.add(domain_name)
    
            if punycode_name and punycode_name != domain_name:
                candidates.add(punycode_name)

    except Exception as e:
        print(f"Advertencia: dnstwist falló para {base_domain}. Error: {e}")

    # 1. Cambios de TLD
    for new_tld in COMMON_TLDS:
        candidates.add(name + new_tld)

    # 2. Typos básicos (sufijos típicos de phishing)
    suffixes = ["-login", "-secure", "-verify", "-support", "-update", "-payment"]
    for s in suffixes:
        candidates.add(name + s + "." + tld)

    # 3. Reemplazos sencillos de caracteres
    replaces = {'o': '0', 'e': '3', 'l': '1', 'a': '4'}
    for i, c in enumerate(name):
        if c in replaces:
            candidates.add(name[:i] + replaces[c] + name[i+1:] + "." + tld)

    # Evitar el original
    candidates.discard(base_domain)

    import dnstwist_domain_generator as dns_dg
    for candidate in dns_dg.get_similar_registered_domains_sync_wrapper(base_domain):
        candidates.add(candidate)

    return sorted(candidates)

