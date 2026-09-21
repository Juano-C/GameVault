from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from models.game import Game


class SyncService:

    MAX_WORKERS = 8
    RECENT_DAYS = 14

    def __init__(
        self,
        steam_service,
        database_service,
        backend_service
    ):

        self.steam_service = steam_service
        self.database_service = database_service
        self.backend_service = backend_service

    # ==================================================
    # FULL SYNC
    # ==================================================

    def sync_library(
        self,
        steam_id,
        api_key=None,
        on_progress=None,
        on_library_updated=None,
        on_finished=None
    ):

        try:

            existing_app_ids = (
                self.database_service
                .get_existing_app_ids()
            )

            # ------------------------------------------
            # OWN LIBRARY
            # ------------------------------------------

            if on_progress:
                on_progress(
                    "Obteniendo biblioteca propia..."
                )

            backend_response = (
                self.backend_service
                .get_owned_games(
                    steam_id
                )
            )

            if not backend_response.get(
                "success",
                False
            ):

                raise Exception(
                    backend_response.get(
                        "error",
                        "Error obteniendo biblioteca."
                    )
                )

            resolved_steam_id = (
                backend_response.get(
                    "steam_id"
                )
            )

            if resolved_steam_id:
                steam_id = resolved_steam_id

            steam_response = (
                backend_response.get(
                    "games",
                    {}
                )
            )

            steam_games = (
                steam_response.get(
                    "games",
                    []
                )
            )

            own_games = [
                self._create_own_game_data(
                    game
                )
                for game in steam_games
            ]

            own_app_ids = {
                game["app_id"]
                for game in own_games
            }

            if on_progress:

                on_progress(
                    f"{len(own_games)} "
                    "juegos propios encontrados"
                )

            # ------------------------------------------
            # FAMILY
            # ------------------------------------------

            if on_progress:

                on_progress(
                    "Obteniendo biblioteca familiar..."
                )

            try:

                family_apps = (
                    self.steam_service
                    .get_family_library(
                        steam_id
                    )
                )

                family_playtime = (
                    self.steam_service
                    .get_family_playtime(
                        steam_id
                    )
                )

            except Exception as error:

                print(
                    "Family no disponible:",
                    type(error).__name__,
                    error
                )

                family_apps = []
                family_playtime = {}

                if on_progress:

                    on_progress(
                        "Biblioteca familiar "
                        "no configurada."
                    )

            # ------------------------------------------
            # BUILD FAMILY GAMES
            # ------------------------------------------

            family_games = []

            target_steam_id = str(
                steam_id
            )

            for app in family_apps:

                app_id = app.get(
                    "appid"
                )

                if app_id is None:
                    continue

                owners = [
                    str(owner)
                    for owner in app.get(
                        "owner_steamids",
                        []
                    )
                ]

                if target_steam_id in owners:
                    continue

                if app.get(
                    "exclude_reason",
                    0
                ) != 0:

                    continue

                playtime = (
                    family_playtime.get(
                        int(app_id),
                        {}
                    )
                )

                family_games.append(
                    self._create_family_game_data(
                        app,
                        playtime
                    )
                )

            # ------------------------------------------
            # FAMILY LAST 2 WEEKS
            # ------------------------------------------

            family_playtime_2weeks = (
                self.database_service
                .update_family_playtime_history(
                    family_games
                )
            )

            for game in family_games:

                game["playtime_2weeks"] = (
                    family_playtime_2weeks.get(
                        game["app_id"],
                        0
                    )
                )

            # ------------------------------------------
            # SAVE
            # ------------------------------------------

            self.database_service.save_games(
                [
                    self._create_game_from_data(
                        game
                    )
                    for game in own_games
                ]
            )

            self.database_service.save_family_games(
                [
                    self._create_game_from_data(
                        game
                    )
                    for game in family_games
                ]
            )

            current_app_ids = (
                own_app_ids
                | {
                    game["app_id"]
                    for game in family_games
                }
            )

            self.database_service.mark_games_not_owned(
                current_app_ids
            )

            if on_library_updated:

                on_library_updated(
                    len(current_app_ids)
                )

            # ------------------------------------------
            # ACHIEVEMENTS
            # ------------------------------------------

            all_games = (
                own_games
                + family_games
            )

            new_app_ids = (
                {
                    game["app_id"]
                    for game in all_games
                }
                - existing_app_ids
            )

            self.sync_achievements(
                all_games,
                steam_id,
                new_app_ids,
                on_progress
            )

            # ------------------------------------------
            # REVIEWS
            # ------------------------------------------

            self.sync_reviews(
                steam_id,
                on_progress
            )

            if on_finished:

                on_finished(
                    len(current_app_ids)
                )

        except Exception as error:

            print(
                "ERROR DE SINCRONIZACIÓN:",
                type(error).__name__,
                error
            )

            if on_progress:

                on_progress(
                    f"Error: {error}"
                )

    # ==================================================
    # OWN GAME DATA
    # ==================================================

    def _create_own_game_data(
        self,
        steam_game
    ):

        last_played = (
            steam_game.get(
                "rtime_last_played"
            )
        )

        return {
            "app_id": steam_game["appid"],
            "name": steam_game["name"],
            "playtime_minutes": (
                steam_game.get(
                    "playtime_forever",
                    0
                )
            ),
            "last_played": (
                int(last_played)
                if last_played
                else None
            ),
            "playtime_2weeks": (
                steam_game.get(
                    "playtime_2weeks",
                    0
                )
            ),
            "library_source": "own",
            "owner_steamids": [],
            "exclude_reason": 0
        }

    # ==================================================
    # FAMILY GAME DATA
    # ==================================================

    def _create_family_game_data(
        self,
        family_app,
        playtime_data
    ):

        rt_playtime = family_app.get(
            "rt_playtime"
        )

        rt_last_played = family_app.get(
            "rt_last_played"
        )

        if rt_playtime is not None:

            try:

                minutes = int(
                    rt_playtime
                )

            except (
                TypeError,
                ValueError
            ):

                minutes = playtime_data.get(
                    "playtime_minutes",
                    0
                )

        else:

            minutes = playtime_data.get(
                "playtime_minutes",
                0
            )

        if rt_last_played:

            try:

                last_played = int(
                    rt_last_played
                )

            except (
                TypeError,
                ValueError
            ):

                last_played = (
                    playtime_data.get(
                        "last_played"
                    )
                )

        else:

            last_played = (
                playtime_data.get(
                    "last_played"
                )
            )

        return {
            "app_id": family_app["appid"],
            "name": family_app.get(
                "name",
                "Sin nombre"
            ),
            "playtime_minutes": minutes,
            "last_played": last_played,
            "playtime_2weeks": 0,
            "library_source": "family",
            "owner_steamids": [
                str(owner)
                for owner in family_app.get(
                    "owner_steamids",
                    []
                )
            ],
            "exclude_reason": family_app.get(
                "exclude_reason",
                0
            )
        }

    # ==================================================
    # GAME MODEL
    # ==================================================

    def _create_game_from_data(
        self,
        data
    ):

        return Game(
            app_id=data["app_id"],
            name=data["name"],
            playtime_minutes=data[
                "playtime_minutes"
            ],
            last_played=data[
                "last_played"
            ],
            playtime_2weeks=data[
                "playtime_2weeks"
            ],
            library_source=data[
                "library_source"
            ],
            owner_steamids=data[
                "owner_steamids"
            ],
            exclude_reason=data[
                "exclude_reason"
            ]
        )

    # ==================================================
    # ACHIEVEMENTS
    # ==================================================

    def sync_achievements(
        self,
        games,
        steam_id,
        new_app_ids,
        on_progress=None
    ):

        if not games:
            return

        games_by_id = {
            game["app_id"]: game
            for game in games
        }

        candidate_ids = set(
            games_by_id.keys()
        )

        ids_to_check = (
            self.database_service
            .get_games_needing_achievements(
                list(candidate_ids),
                days=7
            )
        )

        target_games = [
            games_by_id[app_id]
            for app_id in ids_to_check
            if app_id in games_by_id
        ]

        self.load_achievements(
            target_games,
            steam_id,
            on_progress
        )

    def load_achievements(
        self,
        games,
        steam_id,
        on_progress=None
    ):

        if not games:
            return

        total = len(games)
        completed = 0

        with ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS
        ) as executor:

            futures = {
                executor.submit(
                    self.backend_service
                    .get_achievements,
                    steam_id,
                    game["app_id"]
                ): game
                for game in games
            }

            for future in as_completed(
                futures
            ):

                game = futures[future]

                try:

                    result = future.result()

                    if result.get(
                        "success",
                        False
                    ):

                        unlocked = result.get(
                            "unlocked",
                            0
                        )

                        total_achievements = (
                            result.get(
                                "total",
                                0
                            )
                        )

                        self.database_service.update_achievements(
                            game["app_id"],
                            unlocked,
                            total_achievements
                        )

                except Exception as error:

                    print(
                        "Achievement error:",
                        game["app_id"],
                        type(error).__name__,
                        error
                    )

                completed += 1

                if on_progress:

                    on_progress(
                        f"Logros: "
                        f"{completed}/{total}"
                    )

    # ==================================================
    # REVIEWS
    # ==================================================

    def sync_reviews(
        self,
        steam_id,
        on_progress=None
    ):

        if on_progress:

            on_progress(
                "Obteniendo tus reseñas..."
            )

        try:

            profile_reviews = (
                self.steam_service
                .get_user_reviews(
                    steam_id,
                    on_progress
                )
            )

        except Exception as error:

            print(
                "Review sync error:",
                type(error).__name__,
                error
            )

            if on_progress:

                on_progress(
                    "No se pudieron obtener "
                    "tus reseñas."
                )

            return

        reviews_by_id = {}

        for review in profile_reviews:

            app_id = review.get(
                "app_id"
            )

            if app_id is None:
                continue

            reviews_by_id[int(app_id)] = {
                "app_id": int(app_id),
                "positive": bool(
                    review.get(
                        "positive",
                        False
                    )
                ),
                "text": review.get(
                    "text",
                    ""
                )
            }

        reviews = list(
            reviews_by_id.values()
        )

        self.database_service.replace_reviews(
            reviews
        )

        if on_progress:

            on_progress(
                f"{len(reviews)} "
                "reseñas tuyas sincronizadas."
            )