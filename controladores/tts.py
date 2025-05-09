from modelos.tts import TTSModelo

class TTSControlador:
    def __init__(self):
        self.modelo = TTSModelo()

    def TextToSpeech(self, texto, id):
        #Conversion del texto a voz retornando a base64
        voz = self.modelo.TextToSpeech(texto, id)
        resultado = {
            "ok": True,
            "observacion": None,
            "datos": {'voice_encoded': voz}
        }
        return resultado

    def SpeechToText(self, voz, id):
        #Conversion de la voz a text retornandolo
        texto = self.modelo.SpeechToText(voz, id)
        resultado = {
            "ok": True,
            "observacion": None,
            "datos": texto
        }
        return resultado 
