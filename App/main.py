from services.config_service import ConfigService
from services.database_service import DatabaseService
from services.steam_service import SteamService
from services.sync_service import SyncService
from services.backend_service import BackendService

from ui.main_window import MainWindow
from ui.setup_window import SetupWindow


def main():

    while True:

        config_service = ConfigService()

        config = config_service.load_config()

        # ------------------------------------------
        # SETUP
        # ------------------------------------------

        if not config_service.has_config():

            setup_window = SetupWindow(
                config_service
            )

            result = setup_window.run()

            if not result:
                return

            steam_input = result[
                "steam_id"
            ]

            language = result[
                "language"
            ]

            family_token = result.get(
                "family_token",
                ""
            )

        else:

            steam_input = config.get(
                "steam_id"
            )

            language = config.get(
                "language",
                "es"
            )

            family_token = config.get(
                "family_token",
                ""
            )

        # ------------------------------------------
        # SERVICES
        # ------------------------------------------

        database_service = DatabaseService()

        steam_service = SteamService(
            family_token=family_token
        )

        backend_service = BackendService()

        sync_service = SyncService(
            steam_service,
            database_service,
            backend_service
        )

        # ------------------------------------------
        # RESOLVE STEAM ID
        # ------------------------------------------

        active_steam_id = steam_input

        try:

            backend_data = (
                backend_service
                .get_owned_games(
                    steam_input
                )
            )

            if not backend_data.get(
                "success",
                False
            ):

                print(
                    "Error resolviendo Steam:",
                    backend_data.get(
                        "error"
                    )
                )

            else:

                resolved_steam_id = (
                    backend_data.get(
                        "steam_id"
                    )
                )

                if resolved_steam_id:

                    active_steam_id = (
                        resolved_steam_id
                    )

                games = backend_data.get(
                    "games",
                    {}
                )

                game_count = games.get(
                    "game_count",
                    0
                )

                print(
                    "Backend conectado. "
                    f"Juegos encontrados: "
                    f"{game_count}"
                )

                print(
                    "Steam ID activo:",
                    active_steam_id
                )

        except Exception as error:

            print(
                "Error conectando con el backend:",
                error
            )

        # ------------------------------------------
        # MAIN WINDOW
        # ------------------------------------------

        window = MainWindow(
            database_service,
            sync_service,
            active_steam_id,
            None,
            config_service,
            language
        )

        result = window.run()

        database_service.close()

        # ------------------------------------------
        # LOGOUT
        # ------------------------------------------

        if result == "logout":

            print(
                "Sesión cerrada."
            )

            continue

        return


if __name__ == "__main__":
    main()