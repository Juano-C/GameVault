from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode, urlparse

from backend.steam_service import SteamService


app = FastAPI(
    title="Steam GameVault API"
)


STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

RETURN_URL = (
    "https://gamevault-qt6h.onrender.com/auth/steam/callback"
)

REALM = (
    "https://gamevault-qt6h.onrender.com/"
)


steam_service = SteamService()


@app.api_route(
    "/",
    methods=["GET", "HEAD"]
)
def home():
    return {
        "status": "ok",
        "service": "Steam GameVault API",
        "version": "diagnostic-1"
    }


@app.get("/debug/routes")
def debug_routes():
    return {
        "loaded_file": __file__,
        "routes": [
            {
                "path": route.path,
                "methods": list(route.methods or [])
            }
            for route in app.routes
        ]
    }


def resolve_steam_id(value):

    if not value:
        return None

    value = value.strip()

    if value.isdigit():
        return value

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    try:
        parsed = urlparse(value)
    except Exception:
        return None

    if parsed.netloc.lower() not in (
        "steamcommunity.com",
        "www.steamcommunity.com"
    ):
        return None

    parts = (
        parsed.path
        .strip("/")
        .split("/")
    )

    if len(parts) < 2:
        return None

    profile_type = parts[0].lower()
    profile_value = parts[1]

    if profile_type == "profiles":

        if profile_value.isdigit():
            return profile_value

        return None

    if profile_type == "id":

        return steam_service.resolve_custom_profile(
            profile_value
        )

    return None


@app.get("/steam/games")
def get_games(
    steam_input: str = Query(...)
):

    steam_id = resolve_steam_id(
        steam_input
    )

    if not steam_id:

        return {
            "success": False,
            "error": (
                "No se pudo convertir la URL "
                "o Steam ID proporcionado."
            )
        }

    try:

        games = steam_service.get_owned_games(
            steam_id
        )

        return {
            "success": True,
            "steam_id": steam_id,
            "games": games
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


@app.get("/steam/achievements")
def get_achievements(
    steam_id: str = Query(...),
    app_id: int = Query(...)
):

    try:

        result = (
            steam_service
            .get_game_achievements(
                steam_id,
                app_id
            )
        )

        return {
            "success": True,
            "unlocked": result[0],
            "total": result[1]
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


@app.get("/auth/steam")
def steam_login():

    params = {
        "openid.ns": (
            "http://specs.openid.net/auth/2.0"
        ),
        "openid.mode": "checkid_setup",
        "openid.return_to": RETURN_URL,
        "openid.realm": REALM,
        "openid.identity": (
            "http://specs.openid.net/auth/2.0/"
            "identifier_select"
        ),
        "openid.claimed_id": (
            "http://specs.openid.net/auth/2.0/"
            "identifier_select"
        )
    }

    return RedirectResponse(
        f"{STEAM_OPENID_URL}?{urlencode(params)}"
    )


@app.get("/auth/steam/callback")
def steam_callback(
    claimed_id: str = Query(
        ...,
        alias="openid.claimed_id"
    )
):

    steam_id = extract_steam_id(
        claimed_id
    )

    if not steam_id:

        return {
            "success": False,
            "error": "No se pudo obtener el Steam ID."
        }

    return {
        "success": True,
        "steam_id": steam_id
    }


def extract_steam_id(claimed_id):

    if not claimed_id:
        return None

    parsed_url = urlparse(
        claimed_id
    )

    steam_id = (
        parsed_url.path
        .rstrip("/")
        .split("/")[-1]
    )

    if steam_id.isdigit():
        return steam_id

    return None