import asyncio
import aiodns
import itertools
import dnstwist
import dnstwist_domain_generator as dns_dg

COMMON_TLDS = [".com", ".net", ".org", ".io", ".shop", ".online"]


async def generate_registered_candidates(base_domain: str):
    name, _, tld = base_domain.partition(".")
    candidates = set()

    # 1. Cambios de TLD
    for new_tld in COMMON_TLDS:
        candidates.add(name + new_tld)

    # 2. Typos básicos
    suffixes = ["-login", "-secure", "-verify", "-support", "-update", "-payment"]
    for s in suffixes:
        candidates.add(name + s + "." + tld)

    candidates.discard(base_domain)

    # Create resolver once
    resolver = aiodns.DNSResolver()

    # Run all DNS checks concurrently
    checks = {
        candidate: dns_dg.async_is_registered(resolver, candidate)
        for candidate in list(candidates)
    }

    results = await asyncio.gather(*checks.values())

    # Filter using results
    for candidate, is_registered in zip(checks.keys(), results):
        if not is_registered:
            candidates.discard(candidate)

    # Add similar registered domains (sync wrapper)
    similar = await dns_dg.get_similar_registered_domains(base_domain);
    for candidate in similar:
        candidates.add(candidate)

    # Limit to 5 if too big
    return sorted(candidates)[:5]

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
    fuzzer.generate(fuzzers=[			'addition', 'bitsquatting', 'hyphenation',
			'insertion', 'omission', 'plural', 'repetition', 'replacement',
			'subdomain', 'transposition', 'vowel-swap', 'dictionary'])
    for candidate in [e["domain"] for e in fuzzer.domains]:
        candidates.add(candidate)

    return sorted(candidates)
