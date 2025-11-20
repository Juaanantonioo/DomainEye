from dnstwist import Fuzzer # Importamos la clase específica
import json

def get_similar_registered_domains(domain: str) -> list[str]:
    """Dado un nombre de dominio, devuelve una lista que contiene nombres de dominio registrados similares (SOLO GENERADOS)"""

    # 1. Instanciar la clase Fuzzer
    # Usamos el parámetro 'domain' de la función
    fuzzer = Fuzzer(domain)
    
    # 2. Generar los candidatos (Reemplaza la llamada obsoleta)
    # El método .generate() crea todas las permutaciones y las almacena internamente.
    fuzzer.generate() 
    
    domains_list = []
    
    # 3. Iterar sobre la lista de dominios generados (.domains)
    # Cada elemento es un diccionario que contiene la clave 'domain'
    for entry in fuzzer.domains:
        # Aseguramos que el valor sea un string antes de agregarlo
        domains_list.append(entry["domain"])
        
    return domains_list

if __name__ == "__main__":
    # Ejemplo de uso:
    print(f"[+] Generando candidatos para: google.com")
    candidatos = get_similar_registered_domains('ewala.es')
    # print(candidatos)
    print(f"[+] Se generaron {len(candidatos)} dominios similares.")

