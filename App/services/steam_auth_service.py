import webbrowser
from urllib.parse import urlencode


class SteamAuthService:
    STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

    def login(self):
        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": "http://localhost:8000/auth/steam/callback",
            "openid.realm": "http://localhost:8000/",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select"
        }

        url = f"{self.STEAM_OPENID_URL}?{urlencode(params)}"

        webbrowser.open(url)