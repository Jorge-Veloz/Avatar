from flask import Flask, render_template, url_for, request, session, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
import json
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), '.env'))

# Guardara todos los ChatCompletions de respuesta a las funciones del asistente
# Esto evita que el asistente vuelva a repetir el envio de la funcion
compMsgs = []

app = Flask(__name__)
app.config['SECRET_KEY'] = b'secret_key'

# Inicializacion del JWT
jwt = JWTManager(app)

with app.test_request_context():
    url_for('static', filename='/resources/')
    url_for('static', filename='/css/')
    url_for('static', filename='/scripts/')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

@app.get('/')
def Index():
    return render_template('3d.html')

@app.get('/avatar')
def modeloAvatar():
    return render_template('avatar.html')

if __name__ == '__main__':
    app.run(port=3000, debug=True)