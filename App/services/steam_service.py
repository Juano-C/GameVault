import os
import re
import time

import requests
from bs4 import BeautifulSoup


class SteamService:

    BASE_URL = "https://api.steampowered.com"
    COMMUNITY_URL = "https://steamcommunity.com"

    REQUEST_TIMEOUT = (5, 20)
    MAX_REVIEW_PAGES = 100

    def __init__(self, family_token=None):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/153.0.0.0 "
                "Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
        })

        # IMPORTANTE:
        # No usamos STEAM_WEBAPI_TOKEN del .env.
        # El token de Family pertenece al usuario.
        self.webapi_token = (
            family_token.strip()
            if family_token
            else None
        )

    # ==========================================================
    # STEAM FAMILY
    # ==========================================================

    def get_family_access_token(self):

        if not self.webapi_token:

            raise RuntimeError(
                "Biblioteca familiar no configurada."
            )

        return self.webapi_token

    def get_family_group(self, steam_id):

        token = self.get_family_access_token()

        url = (
            f"{self.BASE_URL}"
            "/IFamilyGroupsService/"
            "GetFamilyGroupForUser/v1/"
        )

        params = {
            "access_token": token,
            "origin": "https://store.steampowered.com",
            "spoof_steamid": "",
            "include_family_group_response": "true"
        }

        response = self.session.get(
            url,
            params=params,
            timeout=self.REQUEST_TIMEOUT
        )

        if response.status_code in (401, 403):

            raise RuntimeError(
                "Token de Steam Family inválido "
                "o vencido."
            )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                "Steam devolvió una respuesta inválida "
                "al consultar Steam Family."
            )

        return data

    def get_family_group_id(self, steam_id):

        data = self.get_family_group(steam_id)

        family_group_id = self._find_family_group_id(
            data
        )

        if family_group_id:
            return family_group_id

        response = data.get(
            "response",
            {}
        )

        if response.get(
            "is_not_member_of_any_group"
        ):
            raise RuntimeError(
                "La cuenta no pertenece a ningún "
                "grupo familiar de Steam."
            )

        raise RuntimeError(
            "Steam no devolvió family_groupid."
        )

    def _find_family_group_id(self, data):

        if isinstance(data, dict):

            if "family_groupid" in data:
                return data["family_groupid"]

            for value in data.values():

                result = self._find_family_group_id(
                    value
                )

                if result:
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._find_family_group_id(
                    item
                )

                if result:
                    return result

        return None

    def get_family_library(self, steam_id):

        family_group_id = self.get_family_group_id(
            steam_id
        )

        token = self.get_family_access_token()

        url = (
            f"{self.BASE_URL}"
            "/IFamilyGroupsService/"
            "GetSharedLibraryApps/v1/"
        )

        params = {
            "access_token": token,
            "family_groupid": family_group_id,
            "include_own": "true",
            "include_excluded": "false",
            "include_free": "false",
            "include_non_games": "false",
            "language": "english",
            "origin": "https://store.steampowered.com"
        }

        response = self.session.get(
            url,
            params=params,
            timeout=(5, 30)
        )

        if response.status_code in (401, 403):

            raise RuntimeError(
                "Steam rechazó el token al obtener "
                "la biblioteca familiar."
            )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                "Steam devolvió una respuesta inválida "
                "al obtener la biblioteca familiar."
            )

        return (
            data
            .get("response", {})
            .get("apps", [])
        )

    def get_family_playtime(self, steam_id):

        family_group_id = self.get_family_group_id(
            steam_id
        )

        token = self.get_family_access_token()

        url = (
            f"{self.BASE_URL}"
            "/IFamilyGroupsService/"
            "GetPlaytimeSummary/v1/"
        )

        response = self.session.post(
            url,
            data={
                "access_token": token,
                "family_groupid": family_group_id
            },
            timeout=self.REQUEST_TIMEOUT
        )

        if response.status_code in (401, 403):

            raise RuntimeError(
                "Steam rechazó el token al obtener "
                "el tiempo de juego familiar."
            )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                "Steam devolvió una respuesta inválida "
                "al obtener el tiempo de juego familiar."
            )

        entries = (
            data
            .get("response", {})
            .get("entries", [])
        )

        target = str(steam_id)

        result = {}

        for entry in entries:

            if str(
                entry.get("steamid", "")
            ) != target:
                continue

            app_id = entry.get("appid")

            if app_id is None:
                continue

            seconds = int(
                entry.get(
                    "seconds_played",
                    0
                ) or 0
            )

            latest = entry.get(
                "latest_played"
            )

            result[int(app_id)] = {
                "playtime_minutes": seconds // 60,
                "last_played": (
                    int(latest)
                    if latest
                    else None
                )
            }

        return result

    # ==========================================================
    # OWN LIBRARY
    # ==========================================================

    def get_owned_games(
        self,
        steam_id,
        api_key
    ):

        url = (
            f"{self.BASE_URL}"
            "/IPlayerService/"
            "GetOwnedGames/v0001/"
        )

        params = {
            "key": api_key,
            "steamid": steam_id,
            "format": "json",
            "include_appinfo": True,
            "include_played_free_games": True,
            "include_free_sub": True
        }

        response = self.session.get(
            url,
            params=params,
            timeout=self.REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # ACHIEVEMENTS
    # ==========================================================

    def get_game_achievements(
        self,
        steam_id,
        app_id,
        api_key
    ):

        player_url = (
            f"{self.BASE_URL}"
            "/ISteamUserStats/"
            "GetPlayerAchievements/v1/"
        )

        response = self.session.get(
            player_url,
            params={
                "key": api_key,
                "steamid": steam_id,
                "appid": app_id
            },
            timeout=self.REQUEST_TIMEOUT
        )

        if response.status_code == 200:

            try:
                data = response.json()
            except ValueError:
                data = {}

            playerstats = data.get(
                "playerstats"
            )

            if playerstats:

                achievements = (
                    playerstats.get(
                        "achievements"
                    )
                )

                if achievements is not None:

                    total = len(
                        achievements
                    )

                    unlocked = sum(
                        1
                        for achievement
                        in achievements
                        if achievement.get(
                            "achieved",
                            0
                        ) == 1
                    )

                    return unlocked, total

        schema_url = (
            f"{self.BASE_URL}"
            "/ISteamUserStats/"
            "GetSchemaForGame/v2/"
        )

        schema_response = self.session.get(
            schema_url,
            params={
                "key": api_key,
                "appid": app_id
            },
            timeout=self.REQUEST_TIMEOUT
        )

        if schema_response.status_code != 200:
            return None

        try:
            schema_data = (
                schema_response.json()
            )
        except ValueError:
            return None

        achievements = (
            schema_data
            .get("game", {})
            .get("availableGameStats", {})
            .get("achievements", [])
        )

        if not achievements:
            return 0, 0

        return 0, len(achievements)

    # ==========================================================
    # REVIEWS
    # ==========================================================

    def get_user_reviews(
        self,
        steam_id,
        on_progress=None
    ):

        reviews = []

        seen_signatures = set()

        base_url = (
            f"{self.COMMUNITY_URL}"
            f"/profiles/{steam_id}/recommended/"
        )

        for page in range(
            1,
            self.MAX_REVIEW_PAGES + 1
        ):

            if on_progress:

                on_progress(
                    "Obteniendo tus reseñas... "
                    f"página {page}"
                )

            response = self.session.get(
                base_url,
                params={
                    "p": page,
                    "l": "english"
                },
                timeout=self.REQUEST_TIMEOUT
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            boxes = soup.select(
                "div.review_box"
            )

            if not boxes:
                break

            page_items = []

            for box in boxes:

                review = self._parse_review_box(
                    box
                )

                if review:
                    page_items.append(
                        review
                    )

            if not page_items:
                break

            signature = tuple(
                review.get("app_id")
                for review in page_items
            )

            if signature in seen_signatures:
                break

            seen_signatures.add(
                signature
            )

            reviews.extend(
                page_items
            )

            if len(boxes) < 10:
                break

            time.sleep(0.10)

        return reviews

    def get_user_review(
        self,
        steam_id,
        app_id
    ):

        target_app_id = int(app_id)

        reviews = self.get_user_reviews(
            steam_id
        )

        for review in reviews:

            if int(
                review.get(
                    "app_id",
                    -1
                )
            ) == target_app_id:

                return review

        return None

    def _parse_review_box(
        self,
        review_box
    ):

        app_id = self._extract_review_app_id(
            review_box
        )

        if app_id is None:
            return None

        rating_text = ""

        rating_link = review_box.select_one(
            ".vote_header .title a"
        )

        if rating_link:

            rating_text = (
                rating_link
                .get_text(
                    " ",
                    strip=True
                )
                .lower()
            )

        else:

            text = (
                review_box
                .get_text(
                    " ",
                    strip=True
                )
                .lower()
            )

            if "not recommended" in text:
                rating_text = (
                    "not recommended"
                )

            elif "recommended" in text:
                rating_text = "recommended"

        if "not recommended" in rating_text:

            positive = False

        elif "recommended" in rating_text:

            positive = True

        else:

            return None

        content = review_box.select_one(
            ".content"
        )

        if content:

            gradient = content.select_one(
                ".gradient"
            )

            if gradient:
                gradient.decompose()

            review_text = content.get_text(
                "\n",
                strip=True
            )

        else:

            review_text = ""

        return {
            "app_id": int(app_id),
            "positive": positive,
            "text": review_text
        }

    def _extract_review_app_id(
        self,
        review_box
    ):

        patterns = (
            r"/recommended/(\d+)/",
            r"/app/(\d+)",
            r"steampowered\.com/app/(\d+)"
        )

        for link in review_box.select(
            "a[href]"
        ):

            href = link.get(
                "href",
                ""
            )

            for pattern in patterns:

                match = re.search(
                    pattern,
                    href
                )

                if match:
                    return int(
                        match.group(1)
                    )

        for element in review_box.select(
            "[id]"
        ):

            element_id = element.get(
                "id",
                ""
            )

            match = re.search(
                r"ReviewContent_(\d+)",
                element_id
            )

            if match:
                return int(
                    match.group(1)
                )

        for element in review_box.select(
            "[data-appid]"
        ):

            value = element.get(
                "data-appid"
            )

            if value and value.isdigit():
                return int(value)

        return None