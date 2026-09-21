import json
from pathlib import Path


class ConfigService:

    def __init__(self):

        self.config_directory = (
            Path.home() / ".steam_gamevault"
        )

        self.config_file = (
            self.config_directory / "config.json"
        )

    def create_directory(self):

        self.config_directory.mkdir(
            parents=True,
            exist_ok=True
        )

    def save_config(
        self,
        steam_id,
        language="es",
        family_token=""
    ):

        self.create_directory()

        config = {
            "steam_id": steam_id,
            "language": language,
            "family_token": family_token
        }

        with open(
            self.config_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                config,
                file,
                indent=4,
                ensure_ascii=False
            )

    def load_config(self):

        if not self.config_file.exists():
            return None

        try:

            with open(
                self.config_file,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):

            return None

    def get_steam_id(self):

        config = self.load_config()

        if not config:
            return None

        return config.get("steam_id")

    def get_language(self):

        config = self.load_config()

        if not config:
            return "es"

        return config.get(
            "language",
            "es"
        )

    def get_family_token(self):

        config = self.load_config()

        if not config:
            return ""

        return config.get(
            "family_token",
            ""
        )

    def has_family_config(self):

        return bool(
            self.get_family_token()
        )

    def has_config(self):

        config = self.load_config()

        if not config:
            return False

        return bool(
            config.get("steam_id")
        )

    def clear_config(self):

        if self.config_file.exists():

            try:
                self.config_file.unlink()

            except OSError:
                pass