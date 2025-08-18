# controlador_asistente.py
#from modelos.modelo_llm import stream_llm_tokens
from typing import Generator, List, Dict, Union
from funciones.asistente import getFuncionesAsistente, getPromptAsistentes
from modelos.asistente import AsistenteModelo
from controladores.chats import ChatsControlador
from flask import session
import json
import re
import os
from dotenv import load_dotenv
from decimal import Decimal

import requests

class AsistenteControlador():
    def __init__(self, app):
        self.modelo = AsistenteModelo()
        self.controladorChats = ChatsControlador(app)
        print("Asistente Controlador inicializado")

        self.model_name = "mistral:latest"
        # Base URL de la API LLM, p.ej. 'http://172.16.188.33:3003/api'
        self.base_url = os.environ.get('RUTA_IA', '').rstrip('/')

    
    def crearHilo(self):
        #Podria funcionar para crear el hilo con caracteres aleatorios
        #idHilo = self.modelo.crearHilo()

        #Identificador del hilo obtenido en la bd
        idHilo = self.controladorChats.crearHilo()
        return idHilo

    def getListaMensajesGPT(self, idHilo):
        listaMensajes = self.modelo.getListaMensajes(idHilo)
        print(listaMensajes)
        mensajes = [{
            "creado": m.created_at,
            "rol": m.role,
            "texto": m.content[0].text.value
        } for m in listaMensajes.data]

        return mensajes
        #x = [x if x==2 else 1 for x in listaMensajes]

    def reaccionarMensaje(self, hilo, idMensaje, reaccion):
        return self.controladorChats.reaccionarMensaje(hilo, idMensaje, reaccion)
    
    def getListaMensajes(self, hilo):
        return self.controladorChats.getListaMensajes(hilo)
    
    def getRespuesta(self, hilo, mensaje, intencion="pregunta_respuesta_general"):
        #intencion = session.get('intencion')
        res = self.controladorChats.enviarMensaje(hilo, mensaje)
        if res['ok']:
            historialMsgs = self.controladorChats.getHistorialMensajes(hilo)

            resultado = self.modelo.getRespuesta(historialMsgs, intencion)
            respuesta_msg = resultado
            #funciones = resultado['asis_funciones']
            
            res = ""
            if respuesta_msg:
                mensajeLimpio = self.eliminarPensamiento(respuesta_msg)
                #session['hilo']['mensajes'].append(dict(respuesta_msg))
                self.controladorChats.enviarMensaje(hilo, [mensajeLimpio])
                res = respuesta_msg
            
            """if funciones:
                obj_funciones = []
                for funcion in funciones:
                    #print(funcion.function.arguments)
                    argumentos = dict(funcion.function.arguments)
                    nombreFuncion = funcion.function.name
                    #session['hilo']['mensajes'].append({"role": "tool", "name":nombreFuncion, "content": json.dumps(argumentos)})
                    msgTool = {"role": "assistant", "tool_call": {"name":nombreFuncion, "arguments": json.dumps(argumentos)}}
                    self.controladorChats.enviarMensaje(hilo, dict(msgTool))
                    #json_args = json.loads(argumentos)
                    #print(argumentos)
                    
                    obj_funciones.append({
                        "funcion_name": nombreFuncion,
                        "funcion_args": argumentos,
                    })
                res["asis_funciones"] = obj_funciones"""
            
            print("Respuesta del asistente:")
            print(res)
            if (res != ""):
                return {
                    "ok": True,
                    "observacion": None,
                    "datos": str(res)
                }
            else:
                return {
                    "ok": False,
                    "observacion": "No se obtuvo una respuesta del asistente.",
                    "datos": str(res)
                }
        else:
            print("Error al hablar con el asistente.")
            return {
                "ok": False,
                "observacion": "Error al guardar el mensaje.",
                "datos": None
            }

    def getRespuestaGPT(self, threadId, mensaje):
        [run, messages] = self.modelo.getRespuestaGPT(threadId, mensaje)
        obj_funciones = []
        respuesta = {
            'asis_funciones': None,
            'id_run': None,
            'respuesta_msg': None
        }

        if run.required_action:
            print("Tool calls:")
            funciones = run.required_action.submit_tool_outputs.tool_calls
            print(funciones)

            if len(funciones) > 0:
                for funcion in funciones:
                    argumentos = json.loads(funcion.function.arguments)
                    obj_funciones.append(
                        {
                            "funcion_id": funcion.id,
                            "funcion_name": funcion.function.name,
                            "funcion_args": argumentos,
                        }
                    )
                
                respuesta['asis_funciones'] = obj_funciones
                respuesta['id_run'] = run.id

        if messages and len(messages) > 0:
            print("Contenido mensaje:")
            print(messages)
            message_content = messages[0].content[0].text
            rMensaje = self.limpiarMensajes(message_content)

            respuesta["respuesta_msg"] = rMensaje
        
        if ('asis_funciones' in respuesta and respuesta['asis_funciones']) or ('respuesta_msg' in respuesta  and respuesta['respuesta_msg']):
            return {
                'ok': True,
                'observacion': None,
                'datos': respuesta
            }
        else:
            return {
                'ok': False,
                'observacion': 'No se obtuvo respuesta',
                'datos': respuesta
            }
    
    def verificarConsumo(self, argumentos):
        [isconsumo] = argumentos.values()

        if isconsumo:
            # Consulta con el modelo json
            return { "success": True, "reason": "Esta tratando de obtener informacion de consumo energetico." , "info": {"esJSON": True}}
        else:
            return { "success": True, "reason": "Has retornado el valor correcto, continua con la conversacion", "info": None}


    def conversar(self, respuesta):
        pass

    def eliminarPensamiento(self, mensaje):
        #message_content = messages[0].content[0].text
        cleaned = ''
        if '<think>' in mensaje:
            cleaned = re.sub(r'<think>.*?</think>', '', mensaje, flags=re.DOTALL)
        else:
            cleaned = mensaje
        mensajeC = {'role': 'assistant', 'content': cleaned}
        return mensajeC
    
    def limpiarMensajes(self, message_content):
        #message_content = messages[0].content[0].text
        annotations = message_content.annotations
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, "")

        return message_content.value

    def enviarFunciones(self, idHilo, tcFunciones):
        if tcFunciones and len(tcFunciones) > 0:
            for tf in tcFunciones:
                #session['hilo']['mensajes'].append(tf)
                self.controladorChats.enviarMensaje(idHilo, tf)
            print("Las herramientas fueron enviadas correctamente.")
        else:
            print("No hay herramientas para subir.")
        #self.modelo.enviarFunciones(tcFunciones)
        historialMsgs = self.controladorChats.getHistorialMensajes(idHilo)

        respuesta = self.modelo.getRespuesta(historialMsgs)

        respuesta_msg = respuesta['respuesta_msg']
        funciones = respuesta['asis_funciones']
        
        res = {
            "respuesta_msg": "",
            "asis_funciones": None
        }
        #if respuesta_msg is not None:
        if respuesta_msg and respuesta_msg.content:
            #session['hilo']['mensajes'].append(dict(respuesta_msg))
            self.controladorChats.enviarMensaje(idHilo, dict(respuesta_msg))
            res['respuesta_msg'] = respuesta_msg.content
        
        if funciones:
            obj_funciones = []
            for funcion in funciones:
                #print(funcion.function.arguments)
                argumentos = dict(funcion.function.arguments)
                nombreFuncion = funcion.function.name
                #session['hilo']['mensajes'].append({"role": "tool", "name":nombreFuncion, "content": json.dumps(argumentos)})
                msgTool = {"role": "tool", "name":nombreFuncion, "content": json.dumps(argumentos)}
                self.controladorChats.enviarMensaje(idHilo, dict(msgTool))
                #json_args = json.loads(argumentos)
                #print(argumentos)
                
                obj_funciones.append({
                    #"funcion_id": funcion.id,
                    "funcion_name": funcion.function.name,
                    "funcion_args": argumentos,
                })
            
            res["asis_funciones"] = obj_funciones
        
        if (respuesta_msg and res['respuesta_msg']) or (funciones and res["asis_funciones"]):
            return {
                "ok": True,
                "observacion": None,
                "datos": dict(res)
            }
        else:
            return {
                "ok": False,
                "observacion": "No se obtuvo una respuesta del asistente.",
                "datos": dict(res)
            }

    def enviarFuncionesGPT(self, tcFunciones, idRun, idHilo):
        [run, messages] = respuesta = self.modelo.enviarFuncionesGPT(tcFunciones, idRun, idHilo)

        obj_funciones = []
        respuesta = {
            'asis_funciones': None,
            'id_run': None,
            'respuesta_msg': None
        }
        if run and run.required_action:
            print("Tool calls:")
            funciones = run.required_action.submit_tool_outputs.tool_calls
            print(funciones)

            if len(funciones) > 0:
                for funcion in funciones:
                    argumentos = json.loads(funcion.function.arguments)
                    obj_funciones.append(
                        {
                            "funcion_id": funcion.id,
                            "funcion_name": funcion.function.name,
                            "funcion_args": argumentos,
                        }
                    )
                
                respuesta['asis_funciones'] = obj_funciones
                respuesta['id_run'] = run.id

        if messages and len(messages) > 0:
            print("Contenido mensaje:")
            print(messages)
            message_content = messages[0].content[0].text
            print(message_content.value)
            respuesta["respuesta_msg"] = message_content.value
        
        
        if respuesta['asis_funciones'] or respuesta["respuesta_msg"]:
            return {
                'ok': True,
                'observacion': None,
                'datos': respuesta
            }
        else:
            return {
                'ok': False,
                'observacion': 'No se obtuvo respuesta',
                'datos': respuesta
            }
        #return respuesta

    def getRespuestaAnt(self, usuario, mensajes, compMsgs):
        respuesta = self.modelo.getRespuesta(usuario, mensajes, compMsgs)
        respuesta_msg = respuesta['respuesta_msg']
        funciones = respuesta['asis_funciones']

        mensajes = list(map(lambda c: str(c) if not type(c) is dict else c, mensajes))
        if funciones:
            obj_funciones = []
            for funcion in funciones:
                argumentos = json.loads(funcion.function.arguments)
                obj_funciones.append(
                    {
                        "funcion_id": funcion.id,
                        "funcion_name": funcion.function.name,
                        "funcion_args": argumentos,
                    }
                )
            return {
                "almacenar_msg": mensajes,
                "mensaje": respuesta['respuesta'],
                "respuesta_msg": respuesta_msg,
                "asis_funciones": obj_funciones
            }
        else:
            return {
                "almacenar_msg": mensajes,
                "mensaje": None,
                "respuesta_msg": respuesta_msg,
                "asis_funciones": None
            }
        
    def stream_tokens(
        self,
        hilo: str,
        tipo: str,
        mensajes: Union[str, List[Dict[str, str]]],
        intencion: str = 'ninguna',
        contenidoInfo = None
    ) -> Generator[str, None, None]:
        print("Mensajes recibidos antes de la respuesta:")
        print(mensajes)
        print("Intencion del mensaje antes de la respuesta:")
        print(intencion)
        print("Contenido en sesion:")
        print(contenidoInfo)
        successProceso = mensajes[-1].pop("ok")
        #if not successProceso: res = self.controladorChats.enviarMensaje(hilo, mensajes)
        if True: #res['ok']:
            if tipo == "inicializar":
                historialMsgs = self.controladorChats.getPrompoMensajeBienvenida(hilo)
            else:
                if successProceso:
                    if intencion == 'solicita_datos_consumo':
                        historialMsgs = [
                            {"role": "system", "content": getPromptAsistentes('prediccion')}
                        ] + mensajes
                        print(historialMsgs)
                    elif intencion == 'solicita_prediccion':
                        parametros = [item for item in contenidoInfo if item["nombre"] == "solicita_datos_consumo"]
                        var_adicional = None
                        if parametros and len(parametros) > 0:
                            var_adicional = parametros[-1]['valor']

                        historialMsgs = getPromptAsistentes('solicita_datos_consumo', var_adicional)
                        #historialMsgs = self.controladorChats.getHistorialMensajesConsumo(hilo)
                    else:
                        historialMsgs = self.controladorChats.getHistorialMensajes(hilo)
                else:
                    #Personalizar con mensaje de error de retroalimentacion
                    historialMsgs = [
                        {"role": "system", "content": getPromptAsistentes('error_proceso')}
                    ] + mensajes
                    print("Error en el proceso, se notifica al usuario.")
                    print(historialMsgs)
            
            # Construir prompt como texto si recibimos lista de mensajes
            if isinstance(historialMsgs, list):
                prompt_text = "\n".join(
                    f"{m['role']}: {m['content']}" for m in historialMsgs
                )
            else:
                prompt_text = str(historialMsgs)
            
            # Delegar streaming de tokens al modelo
            yield from self.modelo.stream_llm(prompt_text)

        else:
            print("Error al hablar con el asistente.")
            return {
                "ok": False,
                "observacion": "Error al guardar el mensaje.",
                "datos": None
            }

    def text_to_speech(self, text: str) -> str:
        
        payload = {'texto': text}
        
        #if hilo_id is not None:
        #    payload['id'] = hilo_id

        try:
            resp = requests.post(
                url=os.environ.get("RUTA_VOZ")+'/texto_voz',
                data=payload,
                verify=False,
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json().get('datos', {})
            return result.get('voice_encoded', '') or ''
        except Exception as e:
            # En caso de error, loguear y retornar cadena vacía
            print(f"[TTS ERROR] Llamada API fallida: {e}")
            return ''
        
    def speech_to_text(self, voice_file, codigo):
        
        """
        Envía el audio crudo al servicio de STT sin escribir a disco.
        voice_file: request.files['voice']
        codigo: identificador de hilo/sesión
        Retorna: dict con la respuesta del servicio STT (esperado: {'ok', 'datos', 'observacion'})
        """
        #voice_file.save('./prueba.mp3')
        if voice_file is None:
            return {'ok': False, 'datos': None, 'observacion': 'No se recibió archivo de audio.'}

        # Leemos todo el contenido en memoria
        audio_bytes = voice_file.read()
        if not audio_bytes:
            return {'ok': False, 'datos': None, 'observacion': 'El archivo de audio está vacío.'}

        # Lo enviamos sin grabar a disco:
        try:
            resp = requests.post(
                url=f"{os.environ['RUTA_VOZ']}/voz_texto",
                files={
                    'voice': (
                        getattr(voice_file, 'filename', 'audio.webm'),  # nombre
                        audio_bytes,                                   # contenido
                        getattr(voice_file, 'mimetype', 'application/octet-stream')  # mimetype
                    )
                },
                data={'id': codigo},
                headers={
                    'X-Request-ID': str(codigo),
                    'Accept': 'application/json'
                },
                verify=False
            )

            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'ok': False, 'datos': None, 'observacion': f'Error al llamar STT: {e}'}
    