from modelos.asistente import AsistenteModelo
import json

class AsistenteControlador():
    def __init__(self):
        self.modelo = AsistenteModelo()

    def crearHilo(self):
        hilo = self.modelo.crearHilo()
        return hilo.id
    
    def getListaMensajes(self, idHilo):
        listaMensajes = self.modelo.getListaMensajes(idHilo)
        print(listaMensajes)
        mensajes = [{
            "creado": m.created_at,
            "rol": m.role,
            "texto": m.content[0].text.value
        } for m in listaMensajes.data]

        return mensajes
        #x = [x if x==2 else 1 for x in listaMensajes]

    def getRespuesta(self, threadId, mensaje):
        [run, messages] = self.modelo.getRespuesta(threadId, mensaje)
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
    
    def limpiarMensajes(self, message_content):
        #message_content = messages[0].content[0].text
        annotations = message_content.annotations
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, "")

        return message_content.value

    def enviarFunciones(self, tcFunciones, idRun, idHilo):
        [run, messages] = respuesta = self.modelo.enviarFunciones(tcFunciones, idRun, idHilo)

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