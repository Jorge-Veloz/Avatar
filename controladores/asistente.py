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

        if messages and len(messages) > 0:
            print("Contenido mensaje:")
            print(messages)
            message_content = messages[0].content[0].text
            print(message_content.value)
        
        respuesta_msg = respuesta['respuesta_msg']
        funciones = respuesta['asis_funciones']

        mensajes = list(map(lambda c: str(c) if not type(c) is dict else c, mensajes))
        if funciones:
            obj_funciones = [];
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
    
    def getRespuestaAnt(self, usuario, mensajes, compMsgs):
        respuesta = self.modelo.getRespuesta(usuario, mensajes, compMsgs)
        respuesta_msg = respuesta['respuesta_msg']
        funciones = respuesta['asis_funciones']

        mensajes = list(map(lambda c: str(c) if not type(c) is dict else c, mensajes))
        if funciones:
            obj_funciones = [];
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