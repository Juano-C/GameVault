
class StatisticsService:

    def get_most_played_games(self, games, limit=10):
        sorted_games = sorted(
            games,
            key=lambda game: game.playtime_minutes,
            reverse=True
        )

        return sorted_games[:limit]

    def get_total_playtime(self, games):
        total_minutes = sum(
            game.playtime_minutes for game in games
        )

        return total_minutes / 60
