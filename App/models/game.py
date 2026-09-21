class Game:

    def __init__(
        self,
        app_id,
        name,
        playtime_minutes=0,
        last_played=None,
        playtime_2weeks=0,
        achievements_unlocked=0,
        achievements_total=0,
        has_review=False,
        review_positive=None,
        review_text=None,
        library_source="own",
        owner_steamids=None,
        exclude_reason=0
    ):
        self.app_id = app_id
        self.name = name

        self.playtime_minutes = playtime_minutes
        self.last_played = last_played
        self.playtime_2weeks = playtime_2weeks

        self.achievements_unlocked = (
            achievements_unlocked
        )

        self.achievements_total = (
            achievements_total
        )

        self.has_review = has_review
        self.review_positive = review_positive
        self.review_text = review_text

        self.library_source = library_source

        self.owner_steamids = (
            owner_steamids
            if owner_steamids is not None
            else []
        )

        self.exclude_reason = exclude_reason

    @property
    def playtime_hours(self):
        return self.playtime_minutes / 60

    @property
    def playtime_2weeks_hours(self):
        return self.playtime_2weeks / 60

    @property
    def achievement_percentage(self):
        if self.achievements_total == 0:
            return 0

        return (
            self.achievements_unlocked
            / self.achievements_total
        ) * 100

    @property
    def is_family_game(self):
        return self.library_source == "family"

    @property
    def is_owned_game(self):
        return self.library_source == "own"