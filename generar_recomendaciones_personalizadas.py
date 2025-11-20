import os
from google import genai
from google.genai import types

def call_google_llm(prompt: str, model: str = "gemini-2.5-flash") -> str:
    api_key = "AIzaSyBPoXXaoCfwNvUKYEPhIniFt1AZRVEXXKo"
    if not api_key:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable")

    # Create the client, passing the API key
    client = genai.Client(api_key=api_key)

    # Call the model
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7
        )
    )

    return response.text

def parse_list(s):
    try:
        value = ast.literal_eval(s)
        # optional: enforce that it *is* a list
        if not isinstance(value, list):
            raise TypeError("Not a list")
        return value
    except (ValueError, SyntaxError, TypeError) as e:
        print("Could not parse:", e)
        return []      # or None, or re-raise


import ast

def generar_recomendaciones(dominio_propio: str, dominio_externo: str,
                            puntuacion_obtenida, puntuacion_maxima) -> list:

    num_frases = 5

    prompt = (
        f"He obtenido una puntuacion de {puntuacion_obtenida} "
        f"sobre {puntuacion_maxima} (mas es mayor seguridad) en una prueba "
        f"de typesquatting para mi dominio {dominio_propio}, ya que el "
        f"dominio {dominio_externo} podría suplantar la web de mi marca. "
        f"Dame una lista de {num_frases} frases cortas para ayudar al "
        f"generente a a solventar el problema, en concreto, teniendo el tipo de typesquatting y la gravedad asignada. Solo devuelve la lista, no digas nada mas, "
        f"debe poder ser parseable por python ast, asi que no especifiques nada de markdown tampoco"
    )

    
    lista_str = call_google_llm(prompt)
    print(prompt)
    lista_parsed = []

    while True:
        try:
            lista_parsed = parse_list(lista_str)
        except:
            print("Exception occured")
            lista_parsed = []

        if len(lista_parsed) == num_frases:
            break
        print("La salida del LLM fue invalida: ", lista_str)

        lista_str = call_google_llm(prompt)

    return lista_parsed


if __name__ == "__main__":
    res = generar_recomendaciones("ewala.es", "evvala.es", 20, 100)
    print(res)
