from openai import OpenAI
from funciones.asistente import getFuncionesAsistente
import os
import json

class AsistenteModelo():
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("API_GPT")
        )
        self.sistema = [
            {
                "role": "system",
                "content": "Eres un asistente medico y te encuentras operativo en el área de triage en una clínica, te preocupas por la salud del paciente en turno y para poder ayudarle necesitas saber todos los sintomas que está presentando. Si el paciente ha experimentado anteriormente otros tipos de sintomas, comenzaras preguntandole si los sigue presentando actualmente, cuando termines de hablar de ello con el paciente, le preguntaras si tiene nuevos sintomas actualmente. Si el paciente no te da mucha información, le preguntaras mas detalle sobre cada uno de los sintomas que presenta."
                
            }
        ]
        self.funciones = getFuncionesAsistente()

    def getRespuesta(self, mensajes, compMsgs):
        tMensajes = mensajes
        for cm in compMsgs:
            tMensajes.insert(cm['lastId'], cm['data']);
        response = self.client.chat.completions.create(
            model="gpt-4o", #3.5-turbo
            messages=tMensajes,
            tools=self.funciones,
            tool_choice="auto",
            max_tokens=256,
            temperature=1,
            top_p=1
        )
        respuesta = response.choices[0].message
        print(response.choices[0])
        return {
            'respuesta': respuesta,
            'respuesta_msg': respuesta.content,
            'asis_funciones': respuesta.tool_calls
        }