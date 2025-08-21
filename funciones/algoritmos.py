import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import time
from unidecode import unidecode
from rapidfuzz import process, fuzz

import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error
from skforecast.datasets import fetch_dataset
from skforecast.sarimax import Sarimax
from skforecast.recursive import ForecasterSarimax
from skforecast.model_selection import TimeSeriesFold, backtesting_sarimax, grid_search_sarimax
from skforecast.plot import set_dark_theme
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
warnings.filterwarnings('ignore')
import joblib
import re
from datetime import date, datetime, timedelta
import numpy as np

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
    forecast_steps = 7
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

def getPrediccionConsumoAnt(datos):
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

def detectar_intencion(consulta, etiquetas):
    print("Paso #2: Detección de la intención de la consulta del usuario.")
    tiempo_inicio_intencion = time.time()
    model_name = "Recognai/bert-base-spanish-wwm-cased-xnli"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)

    resultado = classifier(consulta, etiquetas, hypothesis_template="Que accion desea realizar el usuario con esta consulta: {}.")
    tiempo_fin_intencion = time.time()
    print(f"Tiempo de ejecución de la intención (BERT): {tiempo_fin_intencion - tiempo_inicio_intencion:.2f} segundos")
    # Tomamos la etiqueta con mayor score
    mejor_intencion = resultado["labels"][0]
    print(f"Resultado de la intención: {mejor_intencion}")
    return {
        "intencion": mejor_intencion,
        "confianza": round(resultado["scores"][0], 3)
    }

def norm(s: str) -> str:
    return unidecode(s.lower().strip())

def fuzzy_lookup(name: str, items: list, key='nombre', threshold=80):
    choices = [norm(item[key]) for item in items]
    match = process.extractOne(name, choices, scorer=fuzz.QRatio) #.partial_ratio
    if match and match[1] >= threshold:
        return items[choices.index(match[0])]
    return None