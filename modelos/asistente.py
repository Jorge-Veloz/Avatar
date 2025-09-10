#from openai import OpenAI
from ollama import Client
from flask import session
from funciones.asistente import getFuncionesAsistente, getPromptAsistentes
import os
import random
import string

from typing import Generator
import httpx
import json


class AsistenteModelo():
    def __init__(self):
        self.client = None
        
        self.cliente = Client(
            host=os.environ.get("RUTA_IA"),
            headers={'x-some-header': 'some-value'},
            timeout=300
        )
        #self.funciones = getFuncionesAsistente()
        #self.vector_store = self.getVectorDeArchivo('Catalogo edificios pisos y ambientes', ['objeto.json'])
        self.asistente = os.environ.get("MODELO_IA")
        
        self.model_name = self.asistente
        base = os.environ.get('RUTA_IA', '').rstrip('/')
        self.api_url = f"{base}/api/generate"

        #self.hilo = []
        self.run = None
        #self.valorPrueba = 1
        # self.run = self.client.beta.threads.runs.create_and_poll(
        #     thread_id=self.hilo.id, assistant_id=self.asistente.id
        # )

    
    def getVectorDeArchivo(self, nombre, archivos):
        vector_store = self.client.vector_stores.create(
            name=nombre
        )
        file_paths = archivos
        file_streams = [open(path, "rb") for path in file_paths]

        file_batch = self.client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams
        )

        return vector_store

    def getListaMensajes(self, idHilo):
        return self.client.beta.threads.messages.list(idHilo)

    def crearHilo(self):
        #Aqui se creara el hilo en la bd y se obtendra el identificador
        caracteres = string.ascii_letters + string.digits  # Letras y números
        return ''.join(random.choice(caracteres) for _ in range(20))
        #hilo = []
        #return hilo
    
    def crearHiloAnt(self):
        self.hilo = self.client.beta.threads.create()
        return self.hilo

    def enviarFunciones(self, tcFunciones):
        pass
    
    
    def getRespuesta(self, mensajes, intencion="pregunta_respuesta_general"):
        #print(list(session.get('hilo')['mensajes']))

        respuesta = None
        if intencion == "pregunta_respuesta_general":
            response = self.cliente.chat(
                model = self.asistente, #self.asistente,
                #messages = list(session.get('hilo')['mensajes']),
                messages = mensajes,
                stream = False
            )
            respuesta = response.message.content
        else:
            parametros = [item for item in session.get('contenido') if item["nombre"] == intencion]
            var_adicional = None
            if parametros and len(parametros) > 0:
                var_adicional = parametros[-1]['valor']
                
            print("Parametros de contenido en sesion:")
            print(parametros)
            prompt = getPromptAsistentes(intencion, var_adicional)
            print("Prompt enviado:")
            print(prompt)
            response = self.cliente.generate(
                model = self.asistente, #self.asistente,
                prompt = prompt,
                stream = False
            )
            respuesta = response.response
        print("Respuesta obtenida:")
        print(respuesta)
        # x = {
        #     'respuesta': response,
        #     'respuesta_msg': response.message if response and response.message else None,
        #     #'asis_funciones': response.message.tool_calls if response and response.message.tool_calls else None
        # }
        # print("Respuesta obtenida:")
        # print(x)
        return respuesta
    
    
    def stream_llm(self, prompt_text: str) -> Generator[str, None, None]:
        """
        Envía el prompt_text al endpoint LLM en streaming y yield-ea tokens.
        """
        headers = {'Content-Type': 'application/json'}
        payload = {'model': self.model_name, 'prompt': prompt_text, 'stream': True}

        with httpx.Client(timeout=None) as client:
            with client.stream('POST', self.api_url, headers=headers, json=payload) as resp:
                
                resp.raise_for_status()
                
                for raw in resp.iter_lines():
                    # Puede venir como bytes o str
                    if isinstance(raw, (bytes, bytearray)):
                        text = raw.decode('utf-8', errors='ignore').strip()
                    else:
                        text = raw.strip()
                    if not text:
                        continue
                    try:
                        pkt = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    token = pkt.get('token') or pkt.get('response', '')
                    if token:
                        yield token