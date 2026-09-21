import customtkinter as ctk


class SetupWindow:

    TRANSLATIONS = {
        "es": {
            "title": "STEAM GAMEVAULT",
            "subtitle": "Configuración inicial",
            "steam_profile": "Perfil de Steam",
            "steam_placeholder": "Steam ID o URL de tu perfil",
            "steam_help": (
                "Ejemplo:\n"
                "76561198000000000\n"
                "https://steamcommunity.com/id/usuario"
            ),
            "family_title": "Steam Family (opcional)",
            "family_help": (
                "Para sincronizar tu biblioteca de Steam Family, "
                "introducí tu Family Access Token.\n"
                "Si lo dejás vacío, solo se sincronizará "
                "tu biblioteca propia."
            ),
            "family_placeholder": "Steam Family Access Token",
            "language": "Idioma",
            "save": "Guardar y continuar",
            "error": "Introducí tu Steam ID o URL de perfil."
        },

        "en": {
            "title": "STEAM GAMEVAULT",
            "subtitle": "Initial configuration",
            "steam_profile": "Steam Profile",
            "steam_placeholder": "Steam ID or profile URL",
            "steam_help": (
                "Example:\n"
                "76561198000000000\n"
                "https://steamcommunity.com/id/username"
            ),
            "family_title": "Steam Family (optional)",
            "family_help": (
                "To synchronize your Steam Family library, "
                "enter your Family Access Token.\n"
                "If you leave it empty, only your own "
                "library will be synchronized."
            ),
            "family_placeholder": "Steam Family Access Token",
            "language": "Language",
            "save": "Save and continue",
            "error": "Enter your Steam ID or profile URL."
        },

        "pt": {
            "title": "STEAM GAMEVAULT",
            "subtitle": "Configuração inicial",
            "steam_profile": "Perfil da Steam",
            "steam_placeholder": "Steam ID ou URL do perfil",
            "steam_help": (
                "Exemplo:\n"
                "76561198000000000\n"
                "https://steamcommunity.com/id/usuario"
            ),
            "family_title": "Steam Family (opcional)",
            "family_help": (
                "Para sincronizar sua biblioteca do Steam Family, "
                "insira seu Family Access Token.\n"
                "Se deixar vazio, apenas sua biblioteca própria "
                "será sincronizada."
            ),
            "family_placeholder": "Steam Family Access Token",
            "language": "Idioma",
            "save": "Salvar e continuar",
            "error": "Insira seu Steam ID ou URL do perfil."
        }
    }

    LANGUAGE_NAMES = {
        "es": "Español",
        "en": "English",
        "pt": "Português"
    }

    LANGUAGE_CODES = {
        "Español": "es",
        "English": "en",
        "Português": "pt"
    }

    def __init__(self, config_service):

        self.config_service = config_service
        self.result = None

        self.current_language = "es"

        self.window = ctk.CTk()
        self.window.title("Steam GameVault")
        self.window.geometry("560x680")
        self.window.resizable(False, False)

        self.create_interface()

    def create_interface(self):

        container = ctk.CTkFrame(
            self.window,
            fg_color="transparent"
        )

        container.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=30
        )

        self.title_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        self.title_label.pack(
            pady=(5, 5)
        )

        self.subtitle_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=16)
        )

        self.subtitle_label.pack(
            pady=(0, 25)
        )

        self.steam_label = ctk.CTkLabel(
            container,
            text="",
            anchor="w",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        )

        self.steam_label.pack(
            fill="x",
            pady=(0, 5)
        )

        self.steam_id_entry = ctk.CTkEntry(
            container,
            height=38
        )

        self.steam_id_entry.pack(
            fill="x"
        )

        self.steam_help = ctk.CTkLabel(
            container,
            text="",
            anchor="w",
            justify="left",
            text_color="#888888",
            font=ctk.CTkFont(size=11)
        )

        self.steam_help.pack(
            fill="x",
            pady=(5, 0)
        )

        self.family_title = ctk.CTkLabel(
            container,
            text="",
            anchor="w",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        )

        self.family_title.pack(
            fill="x",
            pady=(25, 5)
        )

        self.family_help = ctk.CTkLabel(
            container,
            text="",
            anchor="w",
            justify="left",
            text_color="#888888",
            font=ctk.CTkFont(size=11)
        )

        self.family_help.pack(
            fill="x",
            pady=(0, 8)
        )

        self.family_token_entry = ctk.CTkEntry(
            container,
            height=38,
            show="*"
        )

        self.family_token_entry.pack(
            fill="x"
        )

        self.language_label = ctk.CTkLabel(
            container,
            text="",
            anchor="w",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        )

        self.language_label.pack(
            fill="x",
            pady=(20, 5)
        )

        self.language_menu = ctk.CTkOptionMenu(
            container,
            values=[
                "Español",
                "English",
                "Português"
            ],
            width=180,
            height=38,
            command=self.change_language
        )

        self.language_menu.set(
            "Español"
        )

        self.language_menu.pack(
            anchor="w"
        )

        self.error_label = ctk.CTkLabel(
            container,
            text="",
            text_color="#dc2626"
        )

        self.error_label.pack(
            pady=(10, 0)
        )

        self.save_button = ctk.CTkButton(
            container,
            text="",
            height=40,
            command=self.save
        )

        self.save_button.pack(
            fill="x",
            pady=(10, 0)
        )

        self.update_texts()

    def change_language(self, value):

        language = self.LANGUAGE_CODES.get(
            value
        )

        if not language:
            return

        self.current_language = language

        self.update_texts()

        # Si ya existe configuración, guardamos
        # inmediatamente el nuevo idioma.
        config = self.config_service.load_config()

        if config:

            self.config_service.save_config(
                steam_id=config.get(
                    "steam_id"
                ),
                language=language,
                family_token=config.get(
                    "family_token",
                    ""
                )
            )

    def update_texts(self):

        texts = self.TRANSLATIONS[
            self.current_language
        ]

        self.title_label.configure(
            text=texts["title"]
        )

        self.subtitle_label.configure(
            text=texts["subtitle"]
        )

        self.steam_label.configure(
            text=texts["steam_profile"]
        )

        self.steam_id_entry.configure(
            placeholder_text=texts[
                "steam_placeholder"
            ]
        )

        self.steam_help.configure(
            text=texts["steam_help"]
        )

        self.family_title.configure(
            text=texts["family_title"]
        )

        self.family_help.configure(
            text=texts["family_help"]
        )

        self.family_token_entry.configure(
            placeholder_text=texts[
                "family_placeholder"
            ]
        )

        self.language_label.configure(
            text=texts["language"]
        )

        self.save_button.configure(
            text=texts["save"]
        )

        # No borrar un error existente
        # salvo que haya cambio de idioma.
        if self.error_label.cget("text"):

            self.error_label.configure(
                text=texts["error"]
            )

    def get_language_code(self):

        return self.current_language

    def save(self):

        steam_input = (
            self.steam_id_entry
            .get()
            .strip()
        )

        if not steam_input:

            self.show_error(
                self.TRANSLATIONS[
                    self.current_language
                ]["error"]
            )

            return

        family_token = (
            self.family_token_entry
            .get()
            .strip()
        )

        language = self.get_language_code()

        self.config_service.save_config(
            steam_id=steam_input,
            language=language,
            family_token=family_token
        )

        self.result = {
            "steam_id": steam_input,
            "language": language,
            "family_token": family_token
        }

        self.window.destroy()

    def show_error(self, message):

        self.error_label.configure(
            text=message
        )

    def run(self):

        self.window.mainloop()

        return self.result