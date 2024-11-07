import mysql.connector
import os
from dotenv import load_dotenv

class db():
    def __init__(self):
        rutaActual = os.getcwd()
        load_dotenv(os.path.join(rutaActual, '.env'))
        config = {
            'user': os.getenv("MYSQL_USER"),
            'password': os.getenv("MYSQL_PASSWORD"),
            'host': os.getenv("MYSQL_HOST"),
            'port': int(os.getenv("MYSQL_PORT")),
            'database': os.getenv("MYSQL_DB")
        }
        self.mysql = mysql.connector.connect(**config)
    
    def consultarDato(self, sql):
        cursor = self.mysql.cursor(dictionary=True)

        cursor.execute(sql)
        data = cursor.fetchone()
        if(data != None and len(data) > 0):
            return data
        else:
            return None

    def consultarDatos(self, sql):
        cursor = self.mysql.cursor(dictionary=True)

        cursor.execute(sql)
        data = cursor.fetchall()
        if(len(data) > 0):
            return data
        else:
            return None
    
    def insertarDatos(self, sql, data, devolucion=0):
        cursor = self.mysql.cursor()
        cursor.execute(sql, data)
        idRow = cursor.lastrowid

        respuesta = None
        if devolucion:
            if idRow:
                respuesta = {'res': 1, 'id': idRow}
            else:
                respuesta = {'res': 0, 'id': 0}

        else:
            respuesta = 1 if idRow else 0
            
        self.mysql.commit()
        cursor.close()
        return respuesta
    
    def actualizarDatos(self, sql, data):
        cursor = self.mysql.cursor()
        cursor.execute(sql, data)
        self.mysql.commit()
        filasAct = cursor.rowcount
        
        respuesta = None
        if filasAct > 0:
            respuesta = 1
        else:
            respuesta = 0
            
        cursor.close()
        return respuesta