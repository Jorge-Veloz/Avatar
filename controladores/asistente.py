from modelos.asistente import AsistenteModelo
from controladores.chats import ChatsControlador
from flask import session
import json

class AsistenteControlador():
    def __init__(self, app):
        self.modelo = AsistenteModelo()
        self.controladorChats = ChatsControlador(app)
        print("Asistente Controlador inicializado")

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
    
    def getRespuesta(self, hilo, mensaje):
        res = self.controladorChats.enviarMensaje(hilo, mensaje)
        if res['ok']:
            historialMsgs = self.controladorChats.getHistorialMensajes(hilo)

            resultado = self.modelo.getRespuesta(historialMsgs)
            respuesta_msg = resultado['respuesta_msg']
            #funciones = resultado['asis_funciones']
            
            res = ""
            if respuesta_msg and respuesta_msg.content:
                #session['hilo']['mensajes'].append(dict(respuesta_msg))
                self.controladorChats.enviarMensaje(hilo, [dict(respuesta_msg)])
                res = respuesta_msg.content
            
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
            
            print("RESpuses aflsakfs")
            print(respuesta_msg)
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