from openai import OpenAI
from ollama import Client
from flask import session
from funciones.asistente import getFuncionesAsistente, getMensajeSistema
import os
import random
import string

class AsistenteModelo():
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("API_GPT")
        )
        self.cliente = Client(
            host=os.environ.get("RUTA_IA"),
            headers={'x-some-header': 'some-value'}
        )
        #self.funciones = getFuncionesAsistente()
        #self.vector_store = self.getVectorDeArchivo('Catalogo edificios pisos y ambientes', ['objeto.json'])
        self.asistente = os.environ.get("MODELO_IA")
        #self.hilo = []
        self.run = None
        #self.valorPrueba = 1
        # self.run = self.client.beta.threads.runs.create_and_poll(
        #     thread_id=self.hilo.id, assistant_id=self.asistente.id
        # )

    def crearAsistente(self):
        #Subida del archivo
        funcionesAsistente = getFuncionesAsistente()

        thisTools = [{"type": "file_search"}] + funcionesAsistente

        asistente = self.client.beta.assistants.create(
            #name="Asistente de Consumo Energetico",
            #instructions=getMensajeSistema(),
            instructions="Eres un asistente de consumo energético y te encuentras operativo en el edificio de Humanística de la Universidad Técnica de Manabí. Tu trabajo será mostrar de manera gráfica el histórico del consumo energético tanto del ambiente como de todo el edificio en general. Tendrás que preguntarle al usuario qué edificio, piso y ambiente desea consultar para que puedas presentar la información respectiva. Tienes que basarte en la informacion del archivo json. Cuando el usuario te diga que quiere el consumo de energia del edificio, piso y ambiente, devolveras los identificadores de cada uno.",
            model="gpt-4o",
            tools=thisTools,
            tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
        )

        return asistente
    
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
        if tcFunciones and len(tcFunciones) > 0:
            session['hilo']['mensajes'].append(tcFunciones)
            print("Las herramientas fueron enviadas correctamente.")
        else:
            print("No hay herramientas para subir.")
    
    def enviarFuncionesGPT(self, tcFunciones, idRun, idHilo):
        if tcFunciones and len(tcFunciones) > 0:
            try:
                self.run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=idHilo,
                    run_id=idRun,
                    tool_outputs=tcFunciones
                )
                print("Las herramientas fueron enviadas correctamente.")
            except Exception as e:
                print("Fallo al enviar las herramientas:", e)
        else:
            print("No hay herramientas para subir.")

        if self.run.status == 'completed':
            messages = list(self.client.beta.threads.messages.list(thread_id=idHilo, run_id=idRun))
            #ejecucion = self.run
            return [self.run, messages]
        else:
            #ejecucion = self.run
            return [self.run, None]
    
    def getRespuesta(self):
        # /!\ Inicia Adaptacion para trabajo remoto sin apis /!\
        class respuesta_msg:
            # Crea una respuesta falsa que sea usable en el resto del sistema
            role = 'User'
            content = 'Hola esta es la respuesta generada por ollama'
            actual = 1; max = 1
            def __iter__(self): return self
            def __next__(self):
                if self.actual < self.max:
                    self.actual += 1
                    return [['role', self.role], ['content', self.content]]
                else:
                    raise StopIteration
        return {
            'respuesta': None,
            'respuesta_msg': respuesta_msg(),
            'asis_funciones': None
        }
        # /!\ Acaba Adaptacion para trabajo remoto sin apis /!\
        print(list(session.get('hilo')['mensajes']))
        response = self.cliente.chat(
            model = self.asistente,
            messages = list(session.get('hilo')['mensajes']),
            stream = False
            
        )
        """
            tools = [{
                "type": "function",
                "function": {
                    "name": "is_get_consumo",
                    "description": "Devuelve verdadero cuando el usuario quiere consultar datos de consumo energetico, caso contrario falso",
                    "strict": False,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "isconsumo": {
                                "type": "boolean",
                                "description": "verdadero cuando va a consultar datos energeticos, falso en caso contrario"
                            }
                        },
                        "required": ["isconsumo"]
                    }
                }
            }],
        """

        x = {
            'respuesta': response,
            'respuesta_msg': response.message if response and response.message else None,
            'asis_funciones': response.message.tool_calls if response and response.message.tool_calls else None
        }
        print(x)
        return x
    
    def getRespuestaGPT(self, threadId, mensaje):
        message = self.client.beta.threads.messages.create(
            thread_id=threadId,
            role="user",
            content=mensaje,
        )

        self.run = self.client.beta.threads.runs.create_and_poll(
            #thread_id=threadId, assistant_id=self.asistente.id
            thread_id=threadId, assistant_id=self.asistente
        )

        messages = list(self.client.beta.threads.messages.list(thread_id=self.hilo.id, run_id=self.run.id))
        return [self.run, messages]
    
    def getRespuestaAnt2(self, usuario, mensajes, compMsgs):
        tMensajes = mensajes
        for cm in compMsgs:
            if cm and cm['usuario'] == usuario: 
                tMensajes.insert(cm['lastId'], cm['data'])
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