import subprocess
import base64
import platform
from werkzeug.datastructures import FileStorage

class TTSModelo:
    # … tus otros métodos y atributos …

    def SpeechToText(self, file: FileStorage, id):
        """Convert speech to text.

        Args:
            file (FileStorage):
                Input audio file
            id (str):
                unique user session ID for save the file
        """
        #Conversion de la voz a text retornandolo
        self.__setId(id)
        file.save(self.input_path)
        model_size = 'small'  # 'small' | 'big'

        # ——— Validación de sistema operativo ———
        system = platform.system()
        # Ruta al modelo (usa siempre separadores POSIX; subprocess lo manejará)
        model_arg = f"{self.vosk_models_dir}/es-{model_size}"
        base_cmd = [
            'vosk-transcriber',
            '--model', model_arg,
            '-i', self.input_path,
            '-l', 'es'
        ]

        if system == "Windows":
            # En Windows invocamos vía PowerShell
            cmd = [
                'powershell', '-Command',
                " ".join(f'"{part}"' for part in base_cmd)
            ]
        else:
            # En Linux/macOS invocación directa
            cmd = base_cmd

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        print(result)
        return result.stdout

    def __setId(self, id):
        self.input_path = f'./static/media/records/input-{id}.mp3'
        self.output_path = f'./static/media/records/output-{id}.wav'
