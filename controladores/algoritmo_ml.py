from modelos.algoritmo_ml import AlgoritmoMLModelo
from funciones.funciones import completarDias
from datetime import timedelta
import re
import pandas as pd
import numpy as np

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

class AlgoritmoMLControlador():
    def __init__(self):
        self.modelo = AlgoritmoMLModelo()
    
    def generarDF(self, respuesta_llm, f_inicio):
        patron = r'DÍA:\s*(\w+)\s*\|\s*TIPO:\s*(\w+)'
        resultados = re.findall(patron, respuesta_llm)
        dias_llm_ordenada, fecha_inicio = completarDias(resultados, pd.to_datetime(f_inicio))

        # === Construir el DataFrame ===
        data = []

        for i, (dia, tipo) in enumerate(dias_llm_ordenada):
            fecha = fecha_inicio + timedelta(days=i)
            data.append({
                'fecha': fecha,
                'feriado': 1 if tipo.lower() == 'feriado' else 0,
                'evento_especial': 1 if tipo.lower() == 'especial' else 0
            })
        
        fechas = pd.date_range(start=data[0]['fecha'], end=data[-1]['fecha'], freq="D")
        col_temp = np.random.uniform(np.float64(19.42430644731337), np.float64(30.47436405875521), len(fechas)).astype(np.float64)
        df = pd.DataFrame({
            'feriado': [item['feriado'] for item in data],
            'evento_especial': [item['evento_especial'] for item in data],
            'total_temperatura': col_temp
        }, index=fechas)
        #df = pd.DataFrame(data)
        #df['fecha'] = pd.to_datetime(df['fecha'])
        # Establecer como índice y asegurar frecuencia diaria
        #df.set_index('fecha', inplace=True)
        
        return df
    
    def encontrarHiperparametros(self, df_full, fecha_inicio_eval):
        # Proceso para encontrar los mejores hiperparámetros
        # ==============================================================================
        order = (1, 1, 2) #Podrian cambiarse
        seasonal_order = (1, 1, 1, 14) #Podrian cambiarse

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
            initial_train_size = len(df_full.loc[:fecha_inicio_eval, 'total_kilovatio']),
            refit              = False
        )

        results_grid = grid_search_sarimax(
            forecaster            = forecaster,
            y                     = df_full.loc[:, 'total_kilovatio'],
            exog                  = df_full.loc[:, ['feriado', 'evento_especial', 'total_temperatura']],
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

        return forecaster, results_grid
    
    def predecirConsumo(self, df_full, nuevo_data_test, fechas_prediccion):
        lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva = fechas_prediccion

        #df_full = pd.read_json(ruta_data)
        df_full['fecha'] = pd.to_datetime(df_full['fecha'])
        df_full.set_index('fecha', inplace=True)      
        df_full.index.name = 'datetime'
        df_full = df_full.sort_index()

        df_full = df_full[['total_kilovatio', 'feriado', 'evento_especial', 'total_temperatura']]

        # Se comienza a evaluar desde el 16 de mayo donde empiezan valores veridicos
        fecha_inicio = pd.to_datetime('2025-05-16')
        df_full = df_full.loc[fecha_inicio:]

        # Asegurar que el índice tiene tipo correcto para entrenar
        df_full = df_full.copy()

        # Quitar duplicados o agregarlos
        df_full = df_full.groupby(df_full.index).sum()

        fechas_completas = pd.date_range(start=df_full.index.min(), end=df_full.index.max(), freq='D') #Linea maldita
        df_full = df_full.reindex(fechas_completas)

        # Calcular valores para rellenar
        promedio_kilovatio = df_full["total_kilovatio"].mean()
        promedio_temperatura = df_full["total_temperatura"].mean()
        moda_feriado = df_full["feriado"].mode()[0]  # mode() devuelve una Serie
        moda_evento = df_full["evento_especial"].mode()[0]  # mode() devuelve una Serie

        # Rellenar
        df_full["total_kilovatio"] = df_full["total_kilovatio"].fillna(promedio_kilovatio)
        df_full["total_temperatura"] = df_full["total_temperatura"].fillna(promedio_temperatura)
        df_full["feriado"] = df_full["feriado"].fillna(moda_feriado)
        df_full["evento_especial"] = df_full["evento_especial"].fillna(moda_evento)

        # Cortes de fechas lastwindow y evaluacion
        fechas_fin_lw = lunes_semana_actual - pd.Timedelta(days=1)
        fechas_inicio_lw = fechas_fin_lw - pd.Timedelta(days=6)

        fecha_fin_eval = pd.to_datetime(fechas_inicio_lw - pd.Timedelta(days=1))
        fecha_inicio_eval = fecha_fin_eval - pd.Timedelta(days=13)
        print(f"Eval fecha inicio: {fecha_inicio_eval} ----> fecha fin: {fecha_fin_eval}")

        # Dividir los datos en entrenamiento y evaluación
        y_comp = df_full.loc[:fecha_inicio_eval].copy()
        test_comp = df_full.loc[fecha_inicio_eval:fecha_fin_eval].copy()

        y = y_comp[['total_kilovatio']].copy()
        exog = y_comp[['feriado', 'evento_especial', 'total_temperatura']].copy()
        test = test_comp[['total_kilovatio']].copy()
        exog_test = test_comp[['feriado', 'evento_especial', 'total_temperatura']].copy()

        # Encontrar en la base de datos
        new_order = (2, 1, 1)
        new_seasonal_order = (0, 1, 1, 14)

        forecaster = ForecasterSarimax(
            regressor=Sarimax(order=new_order, seasonal_order=new_seasonal_order, maxiter=200)
        )

        forecaster.fit(y=df_full.loc[:fecha_fin_eval, 'total_kilovatio'],exog = df_full.loc[:fecha_fin_eval, ['feriado', 'evento_especial', 'total_temperatura']], suppress_warnings=True)

        prediccion = forecaster.regressor.sarimax_res.fittedvalues

        try:
            predictions = forecaster.predict(
                steps            = 14,
                exog             = nuevo_data_test[['feriado', 'evento_especial', 'total_temperatura']],
                last_window      = df_full.loc[fechas_inicio_lw:fechas_fin_lw, 'total_kilovatio'],
                last_window_exog = df_full.loc[fechas_inicio_lw:fechas_fin_lw, ['feriado', 'evento_especial', 'total_temperatura']]
            )
        except Exception as e:
            print("Ocurrio un error al momento de procesar la prediccion: " + e)
            return None
        
        # Asegurar que las fechas de predicción están en el índice
        forecast_dates = pd.date_range(start=predictions.index.min(), end=predictions.index.max(), freq='D')

        # Crear un DataFrame con las predicciones futuras
        forecast_df = pd.DataFrame({'fecha': forecast_dates, 'consumo_predicho': list(predictions.to_dict().values())})
        forecast_df['fecha'] = forecast_df['fecha'].dt.strftime('%Y-%m-%d')

        resultado = forecast_df.to_dict(orient='records')

        return resultado