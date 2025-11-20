import dnstwist
import json

def get_similar_registered_domains(domain: str) -> list[str]:
    """Given a domain name returns a list containing similar registered domain names"""

    domains_list = []
    domains = dnstwist.run(domain='ewala.es', threads=10)
    for domain in domains:
        domains_list.append(domain["domain"])
    return domains_list

            