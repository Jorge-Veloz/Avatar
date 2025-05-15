
import os
import platform
import subprocess
import base64

import torch
from TTS.api import TTS
from werkzeug.datastructures import FileStorage

class TTSModelo:
    def __init__(
        self,
        records_dir: str = "./static/media/records",
        vosk_models_dir: str = "./modelosIA/vosk-models",
    ):
        """
        Args:
            records_dir: carpeta donde se guardan input/output de audio.
            vosk_models_dir: ruta base de los modelos Vosk.
        """
        self.records_dir = records_dir
        self.vosk_models_dir = vosk_models_dir
        os.makedirs(self.records_dir, exist_ok=True)

    def __set_id(self, session_id: str):
        """Define rutas de input/output según el session_id."""
        filename_base = f"{session_id}"
        self.input_path = os.path.join(self.records_dir, f"input-{filename_base}.mp3")
        self.output_path = os.path.join(self.records_dir, f"output-{filename_base}.wav")

    def TextToSpeech(self, text: str, session_id: str, model_choice: str = "vits") -> str:
        """
        Convierte texto a voz y retorna el audio codificado en base64.

        Args:
            text: texto a sintetizar.
            session_id: ID de sesión para nombrar archivos.
            model_choice: 'xtts' o 'vits'. Por defecto 'vits'.
        """
        self.__set_id(session_id)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[TTSModelo] Usando dispositivo: {device}")

        if model_choice.lower() == "xtts":
            tts = TTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                progress_bar=False
            ).to(device)
            tts.tts_to_file(
                text=text,
                file_path=self.output_path,
                speaker="Filip Traverse",
                language="es"
            )
        else:
            tts = TTS(
                model_name="tts_models/es/css10/vits",
                progress_bar=False
            ).to(device)
            tts.tts_to_file(text=text, file_path=self.output_path)

        # Leer y codificar en base64
        with open(self.output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return encoded

    def SpeechToText(
        self,
        file: FileStorage,
        session_id: str,
        model_size: str = "small",
    ) -> str:
        """
        Convierte audio a texto usando Vosk.

        Args:
            file: objeto FileStorage de Flask/Werkzeug.
            session_id: ID de sesión para nombrar archivos.
            model_size: 'small' o 'big'. Por defecto 'small'.
        """
        self.__set_id(session_id)
        file.save(self.input_path)

        # Ruta al modelo Vosk
        model_folder = f"es-{model_size}"
        model_path = os.path.join(self.vosk_models_dir, model_folder)

        # Construir comando
        base_cmd = [
            "vosk-transcriber",
            "--model", model_path,
            "-i", self.input_path,
            "-l", "es"
        ]

        system = platform.system()
        if system == "Windows":
            # En Windows ejecutamos en PowerShell para respetar .exe y rutas
            cmd = ["powershell", "-Command", " ".join(f'"{p}"' for p in base_cmd)]
        else:
            # Linux/macOS: invocación directa
            cmd = base_cmd

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # Puedes loguear e.stderr para depuración
            error_msg = e.stderr or e.stdout or str(e)
            raise RuntimeError(f"[TTSModelo] Error en SpeechToText: {error_msg}")

