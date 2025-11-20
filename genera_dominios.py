import asyncio
import aiodns
import itertools
import dnstwist
import dnstwist_domain_generator as dns_dg

COMMON_TLDS = [".com", ".net", ".org", ".io", ".shop", ".online"]

def generate_registered_candidates(base_domain: str):
    name, _, tld = base_domain.partition(".")
    candidates = set()

    # 1. Cambios de TLD
    for new_tld in COMMON_TLDS:
        candidates.add(name + new_tld)

    # 2. Typos básicos (sufijos típicos de phishing)
    suffixes = ["-login", "-secure", "-verify", "-support", "-update", "-payment"]
    for s in suffixes:
        candidates.add(name + s + "." + tld)

    # Evitar el original
    candidates.discard(base_domain)
    for candidate in candidates.copy():
        if not asyncio.run(dns_dg.async_is_registered(aiodns.DNSResolver, candidate)):
            candidates.discard(candidate)

    for candidate in dns_dg.get_similar_registered_domains_sync_wrapper(base_domain):
        candidates.add(candidate)

    return sorted(candidates)

def generate_all_candidates(base_domain: str):
    name, _, tld = base_domain.partition(".")
    candidates = set()

    # 1. Cambios de TLD
    for new_tld in COMMON_TLDS:
        candidates.add(name + new_tld)

    # 2. Typos básicos (sufijos típicos de phishing)
    suffixes = ["-login", "-secure", "-verify", "-support", "-update", "-payment"]
    for s in suffixes:
        candidates.add(name + s + "." + tld)

    # Evitar el original
    candidates.discard(base_domain)
    
    fuzzer = dnstwist.Fuzzer(base_domain)
    fuzzer.generate()
    for candidate in [e["domain"] for e in fuzzer.domains]:
        candidates.add(candidate)

    return sorted(candidates)