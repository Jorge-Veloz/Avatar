import mysql.connector
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

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
    
class PostgresDB():
    def __init__(self, app):
        self.app = app
        self.connection = psycopg2.connect(
            dbname=os.getenv("PG_DB"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
        self.connection.autocommit = True
        conexion = self.probarConexion()
        print(conexion)

    def probarConexion(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"status": "success", "message": "Conexión exitosa"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    def consultarDato(self, sql, params=None):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchone()
            return data if data else None

    def consultarDatos(self, sql, params=None):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchall()
            return data if data else None

    def insertarDatos(self, sql, params=None, devolucion=False):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            idRow = cursor.fetchone()[0] if devolucion else None
            return {'res': 1, 'id': idRow} if devolucion else 1

    def actualizarDatos(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            filasAct = cursor.rowcount
            return 1 if filasAct > 0 else 0

    def eliminarDatos(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            filasElim = cursor.rowcount
            return 1 if filasElim > 0 else 0
    
    def llamarFuncion(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            resultados = cursor.fetchall()
            return resultados if resultados else None