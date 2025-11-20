from collections import Counter
from datetime import datetime
from typing import Protocol, List
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

    if response is None:
        raise Exception("Error doing request to Google AI")

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

def average(nums: List[int]) -> int:
    if not nums:
        raise ValueError("Cannot compute average of an empty list")
    return sum(nums) // len(nums)

def pais_frecuente(paises: List[str]) -> str:
    if not paises:
        raise ValueError("La lista está vacía")
    contador = Counter(paises)
    # `most_common(1)` devuelve una lista con tupla (pais, cantidad)
    return contador.most_common(1)[0][0]

class RecomendacionesParams:
    # Datos generales de los dominios analizados
    score_medio: float
    creacion_media: datetime
    pais_mas_frecuente: str


    # Datos del dominio importante
    domain: str
    score: int
    creation_date: datetime
    country: str
    action: str

    # Datos generales
    score_maximo: int
    dominio_propio: str

    def __init__(self, scores: list[int], creaciones: list[datetime], paises: list[str], importante_domain: str, importante_score: int, importante_creation_date: datetime, importante_country: str, importante_action: str, score_maximo: int, dominio_propio: str):
        self.score_medio = average(scores)
        creaciones_int = []
        for creacion in creaciones:
            creaciones_int.append(creacion.second)

        seconds = average(creaciones_int)
        self.creacion_media = datetime.utcfromtimestamp(seconds)

        self.pais_mas_frecuente = pais_frecuente(paises)

        self.domain = importante_domain
        self.score = importante_score
        self.creation_date = importante_creation_date
        self.country = importante_country
        self.action = importante_action

        self.dominio_propio = dominio_propio
        self.score_maximo = score_maximo



def generar_recomendaciones(params: RecomendacionesParams) -> dict:
    num_frases = 5

    prompt = (
        f"Se ha realizado un informe de typosqiatting."
        f"Se han analizado varios dominios problemáticos. He obtenido una puntuacion de media de {params.score_medio} "
        f"sobre {params.score_maximo} (mas es mayor seguridad) "
        f"de typesquatting para mi dominio {params.dominio_propio}. El dominio mas problemático, con un score de {params.score}, del pais {params.country}, con dominio registrado el {params.creation_date} (hoy es {datetime.now()}) "
        f"dominio {params.domain} podría suplantar la web de mi marca, el informe ha detectado que la action recomendada es {params.action}."
        f"Dame una lista de {num_frases * 2} frases cortas para ayudar al "
        f"generente a a solventar el problema, en concreto, teniendo en cuenta el tipo de typesquatting y la gravedad asignada. Solo devuelve la lista, no digas nada mas, "
        f"debe poder ser parseable por python ast, asi que no especifiques nada de markdown tampoco. Las {num_frases} primeras frases deben estar relacionadas con las recomendaciones en general, las {num_frases} ultimas frases se relacionaran con el dominio mas problemático."
    )



    lista_str = ""
    lista_parsed = []

    while True:
        try:
            lista_str = call_google_llm(prompt)
        except:
            print("Exception occured on parse list")

        lista_parsed = parse_list(lista_str)

        if len(lista_parsed) == num_frases * 2:
            break
        print("La salida del LLM fue invalida: ", lista_str)


    return {
        "generales": lista_parsed[:num_frases],
        "especificas": lista_parsed[num_frases:],
    }


if __name__ == "__main__":
    params = RecomendacionesParams([12, 20, 32, 12, 15, 17], [datetime.now()], ["España", "España", "España", "Italia", "Italia", "Portugal"], "evvala.es", 30, datetime.now(), "España", "Alto riesgo: revisar contenido y considerar denuncia al registrador/hosting.", 100, "ewala.es")
    res = generar_recomendaciones(params)
    print(res)
