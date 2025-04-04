from modelos.asistente import AsistenteModelo
import json

class AsistenteControlador():
    def __init__(self):
        self.modelo = AsistenteModelo()

    def crearHilo(self):
        return self.modelo.crearHilo()
       
    def getRespuesta(self, threadId, mensaje):
        [run, messages] = self.modelo.getRespuesta(threadId, mensaje)
        
        obj_funciones = []
        respuesta = {}
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
            else:
                respuesta['asis_funciones'] = None
                respuesta['id_run'] = None

        if messages and len(messages) > 0:
            print("Contenido mensaje:")
            print(messages)
            message_content = messages[0].content[0].text
            print(message_content.value)
            respuesta["respuesta_msg"] = message_content.value
        else:
            respuesta["respuesta_msg"] = None
        
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
    
    def enviarFunciones(self, tcFunciones, idRun, idHilo):
        [run, messages] = respuesta = self.modelo.enviarFunciones(tcFunciones, idRun, idHilo)

        obj_funciones = []
        respuesta = {}
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
            else:
                respuesta['asis_funciones'] = None
                respuesta['id_run'] = None

        if messages and len(messages) > 0:
            print("Contenido mensaje:")
            print(messages)
            message_content = messages[0].content[0].text
            print(message_content.value)
            respuesta["respuesta_msg"] = message_content.value
        else:
            respuesta["respuesta_msg"] = None
        
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