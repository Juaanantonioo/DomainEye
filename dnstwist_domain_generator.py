import asyncio
import aiodns # Librería Asíncrona de DNS
import aiodns.error # Para manejar errores específicos de DNS

# dnstwist imports (mantienen su uso síncrono para la generación)
from dnstwist import Fuzzer
import json

# --- 1. FUNCIÓN ASÍNCRONA DE VERIFICACIÓN ---
async def async_is_registered(resolver: aiodns.DNSResolver, domain: str) -> bool:
    """Intenta resolver un registro A (IP) para el dominio de forma asíncrona."""
    try:
        # Usamos await para esperar el resultado de la consulta
        await resolver.query(domain, 'A')
        return True
        
    # aiodns tiene sus propios códigos de error
    except aiodns.error.DNSError as e:
        # Código 1 es NXDOMAIN (No existe) o 4 (NoAnswer)
        # Esto indica que el dominio no está registrado o no tiene registro A
        return False
        
    except Exception:
        # Errores generales (ej. timeout de red)
        return False

# --- 2. FUNCIÓN PRINCIPAL ASÍNCRONA ---
async def async_get_similar_registered_domains(domain: str) -> list[str]:
    """Genera dominios similares y los verifica de forma concurrente."""

    print(f"[*] Generando candidatos similares a {domain}...")
    
    # 1. Generación (Síncrona, ya que dnstwist no es async)
    fuzzer = Fuzzer(domain)
    fuzzer.generate()
    candidates = [e["domain"] for e in fuzzer.domains]
    
    total_candidates = len(candidates)
    print(f"[*] Se generaron {total_candidates} candidatos. Verificando asíncronamente...")

    # 2. Configuración asíncrona
    # Inicializamos el resolver una sola vez
    resolver = aiodns.DNSResolver()
    
    # Creamos una lista de TAREAS
    tasks = [async_is_registered(resolver, candidate) for candidate in candidates]

    # 3. Ejecutar TAREAS concurrentemente
    # asyncio.gather ejecuta todas las peticiones a la vez (mucho más rápido)
    results = await asyncio.gather(*tasks)

    # 4. Filtrar resultados y devolver la lista
    registered_domains = [
        candidates[i] 
        for i, is_reg in enumerate(results) 
        if is_reg
    ]
            
    return registered_domains

# --- 3. ENVOLTORIO SÍNCRONO PARA EJECUTAR EL BUCLE ---
def get_similar_registered_domains_sync_wrapper(domain: str) -> list[str]:
    """Función de interfaz para ejecutar el código asíncrono desde un contexto síncrono."""
    return asyncio.run(async_get_similar_registered_domains(domain))


if __name__ == "__main__":
    # --- Ejemplo de Uso ---
    base_domain = 'google.com' 
    dominios_registrados = get_similar_registered_domains_sync_wrapper(base_domain)

    print("\n--- Resultado Final ---")
    if dominios_registrados:
        print("Dominios Similares y Registrados Encontrados:")
        for d in dominios_registrados:
            print(f"- {d}")
    else:
        print("No se encontraron dominios similares registrados.")