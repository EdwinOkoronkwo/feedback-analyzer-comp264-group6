# chalicelib/interfaces/translator.py

from abc import ABC, abstractmethod

class ITranslateProvider(ABC):
    @abstractmethod
    def translate(self, text: str, target_lang: str = "en") -> str:
        """Translates text to the target language"""
        pass