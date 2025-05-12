from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import json
import re
from unidecode import unidecode
from rapidfuzz import process, fuzz

class IAModelo:
    def __init__(self, etiquetas):
        self.model_name = "Recognai/bert-base-spanish-wwm-cased-xnli"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.etiquetas = etiquetas
        self.classifier = pipeline("zero-shot-classification", model=self.model, tokenizer=self.tokenizer)
    
    def detectar_intencion(self, consulta):
        resultado = self.classifier(consulta, self.etiquetas, hypothesis_template="Que es lo que el usuario quiso decir aqui: {}. Toma en consideracion siempre las primeras palabras para clasificar")

        # Tomamos la etiqueta con mayor score
        mejor_intencion = resultado["labels"][0]
        return {
            "intencion": mejor_intencion,
            "confianza": round(resultado["scores"][0], 3)
        }