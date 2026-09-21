SUPPORTED_LANGUAGES = {
    "es": "Español",
    "en": "English",
    "pt": "Português"
}


DEFAULT_LANGUAGE = "es"


def get_supported_languages():
    return SUPPORTED_LANGUAGES.copy()


def is_supported_language(language):
    return language in SUPPORTED_LANGUAGES


def get_language_name(language):
    return SUPPORTED_LANGUAGES.get(
        language,
        SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]
    )