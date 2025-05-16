import os
import platform
import subprocess
import base64

import torch
from TTS.api import TTS
from werkzeug.datastructures import FileStorage

class TTSModelo:
    id: str
    input_path: str
    output_path: str
    transcribed: str

    def TextToSpeech(self, text, id):
        """Convert speech to text.

        Args:
            text (FileStorage):
                Input text to synthesize
            id (str):
                unique user session ID for save the file
        """
        # Conversión del texto a voz retornando a base64
        self.__setId(id)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print('//////////////////////////////////////////', device)
        model = 'vits'  # 'xtts' | 'vits'
        if model == 'xtts':
            tts = TTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                progress_bar=False
            ).to(device)
            tts.tts_to_file(
                text=text,
                file_path=self.output_path,
                speaker='Filip Traverse',
                language='es'
            )
        else:
            tts = TTS(
                model_name="tts_models/es/css10/vits",
                progress_bar=False
            ).to(device)
            tts.tts_to_file(text=text, file_path=self.output_path)

        with open(self.output_path, "rb") as audio_file:
            encoded = base64.b64encode(audio_file.read()).decode("utf-8")
        return encoded

    def SpeechToText(self, file: FileStorage, id):
        """Convert speech to text.

        Args:
            file (FileStorage):
                Input audio file
            id (str):
                unique user session ID for save the file
        """
        # Conversión de la voz a text retornándolo
        self.__setId(id)
        file.save(self.input_path)

        model_size = 'big'  # 'small' | 'big'

        # Construye la ruta al modelo de forma portátil
        model_path = os.path.join('.', 'modelosIA', 'vosk-models', f'es-{model_size}')

        # Prepara el comando según el sistema operativo
        system = platform.system()
        if system == "Windows":
            # En Windows invocamos vía PowerShell para respetar .exe y comillas
            cmd = [
                'powershell', '-Command',
                f'vosk-transcriber --model "{model_path}" -i "{self.input_path}" -l es'
            ]
        else:
            # En Linux/macOS llamamos directo al ejecutable
            cmd = [
                'vosk-transcriber',
                '--model', model_path,
                '-i', self.input_path,
                '-l', 'es'
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result)
        return result.stdout

    def __setId(self, id):
        self.input_path = f'./static/media/records/input-{id}.mp3'
        self.output_path = f'./static/media/records/output-{id}.wav'
