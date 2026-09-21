import requests


class BackendService:

    def __init__(
        self,
        base_url="https://gamevault-qt6h.onrender.com"
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = (5, 30)

    def get_owned_games(self, steam_input):
        response = requests.get(
            f"{self.base_url}/steam/games",
            params={
                "steam_input": steam_input
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_recently_played_games(self, steam_id):

        response = requests.get(
            f"{self.base_url}/steam/recently-played",
            params={
                "steam_id": steam_id
            },
            timeout=self.timeout
        )

        response.raise_for_status()
        return response.json()

    def get_achievements(self, steam_id, app_id):
        response = requests.get(
            f"{self.base_url}/steam/achievements",
            params={
                "steam_id": steam_id,
                "app_id": app_id
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_steam_login_url(self):
        return f"{self.base_url}/auth/steam"