import torch
from TTS.api import TTS
from werkzeug.datastructures import FileStorage

import subprocess
import base64

class SpeechController:
    id: str

    input_path: str

    output_path: str

    transcribed: str

    def speechToText(self, file: FileStorage, id: str) -> str:
        """Convert speech to text.

        Args:
            file (FileStorage):
                Input audio file
            id (str):
                unique user session ID for save the file
        """
        self.__setId(id)
        file.save(self.input_path)
        result = subprocess.run([
            'powershell', '-Command', 
            f'vosk-transcriber --model .\\speech-recognition\\vosk-models\\es-small -i {self.input_path} -l es'], capture_output=True, text=True
        )
        return result.stdout

    def textToSpeech(self, text: str, id: str) -> str:
        """Convert speech to text.

        Args:
            text (FileStorage):
                Input text to synthesize
            id (str):
                unique user session ID for save the file
        """
        self.__setId(id)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts = TTS(
            model_name="tts_models/es/css10/vits", 
            progress_bar=False
        ).to(device)
        tts.tts_to_file(text=text, file_path=self.output_path)
        with open(self.output_path, "rb") as audio_file:
            encoded = base64.b64encode(audio_file.read()).decode("utf-8")
        return encoded

    def __setId(self, id: str) -> None:
        self.input_path = f'./speech-recognition/records/input-{id}.mp3'
        self.output_path = f'./speech-recognition/records/output-{id}.wav'