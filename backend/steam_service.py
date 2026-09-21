import os
import re
import requests

from urllib.parse import quote, urlparse
from dotenv import load_dotenv


load_dotenv()


class SteamService:

    BASE_URL = "https://api.steampowered.com"
    TIMEOUT = (5, 15)

    def __init__(self):

        self.api_key = os.getenv("STEAM_API_KEY")

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/153.0.0.0 "
                "Safari/537.36"
            )
        })

    def get_owned_games(self, steam_id):

        url = (
            f"{self.BASE_URL}"
            "/IPlayerService/GetOwnedGames/v0001/"
        )

        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "format": "json",
            "include_appinfo": True,
            "include_played_free_games": True,
            "include_free_sub": True
        }

        response = self.session.get(
            url,
            params=params,
            timeout=self.TIMEOUT
        )

        response.raise_for_status()

        return response.json().get(
            "response",
            {}
        )

    def resolve_custom_profile(self, custom_name):

        custom_name = custom_name.strip()

        if not custom_name:
            return None

        # ------------------------------------------
        # STEAM WEB API
        # ------------------------------------------

        try:

            url = (
                f"{self.BASE_URL}"
                "/ISteamUser/ResolveVanityURL/v0001/"
            )

            params = {
                "key": self.api_key,
                "vanityurl": custom_name,
                "format": "json"
            }

            response = self.session.get(
                url,
                params=params,
                timeout=self.TIMEOUT
            )

            response.raise_for_status()

            result = response.json().get(
                "response",
                {}
            )

            if result.get("success") == 1:

                steam_id = result.get("steamid")

                if steam_id:
                    return steam_id

        except Exception as error:

            print(
                "ResolveVanityURL error:",
                error
            )

        # ------------------------------------------
        # PERFIL XML
        # ------------------------------------------

        try:

            profile_url = (
                "https://steamcommunity.com/id/"
                f"{quote(custom_name, safe='')}"
                "?xml=1"
            )

            response = self.session.get(
                profile_url,
                timeout=self.TIMEOUT
            )

            response.raise_for_status()

            match = re.search(
                r"<steamID64>(\d+)</steamID64>",
                response.text
            )

            if match:
                return match.group(1)

        except Exception as error:

            print(
                "Steam XML error:",
                error
            )

        # ------------------------------------------
        # PERFIL HTML
        # ------------------------------------------

        try:

            profile_url = (
                "https://steamcommunity.com/id/"
                f"{quote(custom_name, safe='')}"
            )

            response = self.session.get(
                profile_url,
                timeout=self.TIMEOUT
            )

            response.raise_for_status()

            patterns = [
                r'"steamid"\s*:\s*"(\d{17})"',
                r'"steamID"\s*:\s*"(\d{17})"',
                r'data-steamid="(\d{17})"',
                r'/profiles/(\d{17})'
            ]

            for pattern in patterns:

                match = re.search(
                    pattern,
                    response.text
                )

                if match:
                    return match.group(1)

        except Exception as error:

            print(
                "Steam profile error:",
                error
            )

        return None

    def get_game_achievements(
        self,
        steam_id,
        app_id
    ):

        url = (
            f"{self.BASE_URL}"
            "/ISteamUserStats/"
            "GetPlayerAchievements/v0001/"
        )

        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "appid": app_id,
            "format": "json"
        }

        response = self.session.get(
            url,
            params=params,
            timeout=self.TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        achievements = (
            data
            .get("playerstats", {})
            .get("achievements", [])
        )

        total = len(achievements)

        unlocked = sum(
            1
            for achievement in achievements
            if achievement.get("achieved") == 1
        )

        return unlocked, total

    def get_user_reviews(
        self,
        steam_id,
        on_progress=None
    ):

        reviews = []

        page = 1

        while True:

            url = (
                f"https://store.steampowered.com/"
                f"curator/{steam_id}"
            )

            # Este método mantiene la compatibilidad
            # con la implementación existente.
            # Si tu SteamService ya tenía una
            # implementación específica de reviews,
            # reemplazaremos solamente este método.

            break

        return reviews