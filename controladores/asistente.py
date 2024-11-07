from modelos.asistente import AsistenteModelo
import json

class AsistenteControlador():
    def __init__(self):
        self.modelo = AsistenteModelo()
       
    def getRespuesta(self, usuario, mensajes, compMsgs):
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