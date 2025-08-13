import pandas as pd
#import numpy as np
#import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
#from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
#import json
#import re
import time
from unidecode import unidecode
from rapidfuzz import process, fuzz


# Libraries
# ==============================================================================
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

def crearModeloARIMA(): #Se ejecutara una sola vez
    ruta = "./consumo_estacional_semanal.csv"
    df_full = pd.read_csv(ruta, parse_dates=['fecha'], index_col=['fecha'])
    df_full.index.name = 'datetime'

    # Hacer un estudio para obtener order y seasonal_order iniciales
    order = (1, 1, 2)
    seasonal_order = (1, 1, 1, 14)

    # Fechas de inicio y fin del conjunto de evaluación | antes conjunto entrenamiento | después conjunto test
    fecha_fin = df_full.index.max() - pd.Timedelta(days=6)
    fecha_inicio = fecha_fin - pd.Timedelta(days=20)
    print(f"Eval fecha inicio: {fecha_inicio} ----> fecha fin: {fecha_fin}")

    # Crear conjuntos de entrenamiento y test
    df_full = df_full.copy()
    df_full.index = pd.date_range(start=df_full.index.min(), end=df_full.index.max(), freq='D') #Linea maldita

    y_comp = df_full.loc[:fecha_inicio].copy()
    test_comp = df_full.loc[fecha_inicio:fecha_fin].copy()

    y = y_comp[['consumo_energetico']].copy()
    exog = y_comp[['temperatura', 'evento_especial']].copy()
    test = test_comp[['consumo_energetico']].copy()
    exog_test = test_comp[['temperatura', 'evento_especial']].copy()

    # Proceso para encontrar los mejores hiperparámetros
    # ==============================================================================
    forecaster = ForecasterSarimax(
        regressor=Sarimax(order=order, seasonal_order=seasonal_order, maxiter=200)
    )

    param_grid = {
        'order': [(1, 1, 1), (1, 1, 2), (2, 1, 2)],
        'seasonal_order': [(1, 1, 1, 14), (1, 1, 0, 14), (0, 1, 1, 14)],
        'trend': [None, 'c']
    }

    cv = TimeSeriesFold(
        steps              = 14,
        initial_train_size = len(df_full.loc[:fecha_inicio, 'consumo_energetico']),
        refit              = False
    )

    results_grid = grid_search_sarimax(
        forecaster            = forecaster,
        y                     = df_full.loc[:, 'consumo_energetico'],
        exog                  = df_full.loc[:, ['temperatura', 'evento_especial']],
        param_grid            = param_grid,
        cv                    = cv,
        metric                = 'mean_absolute_error',
        return_best           = True,
        n_jobs                = 'auto',
        suppress_warnings_fit = True,
        verbose               = False,
        show_progress         = True
    )

    # ==============================================================================
    new_order = results_grid.iloc[0]['order']
    new_seasonal_order = results_grid.iloc[0]['seasonal_order']
    
    forecaster = ForecasterSarimax(
        regressor=Sarimax(order=new_order, seasonal_order=new_seasonal_order, maxiter=200)
    )

    forecaster.fit(y=df_full.loc[:fecha_fin-pd.Timedelta(days=2), 'consumo_energetico'],exog = df_full.loc[:fecha_fin-pd.Timedelta(days=2), ['temperatura', 'evento_especial']], suppress_warnings=True)

    prediccion = forecaster.regressor.sarimax_res.fittedvalues

    # Guardar el modelo
    joblib.dump(forecaster, 'modelo_sarimax_ambiente.pkl')

def entrenarModeloARIMA(nuevo_data_test): #Se ejecutara cada siete dias
    # Cargar el modelo
    forecaster = joblib.load('modelo_sarimax_ambiente.pkl')

    #forecaster.fit(y=df_full.loc[:fecha_fin-pd.Timedelta(days=2), 'consumo_energetico'],exog = df_full.loc[:fecha_fin-pd.Timedelta(days=2), ['temperatura', 'evento_especial']], suppress_warnings=True)

    prediccion = forecaster.regressor.sarimax_res.fittedvalues

    fechas_inicio_lw = prediccion.index.max() + pd.Timedelta(days=1)
    fechas_fin_lw = fechas_inicio_lw + pd.Timedelta(days=6)
    
    predictions = forecaster.predict(
        steps            = 14,
        exog             = nuevo_data_test[['temperatura', 'evento_especial']],
        last_window      = df_full.loc[fechas_inicio_lw:fechas_fin_lw, 'consumo_energetico'],
        last_window_exog = df_full.loc[fechas_inicio_lw:fechas_fin_lw, ['temperatura', 'evento_especial']]
    )

    # Guardar el modelo
    joblib.dump(forecaster, 'modelo_sarimax_ambiente.pkl')

def getPrediccionConsumoAnt1(nuevo_data_test): #Se ejecutara cada que el usuario solicite la prediccion
    # Cargar el modelo
    forecaster = joblib.load('modelo_sarimax_ambiente.pkl')

    fechas_inicio_lw = prediccion.index.max() + pd.Timedelta(days=1)
    fechas_fin_lw = fechas_inicio_lw + pd.Timedelta(days=6)
    
    predictions = forecaster.predict(
        steps            = 14,
        exog             = nuevo_data_test[['temperatura', 'evento_especial']],
        last_window      = df_full.loc[fechas_inicio_lw:fechas_fin_lw, 'consumo_energetico'],
        last_window_exog = df_full.loc[fechas_inicio_lw:fechas_fin_lw, ['temperatura', 'evento_especial']]
    )

    return predictions

*/

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
    tiempo_inicio = time.time()
    model_name = "Recognai/bert-base-spanish-wwm-cased-xnli"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)

    resultado = classifier(consulta, etiquetas, hypothesis_template="Que accion desea realizar el usuario con esta consulta: {}.")
    tiempo_fin = time.time()
    print(f"Tiempo de ejecución de la intención (BERT): {tiempo_fin - tiempo_inicio:.2f} segundos")
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