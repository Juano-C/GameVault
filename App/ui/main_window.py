import threading
from datetime import datetime

import customtkinter as ctk

from models.game import Game
from localization.language_manager import LanguageManager


class MainWindow:

    def __init__(
        self,
        database_service,
        sync_service,
        steam_id,
        api_key,
        config_service,
        language="es"
    ):  

        self.database_service = database_service
        self.sync_service = sync_service
        self.config_service = config_service
        self.language_manager = LanguageManager(
            language
        )

        self.steam_id = steam_id
        self.api_key = api_key

        self.current_page = 1
        self.page_size = 50

        # FILTERS
        self.library_source_filter = None
        self.completion_filter = None
        self.review_filter = None
        self.activity_filter = None
        self.result = None

        # SEARCH
        self.search_text = ""

        # SORT
        self.current_order = "playtime"
        self.current_descending = True

        # SYNC
        self.is_syncing = False

        # WINDOW
        self.window = ctk.CTk()

        self.window.title(
            "Steam GameVault"
        )

        self.window.geometry(
            "1500x800"
        )

        self.window.minsize(
            1200,
            650
        )

        self.create_header()
        self.create_filters()
        self.create_game_list()
        self.create_footer()

        self.load_games()

    # --------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------

    def t(self, key, **kwargs):

        return self.language_manager.get(
            key,
            **kwargs
        )

    def change_language(self, value):

        language_map = {
            "Español": "es",
            "English": "en",
            "Português": "pt"
        }

        language = language_map.get(value)

        if not language:
            return

        if language == self.language_manager.get_language():
            return

        self.language_manager.set_language(
            language
        )

        # Guardar idioma permanentemente
        config = self.config_service.load_config()

        if config:

            self.config_service.save_config(
                steam_id=config.get("steam_id"),
                language=language,
                family_token=config.get(
                    "family_token",
                    ""
                )
            )

        # Reconstruir interfaz
        for widget in self.window.winfo_children():
            widget.destroy()

        self.create_header()
        self.create_filters()
        self.create_game_list()
        self.create_footer()

        self.update_filter_title()
        self.load_games()

    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------

    def logout(self):

        if self.is_syncing:
            return

        self.config_service.clear_config()

        self.database_service.clear_all_data()

        self.result = "logout"

        self.window.destroy()

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    def create_header(self):

        self.header = ctk.CTkFrame(
            self.window,
            corner_radius=0
        )

        self.header.pack(
            fill="x"
        )

        title = ctk.CTkLabel(
            self.header,
            text=self.t("app_title").upper(),
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        title.pack(
            side="left",
            padx=25,
            pady=15
        )

        self.sync_status = ctk.CTkLabel(
            self.header,
            text=self.t("ready")
        )

        self.sync_status.pack(
            side="left",
            padx=10
        )

        self.library_total_label = ctk.CTkLabel(
            self.header,
            text=self.t("total_library", count=0),
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        self.library_total_label.pack(
            side="right",
            padx=25
        )

        self.language_menu = ctk.CTkOptionMenu(
            self.header,
            values=[
                "Español",
                "English",
                "Português"
            ],
            command=self.change_language,
            width=120
        )

        language_names = {
            "es": "Español",
            "en": "English",
            "pt": "Português"
        }

        self.language_menu.set(
            language_names[
                self.language_manager.get_language()
            ]
        )

        self.language_menu.pack(
            side="right",
            padx=(5, 10)
        )

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------

    def create_filters(self):

        self.filter_frame = ctk.CTkFrame(
            self.window
        )

        self.filter_frame.pack(
            fill="x",
            padx=20,
            pady=(20, 10)
        )

        label = ctk.CTkLabel(
            self.filter_frame,
            text=self.t("filters"),
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        label.pack(
            side="left",
            padx=(15, 10),
            pady=15
        )

        # PROPERTY

        property_filter_frame = ctk.CTkFrame(
            self.filter_frame,
            fg_color="transparent"
        )

        property_filter_frame.pack(
            side="left",
            padx=5
        )

        property_label = ctk.CTkLabel(
            property_filter_frame,
            text=self.t("library"),
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        )

        property_label.pack(
            anchor="w",
            pady=(0, 3)
        )

        self.property_menu = ctk.CTkOptionMenu(
            property_filter_frame,
            values=[
                self.t("all"),
                self.t("owned"),
                self.t("family")
            ],
            command=self.change_property_filter,
            width=150
        )

        self.property_menu.set(
            self.t("all")
        )

        self.property_menu.pack()

        # ACHIEVEMENTS

        achievement_filter_frame = ctk.CTkFrame(
            self.filter_frame,
            fg_color="transparent"
        )

        achievement_filter_frame.pack(
            side="left",
            padx=5
        )

        achievement_label = ctk.CTkLabel(
            achievement_filter_frame,
            text=self.t("achievements"),
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        )

        achievement_label.pack(
            anchor="w",
            pady=(0, 3)
        )

        self.achievement_menu = ctk.CTkOptionMenu(
            achievement_filter_frame,
            values=[
                self.t("all"),
                self.t("completed"),
                self.t("incomplete"),
                self.t("no_achievements")
            ],
            command=self.change_achievement_filter,
            width=160
        )

        self.achievement_menu.set(
            self.t("all")
        )

        self.achievement_menu.pack()

        # REVIEWS

        review_filter_frame = ctk.CTkFrame(
            self.filter_frame,
            fg_color="transparent"
        )

        review_filter_frame.pack(
            side="left",
            padx=5
        )

        review_label = ctk.CTkLabel(
            review_filter_frame,
            text=self.t("reviews"),
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        )

        review_label.pack(
            anchor="w",
            pady=(0, 3)
        )

        self.review_menu = ctk.CTkOptionMenu(
            review_filter_frame,
            values=[
                self.t("all"),
                self.t("with_review"),
                self.t("without_review"),
                self.t("positive_reviews"),
                self.t("negative_reviews")
            ],
            command=self.change_review_filter,
            width=150
        )

        self.review_menu.set(
            self.t("all")
        )

        self.review_menu.pack()

        # ACTIVITY

        activity_filter_frame = ctk.CTkFrame(
            self.filter_frame,
            fg_color="transparent"
        )

        activity_filter_frame.pack(
            side="left",
            padx=5
        )

        activity_label = ctk.CTkLabel(
            activity_filter_frame,
            text=self.t("activity"),
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        )

        activity_label.pack(
            anchor="w",
            pady=(0, 3)
        )

        self.activity_menu = ctk.CTkOptionMenu(
            activity_filter_frame,
            values=[
                self.t("all"),
                self.t("recently_played"),
                self.t("never_played"),
                self.t("last_two_weeks")
            ],
            command=self.change_activity_filter,
            width=210
        )

        self.activity_menu.set(
            self.t("all")
        )

        self.activity_menu.pack()

        # SORT

        sort_label = ctk.CTkLabel(
            self.filter_frame,
            text=self.t("sort_by")
        )

        sort_label.pack(
            side="left",
            padx=(25, 5)
        )

        self.sort_menu = ctk.CTkOptionMenu(
            self.filter_frame,
            values=[
                self.t("hours_desc"),
                self.t("hours_asc"),
                self.t("name_asc"),
                self.t("name_desc")
            ],
            command=self.change_sort,
            width=190
        )

        self.sort_menu.set(
            self.t("hours_desc")
        )

        self.sort_menu.pack(
            side="left",
            padx=5
        )

    # --------------------------------------------------
    # PROPERTY FILTER
    # --------------------------------------------------

    def change_property_filter(
        self,
        value
    ):

        self.current_page = 1

        if value == self.t("owned"):

            self.library_source_filter = (
                "own"
            )

        elif value == self.t("family"):

            self.library_source_filter = (
                "family"
            )

        else:

            self.library_source_filter = None

        self.update_filter_title()
        self.load_games()

    # --------------------------------------------------
    # ACHIEVEMENT FILTER
    # --------------------------------------------------

    def change_achievement_filter(
        self,
        value
    ):

        self.current_page = 1

        if value == self.t("completed"):

            self.completion_filter = (
                "completed"
            )

        elif value == self.t("incomplete"):

            self.completion_filter = (
                "incomplete"
            )

        elif value == self.t("no_achievements"):

            self.completion_filter = (
                "no_achievements"
            )

        else:

            self.completion_filter = None

        self.update_filter_title()
        self.load_games()

    # --------------------------------------------------
    # REVIEW FILTER
    # --------------------------------------------------

    def change_review_filter(
        self,
        value
    ):

        self.current_page = 1

        if value == self.t("with_review"):

            self.review_filter = {
                "has_review": True,
                "positive": None
            }

        elif value == self.t("without_review"):

            self.review_filter = {
                "has_review": False,
                "positive": None
            }

        elif value == self.t("positive_reviews"):

            self.review_filter = {
                "has_review": True,
                "positive": True
            }

        elif value == self.t("negative_reviews"):

            self.review_filter = {
                "has_review": True,
                "positive": False
            }

        else:

            self.review_filter = None

        self.update_filter_title()
        self.load_games()

    # --------------------------------------------------
    # ACTIVITY FILTER
    # --------------------------------------------------

    def change_activity_filter(
        self,
        value
    ):

        self.current_page = 1

        if value == self.t("recently_played"):

            self.activity_filter = (
                "recent"
            )

        elif value == self.t("never_played"):

            self.activity_filter = (
                "never"
            )

        elif value == self.t("last_two_weeks"):

            self.activity_filter = (
                "two_weeks"
            )

        else:

            self.activity_filter = None

        self.update_filter_title()
        self.load_games()

    # --------------------------------------------------
    # ACTIVITY FILTER LOGIC
    # --------------------------------------------------

    def filter_by_activity(
        self,
        games
    ):

        if not self.activity_filter:

            return games

        now = datetime.now().timestamp()

        fourteen_days = (
            14 * 24 * 60 * 60
        )

        cutoff = (
            now - fourteen_days
        )

        if self.activity_filter == "recent":

            return [
                game
                for game in games
                if (
                    game.last_played
                    and game.last_played >= cutoff
                )
            ]

        if self.activity_filter == "never":

            return [
                game
                for game in games
                if not game.last_played
            ]

        if self.activity_filter == "two_weeks":

            return [
                game
                for game in games
                if game.playtime_2weeks > 0
            ]

        return games

    # --------------------------------------------------
    # FILTER TITLE
    # --------------------------------------------------

    def update_filter_title(self):

        parts = []

        property_value = (
            self.property_menu.get()
        )

        achievement_value = (
            self.achievement_menu.get()
        )

        review_value = (
            self.review_menu.get()
        )

        activity_value = (
            self.activity_menu.get()
        )

        if property_value != self.t("all"):

            parts.append(
                property_value
            )

        if achievement_value != self.t("all"):

            parts.append(
                achievement_value
            )

        if review_value != self.t("all"):

            parts.append(
                review_value
            )

        if activity_value != self.t("all"):

            parts.append(
                activity_value
            )

        if self.search_text:

            parts.append(
                f"'{self.search_text}'"
            )

        if parts:

            title = self.t(
                "library_title",
                filters=" · ".join(parts)
            )

        else:

            title = self.t(
                "library_title",
                filters=self.t("all_games")
            )

        self.list_title.configure(
            text=title
        )

    # --------------------------------------------------
    # GAME LIST
    # --------------------------------------------------

    def create_game_list(self):

        self.title_search_frame = ctk.CTkFrame(
            self.window,
            fg_color="transparent"
        )

        self.title_search_frame.pack(
            fill="x",
            padx=25,
            pady=(10, 0)
        )

        self.list_title = ctk.CTkLabel(
            self.title_search_frame,
            text=self.t(
                "library_title",
                filters=self.t("all_games")
            ),
            anchor="w",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        )

        self.list_title.pack(
            side="left"
        )

        self.search_entry = ctk.CTkEntry(
            self.title_search_frame,
            width=320,
            height=36,
            placeholder_text=self.t("search_placeholder")
        )

        self.search_entry.pack(
            side="right"
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self.on_search
        )

        # Encabezado de columnas FUERA del scroll.
        # De esta forma queda fijo mientras se desplazan los juegos.
        self.column_header = ctk.CTkFrame(
            self.window,
            height=42
        )

        self.column_header.pack(
            fill="x",
            padx=25,
            pady=(0, 5)
        )

        self.list_frame = ctk.CTkScrollableFrame(
            self.window
        )

        self.list_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 10)
        )

        self.column_widths = [
            350,
            90,
            130,
            150,
            100,
            130,
            500
        ]

        for index, width in enumerate(
            self.column_widths
        ):

            self.column_header.grid_columnconfigure(
                index,
                weight=0,
                minsize=width
            )

        headers = [
            (self.t("game"), 0, "w"),
            (self.t("hours"), 1, "center"),
            (self.t("last_played"), 2, "center"),
            (self.t("last_two_weeks"), 3, "center"),
            (self.t("achievements"), 4, "center"),
            (self.t("reviews"), 5, "center"),
            (self.t("review_text"), 6, "w")
        ]

        for text, column, anchor in headers:

            label = ctk.CTkLabel(
                self.column_header,
                text=text,
                anchor=anchor,
                font=ctk.CTkFont(
                    size=13,
                    weight="bold"
                )
            )

            label.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=10,
                pady=10
            )

    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------

    def on_search(
        self,
        event=None
    ):

        self.search_text = (
            self.search_entry
            .get()
            .strip()
            .lower()
        )

        self.current_page = 1

        self.update_filter_title()

        self.load_games()

    # --------------------------------------------------
    # LOAD GAMES
    # --------------------------------------------------

    def load_games(self):

        review_has_review = None
        review_positive = None

        if self.review_filter:

            review_has_review = (
                self.review_filter[
                    "has_review"
                ]
            )

            review_positive = (
                self.review_filter[
                    "positive"
                ]
            )

        # ----------------------------------------------
        # SEARCH
        # ----------------------------------------------

        if self.search_text:

            rows = (
                self.database_service
                .get_games(
                    limit=100000,
                    offset=0,
                    completion_status=(
                        self.completion_filter
                    ),
                    has_review=(
                        review_has_review
                    ),
                    review_positive=(
                        review_positive
                    ),
                    library_source=(
                        self.library_source_filter
                    ),
                    order_by=(
                        self.current_order
                    ),
                    descending=(
                        self.current_descending
                    )
                )
            )

            games = (
                self.convert_rows_to_games(
                    rows
                )
            )

            games = [
                game
                for game in games
                if self.search_text
                in game.name.lower()
            ]

            games = (
                self.filter_by_activity(
                    games
                )
            )

            total_games = len(
                games
            )

            start = (
                (self.current_page - 1)
                * self.page_size
            )

            end = start + self.page_size

            games = games[
                start:end
            ]

            self.display_games(
                games
            )

            self.update_footer(
                search_total=total_games
            )

            return

        # ----------------------------------------------
        # WITHOUT SEARCH
        # ----------------------------------------------

        rows = (
            self.database_service
            .get_games(
                limit=self.page_size,
                offset=(
                    self.current_page - 1
                ) * self.page_size,
                completion_status=(
                    self.completion_filter
                ),
                has_review=(
                    review_has_review
                ),
                review_positive=(
                    review_positive
                ),
                library_source=(
                    self.library_source_filter
                ),
                order_by=(
                    self.current_order
                ),
                descending=(
                    self.current_descending
                )
            )
        )

        games = (
            self.convert_rows_to_games(
                rows
            )
        )

        if self.activity_filter:

            games = (
                self.filter_by_activity(
                    games
                )
            )

            if len(games) < self.page_size:

                all_rows = (
                    self.database_service
                    .get_games(
                        limit=100000,
                        offset=0,
                        completion_status=(
                            self.completion_filter
                        ),
                        has_review=(
                            review_has_review
                        ),
                        review_positive=(
                            review_positive
                        ),
                        library_source=(
                            self.library_source_filter
                        ),
                        order_by=(
                            self.current_order
                        ),
                        descending=(
                            self.current_descending
                        )
                    )
                )

                all_games = (
                    self.convert_rows_to_games(
                        all_rows
                    )
                )

                all_games = (
                    self.filter_by_activity(
                        all_games
                    )
                )

                start = (
                    (self.current_page - 1)
                    * self.page_size
                )

                end = (
                    start + self.page_size
                )

                games = all_games[
                    start:end
                ]

        self.display_games(
            games
        )

        self.update_footer()

    # --------------------------------------------------
    # CONVERT DATABASE ROWS
    # --------------------------------------------------

    def convert_rows_to_games(
        self,
        rows
    ):

        games = []

        for row in rows:

            game = Game(
                app_id=row[0],
                name=row[1],
                playtime_minutes=row[2],
                last_played=row[3],
                playtime_2weeks=row[4],
                achievements_unlocked=row[5],
                achievements_total=row[6],
                has_review=bool(row[8]),
                review_positive=(
                    None
                    if row[9] is None
                    else bool(row[9])
                ),
                review_text=row[10],
                library_source=row[11],
                owner_steamids=(
                    []
                    if row[12] is None
                    else row[12]
                ),
                exclude_reason=(
                    row[13]
                    if row[13] is not None
                    else 0
                )
            )

            games.append(
                game
            )

        return games

    # --------------------------------------------------
    # DISPLAY GAMES
    # --------------------------------------------------

    def display_games(
        self,
        games
    ):

        children = (
            self.list_frame.winfo_children()
        )

        for widget in children:
            widget.destroy()

        if not games:

            empty_label = ctk.CTkLabel(
                self.list_frame,
                text=(
                    self.t("no_games")
                    + "\n\n"
                    + self.t("sync_to_load")
                ),
                font=ctk.CTkFont(
                    size=18
                )
            )

            empty_label.pack(
                pady=100
            )

            return

        for game in games:

            game_row = ctk.CTkFrame(
                self.list_frame
            )

            game_row.pack(
                fill="x",
                padx=5,
                pady=3
            )

            # --------------------------------------
            # COLUMNS
            # --------------------------------------

            for index, width in enumerate(
                self.column_widths
            ):

                game_row.grid_columnconfigure(
                    index,
                    weight=0,
                    minsize=width
                )

            # --------------------------------------
            # GAME
            # --------------------------------------

            name_label = ctk.CTkLabel(
                game_row,
                text=game.name,
                anchor="w",
                font=ctk.CTkFont(
                    size=14,
                    weight="bold"
                )
            )

            name_label.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=(15, 10),
                pady=15
            )

            # --------------------------------------
            # HOURS
            # --------------------------------------

            hours_label = ctk.CTkLabel(
                game_row,
                text=(
                    f"{game.playtime_hours:.1f} h"
                ),
                anchor="center"
            )

            hours_label.grid(
                row=0,
                column=1,
                sticky="ew",
                padx=10,
                pady=15
            )

            # --------------------------------------
            # LAST PLAYED
            # --------------------------------------

            if game.last_played:

                try:

                    last_played_date = (
                        datetime.fromtimestamp(
                            game.last_played
                        ).strftime(
                            "%d/%m/%Y"
                        )
                    )

                except (
                    ValueError,
                    OSError,
                    OverflowError
                ):

                    last_played_date = (
                        "No disponible"
                    )

            else:

                last_played_date = self.t("never")

            last_played_label = ctk.CTkLabel(
                game_row,
                text=last_played_date,
                anchor="center"
            )

            last_played_label.grid(
                row=0,
                column=2,
                sticky="ew",
                padx=10,
                pady=15
            )

            # --------------------------------------
            # LAST TWO WEEKS
            # --------------------------------------

            two_weeks_label = ctk.CTkLabel(
                game_row,
                text=(
                    f"{game.playtime_2weeks_hours:.1f} h"
                ),
                anchor="center"
            )

            two_weeks_label.grid(
                row=0,
                column=3,
                sticky="ew",
                padx=10,
                pady=15
            )

            # --------------------------------------
            # ACHIEVEMENTS
            # --------------------------------------

            achievements_text = (
                f"{game.achievements_unlocked}"
                f"/"
                f"{game.achievements_total}"
            )

            achievements_label = ctk.CTkLabel(
                game_row,
                text=achievements_text,
                anchor="center"
            )

            achievements_label.grid(
                row=0,
                column=4,
                sticky="ew",
                padx=10,
                pady=15
            )

            # --------------------------------------
            # REVIEW STATUS
            # --------------------------------------

            if not game.has_review:

                review_status = self.t("no_review")
                review_color = "#3a3a3a"

            elif game.review_positive:

                review_status = self.t("positive")
                review_color = "#16a34a"

            else:

                review_status = self.t("negative")
                review_color = "#dc2626"

            review_label = ctk.CTkLabel(
                game_row,
                text=review_status,
                anchor="center",
                corner_radius=8,
                fg_color=review_color,
                text_color="white",
                width=110
            )

            review_label.grid(
                row=0,
                column=5,
                sticky="ew",
                padx=10,
                pady=12
            )

            # --------------------------------------
            # REVIEW TEXT
            # --------------------------------------

            if not game.has_review:

                review_display = self.t("no_review")

            else:

                review_display = (
                    game.review_text
                    or self.t("no_text")
                )

                review_display = (
                    review_display
                    .replace(
                        "\n",
                        " "
                    )
                    .strip()
                )

            review_text_label = ctk.CTkLabel(
                game_row,
                text=review_display,
                anchor="w",
                justify="left",
                wraplength=470
            )

            review_text_label.grid(
                row=0,
                column=6,
                sticky="ew",
                padx=10,
                pady=10
            )

            # --------------------------------------
            # DOUBLE CLICK
            # --------------------------------------

            widgets = [
                game_row,
                name_label,
                hours_label,
                last_played_label,
                two_weeks_label,
                achievements_label,
                review_label,
                review_text_label
            ]

            for widget in widgets:

                widget.bind(
                    "<Double-Button-1>",
                    lambda event,
                    selected_game=game:
                    self.show_game_details(
                        selected_game
                    )
                )

    # --------------------------------------------------
    # GAME DETAILS
    # --------------------------------------------------

    def show_game_details(
        self,
        game
    ):

        detail_window = ctk.CTkToplevel(
            self.window
        )

        detail_window.title(
            game.name
        )

        detail_window.geometry(
            "750x550"
        )

        detail_window.minsize(
            600,
            450
        )

        title = ctk.CTkLabel(
            detail_window,
            text=game.name,
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            )
        )

        title.pack(
            padx=25,
            pady=(25, 10)
        )

        if game.library_source == "family":

            property_text = self.t(
                "property_family"
            )

        else:

            property_text = self.t(
                "property_own"
            )

        property_label = ctk.CTkLabel(
            detail_window,
            text=property_text,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        property_label.pack(
            padx=25,
            pady=5
        )

        # ----------------------------------------------
        # ACHIEVEMENTS
        # ----------------------------------------------

        achievements_text = self.t(
            "achievements_count",
            unlocked=game.achievements_unlocked,
            total=game.achievements_total
        )

        achievements_label = ctk.CTkLabel(
            detail_window,
            text=achievements_text,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        achievements_label.pack(
            padx=25,
            pady=5
        )

        # ----------------------------------------------
        # REVIEW
        # ----------------------------------------------

        if not game.has_review:

            status_text = self.t(
                "no_review_detail"
            )

        elif game.review_positive:

            status_text = self.t(
                "positive_review_detail"
            )

        else:

            status_text = self.t(
                "negative_review_detail"
            )

        status = ctk.CTkLabel(
            detail_window,
            text=status_text,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        )

        status.pack(
            padx=25,
            pady=10
        )

        text_box = ctk.CTkTextbox(
            detail_window,
            wrap="word"
        )

        text_box.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        if game.has_review:

            text_box.insert(
                "1.0",
                game.review_text
                or self.t("no_text")
            )

        else:

            text_box.insert(
                "1.0",
                self.t("no_review_for_game")
            )

        text_box.configure(
            state="disabled"
        )

    # --------------------------------------------------
    # SORT
    # --------------------------------------------------

    def change_sort(
        self,
        sort_type
    ):

        self.current_page = 1

        if sort_type == self.t("hours_desc"):

            self.current_order = "playtime"
            self.current_descending = True

        elif sort_type == self.t("hours_asc"):

            self.current_order = "playtime"
            self.current_descending = False

        elif sort_type == self.t("name_asc"):

            self.current_order = "name"
            self.current_descending = False

        elif sort_type == self.t("name_desc"):

            self.current_order = "name"
            self.current_descending = True

        self.load_games()

    # --------------------------------------------------
    # PAGINATION
    # --------------------------------------------------

    def get_filtered_total(
        self
    ):

        review_has_review = None
        review_positive = None

        if self.review_filter:

            review_has_review = (
                self.review_filter[
                    "has_review"
                ]
            )

            review_positive = (
                self.review_filter[
                    "positive"
                ]
            )

        rows = (
            self.database_service
            .get_games(
                limit=100000,
                offset=0,
                completion_status=(
                    self.completion_filter
                ),
                has_review=(
                    review_has_review
                ),
                review_positive=(
                    review_positive
                ),
                library_source=(
                    self.library_source_filter
                ),
                order_by=(
                    self.current_order
                ),
                descending=(
                    self.current_descending
                )
            )
        )

        games = (
            self.convert_rows_to_games(
                rows
            )
        )

        if self.search_text:

            games = [
                game
                for game in games
                if self.search_text
                in game.name.lower()
            ]

        games = (
            self.filter_by_activity(
                games
            )
        )

        return len(
            games
        )

    def next_page(self):

        total_games = (
            self.get_filtered_total()
        )

        max_page = max(
            1,
            (
                total_games
                + self.page_size
                - 1
            )
            // self.page_size
        )

        if self.current_page < max_page:

            self.current_page += 1

            self.load_games()

    def previous_page(self):

        if self.current_page > 1:

            self.current_page -= 1

            self.load_games()

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------

    def update_footer(
        self,
        search_total=None
    ):

        if search_total is not None:

            total_games = search_total

        else:

            total_games = (
                self.get_filtered_total()
            )

        total_library = (
            self.database_service
            .get_game_count()
        )

        self.library_total_label.configure(
            text=self.t(
                "total_library",
                count=total_library
            )
        )

        if total_games == 0:

            self.total_label.configure(
                text=self.t("total", count=0)
            )

            self.page_label.configure(
                text=self.t("page", current=0, total=0)
            )

            return

        total_pages = (
            total_games
            + self.page_size
            - 1
        ) // self.page_size

        self.total_label.configure(
            text=self.t(
                "total",
                count=total_games
            )
        )

        self.page_label.configure(
            text=self.t(
                "page",
                current=self.current_page,
                total=total_pages
            )
        )

    # --------------------------------------------------
    # FOOTER CREATION
    # --------------------------------------------------

    def create_footer(self):

        self.footer = ctk.CTkFrame(
            self.window,
            corner_radius=0
        )

        self.footer.pack(
            fill="x"
        )

        self.total_label = ctk.CTkLabel(
            self.footer,
            text=self.t("total", count=0)
        )

        self.total_label.pack(
            side="left",
            padx=25,
            pady=15
        )

        self.page_label = ctk.CTkLabel(
            self.footer,
            text=self.t("page", current=0, total=0)
        )

        self.page_label.pack(
            side="left",
            padx=25,
            pady=15
        )

        self.previous_button = ctk.CTkButton(
            self.footer,
            text=self.t("previous"),
            command=self.previous_page
        )

        self.previous_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        self.next_button = ctk.CTkButton(
            self.footer,
            text=self.t("next"),
            command=self.next_page
        )

        self.next_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        self.sync_button = ctk.CTkButton(
            self.footer,
            text=self.t("sync_steam"),
            command=self.sync_steam
        )

        self.sync_button.pack(
            side="right",
            padx=25,
            pady=10
        )

        self.logout_button = ctk.CTkButton(
            self.footer,
            text="Cerrar sesión",
            command=self.logout,
            fg_color="#7f1d1d",
            hover_color="#991b1b"
        )

        self.logout_button.pack(
            side="right",
            padx=(5, 10),
            pady=10
        )

    # --------------------------------------------------
    # SYNCHRONIZATION
    # --------------------------------------------------

    def sync_steam(self):

        if self.is_syncing:
            return

        self.is_syncing = True

        self.sync_button.configure(
            state="disabled",
            text=self.t("syncing")
        )

        self.language_menu.configure(
            state="disabled"
        )

        self.sync_status.configure(
            text=self.t("updating_library")
        )

        thread = threading.Thread(
            target=self._run_sync,
            daemon=True
        )

        thread.start()

    def _run_sync(self):

        self.sync_service.sync_library(
            steam_id=self.steam_id,
            api_key=self.api_key,
            on_progress=self.sync_progress,
            on_library_updated=(
                self.library_updated
            ),
            on_finished=self.sync_finished
        )

    # --------------------------------------------------
    # PROGRESS
    # --------------------------------------------------

    def sync_progress(
        self,
        message
    ):

        self.window.after(
            0,
            lambda:
            self.sync_status.configure(
                text=message
            )
        )

    # --------------------------------------------------
    # LIBRARY UPDATED
    # --------------------------------------------------

    def library_updated(
        self,
        total_games
    ):

        self.window.after(
            0,
            lambda:
            self.finish_library_sync(
                total_games
            )
        )

    def finish_library_sync(
        self,
        total_games
    ):

        self.sync_status.configure(
            text=self.t(
                "library_updated",
                count=total_games
            )
        )

        self.current_page = 1

        self.load_games()

    # --------------------------------------------------
    # FINISHED
    # --------------------------------------------------

    def sync_finished(
        self,
        total_games
    ):

        self.window.after(
            0,
            lambda:
            self.finish_sync(
                total_games
            )
        )

    def finish_sync(
        self,
        total_games
    ):

        self.is_syncing = False

        self.sync_button.configure(
            state="normal",
            text=self.t("sync_steam")
        )

        self.language_menu.configure(
            state="normal"
        )

        self.sync_status.configure(
            text=self.t(
                "sync_completed",
                count=total_games
            )
        )

        self.current_page = 1

        self.load_games()

    # --------------------------------------------------
    # RUN
    # --------------------------------------------------

    def run(self):

        self.window.mainloop()

        return self.result