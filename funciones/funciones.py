from datetime import timedelta, datetime
import pandas as pd
import numpy as np
def completarDias(dias_res, hoy):
    # === Diccionario con orden base ===
    traduccion_dias = {
        'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miercoles', 'thursday': 'jueves', 'friday': 'viernes', 'saturday': 'sabado', 'sunday': 'domingo'
    }
    orden_dias = list(traduccion_dias.values()) #['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    orden_indices = {dia: i for i, dia in enumerate(orden_dias)}
    
    # === Detectar día actual ===
    #hoy = fecha_empieza
    dia_actual = traduccion_dias[hoy.strftime('%A').lower()]
    
    # Normalizar nombre si tiene tilde
    dia_actual = dia_actual.replace('miércoles', 'miercoles').replace('sábado', 'sabado')
    
    # === Construir orden rotado desde el siguiente día ===
    indice_hoy = orden_indices[dia_actual]
    orden_rotado = orden_dias[indice_hoy + 1:] + orden_dias[:indice_hoy + 1]
    
    # === Crear diccionario desde entrada parcial ===
    dias_dict = {dia.lower(): tipo for dia, tipo in dias_res}
    
    # === Completar días faltantes con 'Normal' ===
    for dia in orden_rotado:
        if dia not in dias_dict:
            dias_dict[dia] = 'Normal'
    
    # === Construir lista ordenada completa ===
    dias_llm_ordenada = [(dia.capitalize(), dias_dict[dia]) for dia in orden_rotado]
    
    # === Calcular fechas desde mañana ===
    fecha_inicio = hoy + timedelta(days=1)

    return dias_llm_ordenada, fecha_inicio

def getRandomDF(lunes_semana_actual, inicio_semana_nueva):
    fechas = pd.date_range(start=lunes_semana_actual, end=inicio_semana_nueva, freq="D")
    # Crear los datos aleatorios
    colferiado = np.random.randint(0, 2, len(fechas)).astype(np.int64)
    colevento = np.random.randint(0, 2, len(fechas)).astype(np.int64)
    col_temp = np.random.uniform(np.float64(19.42430644731337), np.float64(30.47436405875521), len(fechas)).astype(np.float64)

    df_semana_aleatoria = pd.DataFrame({
        'feriado': colferiado,
        'evento_especial': colevento,
        'temperatura': col_temp
    }, index=fechas)
    return df_semana_aleatoria

def determinarSemanaActual(dia_actual):
    # Fecha actual
    hoy = pd.to_datetime(dia_actual)
    
    # Encontrar el lunes de la semana actual
    lunes_semana_actual = hoy - timedelta(days=hoy.weekday())  # weekday(): lunes=0, domingo=6
    
    # Calcular domingo de la siguiente semana (lunes + 13 días)
    domingo_semana_siguiente = lunes_semana_actual + timedelta(days=13)
    inicio_semana_nueva = lunes_semana_actual + timedelta(days=6)
    return lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva