from localization.es import TRANSLATIONS as ES
from localization.en import TRANSLATIONS as EN
from localization.pt import TRANSLATIONS as PT


TRANSLATIONS = {
    "es": ES,
    "en": EN,
    "pt": PT
}


class LanguageManager:

    def __init__(self, language="es"):

        if language not in TRANSLATIONS:
            language = "es"

        self.language = language
        self.translations = TRANSLATIONS[language]

    def set_language(self, language):

        if language not in TRANSLATIONS:
            return False

        self.language = language
        self.translations = TRANSLATIONS[language]

        return True

    def get_language(self):

        return self.language

    def get(self, key, **kwargs):

        text = self.translations.get(
            key,
            key
        )

        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text
