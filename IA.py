from abc import ABC, abstractmethod
from typing import Any
from google import genai
import os

# CREA EL TIPO DE FORMATO QUE LLEVARA Y SE ENCARGA UNICAMENTE DE CONVERTIR EL FORMATO AL ADECUADO
class AiFormat(ABC):
    @abstractmethod
    def format(self, unformatted_ask: Any) -> str:
        pass

# SE DEDICA UNICAMENTE A RECIBIR UNA PREGUNTA Y A DAR LA RESPUESTA
class AiType(ABC):
    def __init__(self, ai_format: AiFormat):
        self.ai_format = ai_format

    @abstractmethod
    def ai_ask(self, ask: str) -> str:
        pass

# ES EL ENCARGADO DE QUE TODAS LAS CLASES FUNCIONEN ENTRE SÍ PARA GENERAR UN RESULTADO
class AiModel(ABC):
    def __init__(
        self, 
        ai_type : AiType, 
        ai_format : AiFormat, 
        api_key = ""
    ):
        self.api_key = api_key
        self.ai_type = ai_type
        self.ai_format = ai_format
    

class GoogleFormat(AiFormat):
    def format(self, unformatted_ask: Any) -> str:
        return str(unformatted_ask)
    
class GoogleType(AiType):
    def __init__(self, ai_format: AiFormat, ai_key: str):
        super().__init__(ai_format)
        self.ai_key = ai_key

    def ai_ask(self, ask: str) -> str:
        client = genai.Client()
        client = genai.Client(api_key="xxx")
        response = client.models.generate_content(
            model="gemini-3-flash-preview", contents="Hola"
        )
        return str(response.text)

google_format = GoogleFormat()
google_type = GoogleType(google_format, "")


google_ai = AiModel(google_type, google_format)

print(google_ai.ai_type.ai_ask("Hola"))

# QUIERO FACTORIZARLO PARA QUE SEA SOLID Y CLEAN CODE:






# IA
# clase TIPO(distintos) con polimorfismo en api_key -> GoogleStudio
# clase formato(distintos) -> String
# variable api key (que se pueda utilizar o no)