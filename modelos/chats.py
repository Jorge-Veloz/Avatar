from funciones.asistente import getMensajeSistema
from db.db import PostgresDB

class ChatsModelo:
    def __init__(self, app):
        self.db = PostgresDB(app)
        #self.db.app = None  # Asignar la aplicación a la instancia de PostgresDB
    
    def getIdHilo(self):
        # Aqui se obtendra el identificador de la bd dependiendo del usuario que ingrese
        idHilo = 1
        return idHilo
    
    def getMensajeSistema(self):
        # Aqui se obtendra el mensaje del rol del asistente predefinido por ahora hasta que se integre a la bd
        mensajeSistema = getMensajeSistema()
        return mensajeSistema
    
    def getListaMensajes(self, idHilo):
        # Aqui se obtendra el historial de mensajes de la bd
        sql = f"SELECT datos, creado, id, reaccion FROM asistentes.vmostrarhistorialinteracciones_ia WHERE idusuario = {idHilo} ORDER BY id ASC"
        #resultado = self.db.llamarFuncion('SELECT * FROM asistentes.vmostrarhistorialiteracciones_ia (%s, %s, %s)', (accion, mensaje, idHilo))
        mensajes = self.db.consultarDatos(sql)
        return mensajes
    
    def getHistorialMensajes(self, idHilo):
        # Aqui se obtendra el historial de mensajes de la bd
        sql = f"SELECT datos FROM asistentes.vmostrarhistorialinteracciones_ia WHERE idusuario = {idHilo} AND (reaccion IS NULL OR reaccion = 1) ORDER BY id ASC"
        #resultado = self.db.llamarFuncion('SELECT * FROM asistentes.vmostrarhistorialiteracciones_ia (%s, %s, %s)', (accion, mensaje, idHilo))
        mensajes = self.db.consultarDatos(sql)
        return mensajes
    
    def getHistorialMensajes2(self, idHilo):
        # Aqui se obtendra el historial de mensajes de la bd
        sql = f"SELECT datos FROM asistentes.vmostrarhistorialinteracciones_ia2 WHERE idusuario = {idHilo} AND (reaccion IS NULL OR reaccion = 1) ORDER BY id ASC"
        #resultado = self.db.llamarFuncion('SELECT * FROM asistentes.vmostrarhistorialiteracciones_ia (%s, %s, %s)', (accion, mensaje, idHilo))
        mensajes = self.db.consultarDatos(sql)
        return mensajes

    def enviarMensaje(self, idHilo, mensaje):
        # Aqui se guardara el mensaje en la bd
        accion = "registrar"
        resultado = self.db.llamarFuncion('SELECT * FROM asistentes.actualizarHistorialInteraccionesIA(%s, %s, %s)', (accion, mensaje, str(idHilo)))
        #resultado = self.db.llamarFuncion('asistentes.actualizarHistorialInteraccionesIA', (accion, mensaje, idHilo))
        return resultado
        #sql = f"INSERT INTO asistentes.vmostrarhistorial (id_hilo, mensaje) VALUES ('{idHilo}', '{mensaje}')"
        #self.db.insertarDatos(sql)

    def reaccionarMensaje(self, idHilo, idMensaje, reaccion):
        # Se actualizara el mensaje con like o dislike en la bd
        accion = "modificar"
        resultado = self.db.llamarFuncion('SELECT * FROM asistentes.actualizarReaccionesMensajesIA(%s, %s, %s, %s)', (accion, str(idMensaje), str(reaccion), str(idHilo)))
        return resultado

    def probarConexion(self):
        return self.db.probarConexion()