import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
def getPrediccionConsumo(datos):
    df = pd.DataFrame(datos)
    
    df = df.rename(columns={'x': 'fecha', 'y': 'kilovatio'})

    # Asegúrate de que la columna 'fecha' sea de tipo datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['kilovatio'] = pd.to_numeric(df['kilovatio'])
    df['totalKilovatioEdificio'] = pd.to_numeric(df['totalKilovatioEdificio'])

    # Ordenar los datos por fecha, si no están ordenados
    df = df.sort_values('fecha')

    # Mostrar las primeras filas para verificar
    print(df.head())

    # Configurar la columna 'consumo' como la serie temporal
    y = df['kilovatio']

    # Ajustar el modelo ARIMA (p=1, d=1, q=1 es un buen punto de partida)
    model = ARIMA(y, order=(1, 1, 1))
    model_fit = model.fit()

    # Configurar la columna 'consumo' como la serie temporal
    y1 = df['totalKilovatioEdificio']

    # Ajustar el modelo ARIMA (p=1, d=1, q=1 es un buen punto de partida)
    model1 = ARIMA(y1, order=(1, 1, 1))
    model_fit1 = model1.fit()

    # Realizar la predicción para el día siguiente
    forecast_steps = 30
    forecast = model_fit.forecast(steps=forecast_steps)
    forecast1 = model_fit1.forecast(steps=forecast_steps)


    # Generar las fechas para los próximos 30 días
    last_date = df['fecha'].max()
    forecast_dates = pd.date_range(start=last_date, periods=forecast_steps + 1, freq='D')[1:]

    # Crear un DataFrame con las predicciones futuras
    forecast_df = pd.DataFrame({'fecha': forecast_dates, 'consumo_predicho': forecast, 'consumo_total': forecast1})
    forecast_df['fecha'] = forecast_df['fecha'].dt.strftime('%Y-%m-%d')

    resultado = forecast_df.to_dict(orient='records')
    return resultado


    #Hacerlo por semana
    #Que antes de hacer la prediccion el asistente pregunte a cuanto tiempo se quiere predecir
    # Y que te pregunte si habra un evento especial en la semana