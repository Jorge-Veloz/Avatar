
# =======================
# Imports
# =======================
import os
import re
import json
import time
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
from flask import (
    Flask, Response, render_template, url_for, request, session, jsonify, send_from_directory
)
#from flask_jwt_extended import JWTManager

# Controladores y funciones propias
from controladores.asistente import AsistenteControlador
from controladores.edificios import EdificiosControlador
from controladores.chats import ChatsControlador
from controladores.algoritmo_ml import AlgoritmoMLControlador
from funciones.asistente import getPromptAsistentes
from funciones.funciones import determinarSemanaActual, getRandomDF


# =======================
# Configuración y variables globales
# =======================
load_dotenv(os.path.join(os.getcwd(), '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = b'secret_key'
app.config['ASSETS_FOLDER'] = os.path.join(os.getcwd(), 'assets')

# Instancia de controladores
controladorChats = ChatsControlador(app)
controladorAsistente = AsistenteControlador(app)
controladorEdificios = EdificiosControlador(app)
controladorAlgoritmoML = AlgoritmoMLControlador()

# Inicialización del JWT
#jwt = JWTManager(app)

# Precarga de rutas estáticas
with app.test_request_context():
    url_for('static', filename='/resources/')
    url_for('static', filename='/css/')
    url_for('static', filename='/scripts/')
    url_for('static', filename='/assets/')

"""
=======================
 Rutas de archivos estáticos y vistas principales
=======================
"""

# Sirve archivos de la carpeta assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(app.config['ASSETS_FOLDER'], filename)

# Sirve archivos de la carpeta static
@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

# Página principal
@app.get('/')
def index():
    return render_template('index.html')

@app.get('/avatar')
def modeloAvatar():
    return render_template('avatar.html')

# Obtener edificios
@app.get('/edificios')
def get_edificios():
    respuesta = controladorEdificios.getEdificios()
    estado = 200 if respuesta['ok'] else 500
    return jsonify(respuesta), estado

# Pruebas y utilidades
@app.get('/chats')
def prueba_chats():
    if 'hilo' not in session:
        hilo = controladorAsistente.crearHilo()
        session['hilo'] = hilo
    mensaje = controladorAsistente.getListaMensajes(session.get('hilo'))
    return jsonify(mensaje)

@app.post('/reaccionar-msg')
def reaccionar_msg():
    if 'hilo' not in session:
        hilo = controladorAsistente.crearHilo()
        session['hilo'] = hilo
    data_dict = json.loads(request.data.decode('utf-8'))
    idMensaje = data_dict['idMensaje']
    reaccion = data_dict['reaccion']
    resultado = controladorAsistente.reaccionarMensaje(session.get('hilo'), idMensaje, reaccion)
    return jsonify(resultado)


# Consumo de edificios
@app.get('/datos')
def get_consumo_edificios():

    edificio = request.args.get('idEdificacion')
    piso = request.args.get('idPiso')
    ambiente = request.args.get('idAmbiente')
    fechaInicio = request.args.get('fechaInicio')
    fechaFin = request.args.get('fechaFin')
    respuesta = controladorEdificios.getConsumoEdificios(edificio, piso, ambiente, fechaInicio, fechaFin)
    return jsonify(respuesta)


# Inicializa el asistente en tiempo real (streaming SSE)
@app.post('/inicializar')
def inicializar():
    # Limpia la sesión
    for key in ['hilo', 'contenido', 'intenciones', 'prediccion', 'memoria']:
        if key in session:
            session.pop(key)
    hilo = controladorAsistente.crearHilo()
    session['hilo'] = hilo
    session['contenido'] = []
    mensajes = [{"role": "user", "content": "El usuario se ha conectado, preséntate ante el usuario y dale una bienvenida.", "ok": True}]
    intenciones = {'anterior': 'ninguna', 'actual': 'ninguna', 'siguiente': 'ninguna'}

    return Response(event_stream_universal(
        hilo=hilo,
        modo="inicializar",
        mensajes=mensajes,
        intenciones=intenciones,
        contenido=None,
        controladorAsistente=controladorAsistente,
        controladorChats=controladorChats
    ), mimetype='text/event-stream')



# Conversación principal (voz a texto, procesamiento y streaming SSE)
@app.post('/conversar')
def conversar():
    if 'hilo' not in session:
        session['hilo'] = controladorAsistente.crearHilo()
    if 'prediccion' not in session:
        session['prediccion'] = {'msgs': []}
    if 'intenciones' in session:
        print("Intenciones al inicio de la consulta: ", session['intenciones'])
    if 'intenciones' in session and 'actual' in session['intenciones']:
        session['intenciones']['anterior'] = session['intenciones']['actual']
    else:
        session['intenciones'] = {'anterior': 'ninguna'}
    
    session['intenciones']['actual'] = 'ninguna'
    session['intenciones']['siguiente'] = 'ninguna'
    
    codigo = session['hilo']
    
    intencion = request.form.get('intencion')
    #print(f"Intención recibida: {intencion}")
    
    voz = request.files.get('voice')
    #print("Paso #1: Conversión de voz a texto.")
    
    tiempo_inicio = time.time()
    sttRespuesta = controladorAsistente.speech_to_text(voz, codigo)
    tiempo_fin = time.time()
    print(f"Tiempo de ejecución Conversión de voz a texto: {tiempo_fin - tiempo_inicio:.2f} segundos")
    
    textStt = sttRespuesta['datos'] if sttRespuesta['ok'] else 'No pude entender lo que dijiste, Podrías repetirlo porfavor?'
    controladorChats.enviarMensaje(codigo, [{"role": "user", "content": textStt}])
    respuesta = procesamientoConversacion(textStt, intencion)
    #print("Respuesta procesada:", respuesta)
    #print("Contenido de sesión:", session.get('contenido'))
    
    contenido = session.get('contenido', [])
    intenciones = session.get('intenciones', [])
    #print("Intenciones antes de la respuesta:", intenciones)
    
    return Response(event_stream_universal(
        hilo=codigo,
        modo="conversar",
        mensajes=respuesta,
        intenciones=intenciones,
        contenido=contenido,
        controladorAsistente=controladorAsistente,
        controladorChats=controladorChats
    ), mimetype='text/event-stream')


# Predicción de consumo (API)
@app.get('/api/prediccion')
def get_prediccion():
    edificio = request.args.get('edificio')
    piso = request.args.get('piso')
    ambiente = request.args.get('ambiente')
    fecha = request.args.get('fecha')
    # Determinar las fechas de las semanas
    lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva = determinarSemanaActual(fecha)
    # Se consulta el consumo completo del ambiente seleccionado toda la fecha agrupada por día
    ruta_json = 'consumo_energetico_2025_08_18.json'  # Cambiar por data de base de datos
    # Se consulta la predicción de la última semana del consumo del ambiente seleccionado
    data_semana_consumo = getRandomDF(lunes_semana_actual, inicio_semana_nueva)  # Cambiar por base de datos
    # Se genera la data de variables exógenas para la predicción
    textoLLM = (
        "DÍA: Lunes | TIPO: feriado\nDÍA: Martes | TIPO: normal\nDÍA: Miércoles | TIPO: normal\n"
        "DÍA: Jueves | TIPO: especial\nDÍA: Viernes | TIPO: especial\nDÍA: Sábado | TIPO: normal\nDÍA: Domingo | TIPO: normal"
    )
    data_generada = controladorAlgoritmoML.generarDF(textoLLM, inicio_semana_nueva)
    data_nueva = pd.concat([data_semana_consumo, data_generada], axis=0)
    fechas_prediccion = (lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva)
    datos_prediccion = controladorAlgoritmoML.predecirConsumo(ruta_json, data_nueva, fechas_prediccion)
    datos_ultima_semana = datos_prediccion[-7:]
    return jsonify({'ok': True, 'observacion': None, 'datos': datos_ultima_semana})


# =======================
# Función universal para streaming SSE (event_stream)
# =======================
def event_stream_universal(hilo, modo, mensajes, intenciones, contenido, controladorAsistente, controladorChats):
    """
    Función generadora universal para streaming SSE en Flask.
    - hilo: id de hilo/conversación
    - modo: 'inicializar' o 'conversar'
    - mensajes: lista de mensajes o respuesta
    - intenciones: diccionario de intenciones
    - contenido: datos extra para gráficas (solo en conversar)
    - controladorAsistente, controladorChats: instancias de controladores
    """
    buffer = ''
    txt_completo = ''
    # Solo para modo conversar
    if contenido:
        yield f"{json.dumps({'type':'grafico','data': json.dumps(contenido, default=str)})}\n\n"
    if intenciones:
        yield f"{json.dumps({'type':'intenciones','data': json.dumps(intenciones, default=str)})}\n\n"
    # Streaming de tokens
    for token in controladorAsistente.stream_tokens(hilo, modo, mensajes, intenciones, contenido):
        yield f"{json.dumps({'type':'token','token':token})}\n\n"
        buffer += token
        txt_completo += token
        # Cortar por signos de puntuación
        parts = re.split(r'(?<=[.!?])\s+', buffer)
        if len(parts) > 1:
            for sent in parts[:-1]:
                sent = sent.strip()
                if sent:
                    audio = controladorAsistente.text_to_speech(sent)
                    yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
            buffer = parts[-1]
    if buffer.strip():
        audio = controladorAsistente.text_to_speech(buffer.strip())
        yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
    print("Guardar en la base de datos el mensaje completo:")
    controladorChats.enviarMensaje(hilo, [{"role": "assistant", "content": txt_completo}])
    yield "{\"type\":\"end\"}\n\n"


# =======================
# Funciones auxiliares de procesamiento de conversación
# =======================
def procesamientoConversacion(texto, intencion='ninguna'):
    if intencion == 'ninguna':
        session['contenido'] = []
    funciones = {
        'solicita_datos_consumo': controladorEdificios.consultarConsumo,
        'solicita_prediccion': controladorEdificios.getPrediccion
    }
    etiquetas = list(funciones.keys()) + ['pregunta_respuesta_general']
    if intencion == 'ninguna':
        intencion_asistente = controladorEdificios.preguntarAsistente(
            'mistral:latest', getPromptAsistentes('detectar_intencion', texto), 'generar')
        resultado = {'intencion': intencion_asistente.replace('-', '').replace('\n', '').strip().lower(), 'confidence': 1.0}
    else:
        resultado = {'intencion': intencion, 'confidence': 1.0}
    intencion = 'pregunta_respuesta_general' if resultado['intencion'] not in etiquetas else resultado['intencion']
    session['intenciones']['actual'] = str(intencion)
    mensajeAsistente = {"role": "user", "content": texto, "ok": True}
    mensajesAsis = [mensajeAsistente]
    if intencion != 'pregunta_respuesta_general':
        funcionIA = funciones[intencion]
        respuesta = funcionIA(texto)
        if respuesta['info']:
            session['contenido'].append({"nombre": intencion, "valor": respuesta['info']})
            mensajesAsis.append({"role": "user", "content": respuesta['reason'], "ok": respuesta['success']})
        else:
            mensajesAsis = [{"role": "user", "content": respuesta['reason'], "ok": respuesta['success']}]
    return mensajesAsis


if __name__ == '__main__':
    app.run(port=3005, debug=True, use_reloader=True, host='0.0.0.0', ssl_context=(os.environ.get("RUTA_CERT"), os.environ.get("RUTA_CERT_KEY")))
#    app.run(port=3002, debug=True, host='0.0.0.0')
