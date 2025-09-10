from db.db import db
import pandas as pd

class ConsumoModelo:
    def __init__(self):
        self.db = db()

    def getConsumoActual(self, edificio, ambiente, fecha):
        #sql = f"SELECT * FROM consumo_energetico WHERE ID_Edificio = '{edificio}' AND Cod_Ambiente='{ambiente}' AND Fecha >= '{fecha}' ORDER BY Fecha";
        sql = f"SELECT DATE_FORMAT(Fecha, '%Y-%m') AS Mes, ROUND(SUM(Consumo), 2) AS Consumo_Mensual FROM consumo_energetico WHERE ID_Edificio = '{edificio}' AND Cod_Ambiente='{ambiente}' AND Fecha >= '{fecha}' GROUP BY Mes ORDER BY Mes;";
        datos = self.db.consultarDatos(sql)

        if datos and len(datos) > 0:
            return datos
        else:
            return None
        
    def getConsumoActualTotal(self, edificio, fecha):
        #sql = f"SELECT * FROM consumo_energetico WHERE ID_Edificio = '{edificio}' AND Cod_Ambiente='{ambiente}' AND Fecha >= '{fecha}' ORDER BY Fecha";
        sql = f"SELECT DATE_FORMAT(Fecha, '%Y-%m') AS Mes, ROUND(SUM(Consumo), 2) AS Consumo_Mensual FROM consumo_energetico WHERE ID_Edificio = '{edificio}' AND Fecha >= '{fecha}' GROUP BY Mes ORDER BY Mes;";
        datos = self.db.consultarDatos(sql)

        if datos and len(datos) > 0:
            return datos
        else:
            return None
    
    def getConsumoFuturo(self, datosConsumo):
        df = pd.DataFrame(datosConsumo)

        # Aumentar el consumo en un 20%
        df['Consumo_Mensual'] = df['Consumo_Mensual'] * 1.2

        # Convertir la columna 'Mes' a tipo datetime y agregar un año
        df['Mes'] = pd.to_datetime(df['Mes'], format='%Y-%m') + pd.DateOffset(years=1)
        df['Mes'] = df['Mes'].dt.strftime('%Y-%m')

        return df.to_dict(orient='records')