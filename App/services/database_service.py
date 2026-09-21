import json
import sqlite3
from datetime import datetime
from pathlib import Path


class DatabaseService:

    def __init__(self, db_path="data/gamevault.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )

        self.connection.execute(
            "PRAGMA journal_mode=WAL"
        )
        self.connection.execute(
            "PRAGMA foreign_keys=ON"
        )

        self.create_tables()
        self.migrate_database()
        self.create_indexes()

    def create_tables(self):

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS games (
                app_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                playtime_minutes INTEGER DEFAULT 0,
                last_played INTEGER,
                playtime_2weeks INTEGER DEFAULT 0,
                achievements_unlocked INTEGER DEFAULT 0,
                achievements_total INTEGER DEFAULT 0,
                completion_status TEXT DEFAULT 'no_achievements',
                has_review INTEGER DEFAULT 0,
                review_positive INTEGER,
                review_text TEXT,
                achievements_checked_at TEXT,
                review_checked_at TEXT,
                owned INTEGER DEFAULT 1,
                last_synced TEXT,
                library_source TEXT DEFAULT 'own',
                owner_steamids TEXT DEFAULT '[]',
                exclude_reason INTEGER DEFAULT 0
            )
        """)
        self.connection.commit()

    def migrate_database(self):

        cursor = self.connection.cursor()

        columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(games)"
            ).fetchall()
        }

        migrations = {
            "achievements_checked_at": "TEXT",
            "review_checked_at": "TEXT",
            "owned": "INTEGER DEFAULT 1",
            "last_synced": "TEXT",
            "library_source": "TEXT DEFAULT 'own'",
            "owner_steamids": "TEXT DEFAULT '[]'",
            "exclude_reason": "INTEGER DEFAULT 0",
        }

        for column, definition in migrations.items():

            if column not in columns:

                cursor.execute(
                    f"""
                    ALTER TABLE games
                    ADD COLUMN {column} {definition}
                    """
                )

        self.connection.commit()

    def create_indexes(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_owned
            ON games(owned)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_source
            ON games(library_source)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_playtime
            ON games(playtime_minutes DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_review
            ON games(has_review, review_positive)
        """)

        self.connection.commit()

    def get_existing_app_ids(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT app_id
            FROM games
        """)

        return {
            row[0]
            for row in cursor.fetchall()
        }

    def save_games(self, games):

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor = self.connection.cursor()

        for game in games:

            completion_status = (
                "no_achievements"
                if game.achievements_total == 0
                else (
                    "completed"
                    if game.achievements_unlocked
                    == game.achievements_total
                    else "incomplete"
                )
            )

            cursor.execute("""
                INSERT INTO games (
                    app_id, name, playtime_minutes,
                    last_played, playtime_2weeks,
                    achievements_unlocked,
                    achievements_total,
                    completion_status,
                    has_review,
                    review_positive,
                    review_text,
                    owned,
                    last_synced,
                    library_source,
                    owner_steamids,
                    exclude_reason
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(app_id)
                DO UPDATE SET
                    name = excluded.name,
                    playtime_minutes = excluded.playtime_minutes,
                    last_played = excluded.last_played,
                    playtime_2weeks = excluded.playtime_2weeks,
                    owned = 1,
                    library_source = 'own',
                    owner_steamids = excluded.owner_steamids,
                    exclude_reason = excluded.exclude_reason,
                    last_synced = excluded.last_synced
            """, (
                game.app_id,
                game.name,
                game.playtime_minutes,
                game.last_played,
                game.playtime_2weeks,
                game.achievements_unlocked,
                game.achievements_total,
                completion_status,
                int(game.has_review),
                (
                    None
                    if game.review_positive is None
                    else int(game.review_positive)
                ),
                game.review_text,
                1,
                now,
                "own",
                json.dumps(game.owner_steamids),
                game.exclude_reason
            ))

        self.connection.commit()

    def save_family_games(self, games):

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor = self.connection.cursor()

        for game in games:

            cursor.execute("""
                INSERT INTO games (
                    app_id, name, playtime_minutes,
                    last_played, playtime_2weeks,
                    achievements_unlocked,
                    achievements_total,
                    completion_status,
                    has_review,
                    review_positive,
                    review_text,
                    owned,
                    last_synced,
                    library_source,
                    owner_steamids,
                    exclude_reason
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(app_id)
                DO UPDATE SET
                    name = excluded.name,
                    library_source =
                        CASE
                            WHEN games.library_source = 'own'
                            THEN 'own'
                            ELSE 'family'
                        END,
                    owner_steamids =
                        excluded.owner_steamids,
                    exclude_reason =
                        excluded.exclude_reason,
                    playtime_minutes =
                        CASE
                            WHEN games.library_source = 'own'
                            THEN games.playtime_minutes
                            ELSE excluded.playtime_minutes
                        END,
                    last_played =
                        CASE
                            WHEN games.library_source = 'own'
                            THEN games.last_played
                            ELSE excluded.last_played
                        END,
                    playtime_2weeks =
                        CASE
                            WHEN games.library_source = 'own'
                            THEN games.playtime_2weeks
                            ELSE excluded.playtime_2weeks
                        END,
                    owned = 1,
                    last_synced = excluded.last_synced
            """, (
                game.app_id,
                game.name,
                game.playtime_minutes,
                game.last_played,
                game.playtime_2weeks,
                0,
                0,
                "no_achievements",
                0,
                None,
                None,
                1,
                now,
                "family",
                json.dumps(game.owner_steamids),
                game.exclude_reason
            ))

        self.connection.commit()

    def mark_games_not_owned(self, current_app_ids):

        cursor = self.connection.cursor()

        if not current_app_ids:

            cursor.execute("""
                UPDATE games
                SET owned = 0
            """)

        else:

            placeholders = ",".join(
                "?" for _ in current_app_ids
            )

            cursor.execute(
                f"""
                UPDATE games
                SET owned = 0
                WHERE app_id NOT IN ({placeholders})
                """,
                list(current_app_ids)
            )

        self.connection.commit()

    def update_achievements(
        self,
        app_id,
        unlocked,
        total
    ):

        if total == 0:
            status = "no_achievements"
        elif unlocked == total:
            status = "completed"
        else:
            status = "incomplete"

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        self.connection.execute("""
            UPDATE games
            SET
                achievements_unlocked = ?,
                achievements_total = ?,
                completion_status = ?,
                achievements_checked_at = ?
            WHERE app_id = ?
        """, (
            unlocked,
            total,
            status,
            now,
            app_id
        ))

        self.connection.commit()

    def replace_reviews(self, reviews):

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor = self.connection.cursor()

        try:

            cursor.execute("BEGIN")

            # IMPORTANT:
            # Every review currently stored is cleared first.
            # Then only reviews returned for the configured
            # Steam user are inserted.
            cursor.execute("""
                UPDATE games
                SET
                    has_review = 0,
                    review_positive = NULL,
                    review_text = NULL,
                    review_checked_at = ?
                WHERE owned = 1
            """, (now,))

            for review in reviews:

                app_id = review.get("app_id")

                if app_id is None:
                    continue

                cursor.execute("""
                    UPDATE games
                    SET
                        has_review = 1,
                        review_positive = ?,
                        review_text = ?,
                        review_checked_at = ?
                    WHERE app_id = ?
                      AND owned = 1
                """, (
                    1 if review.get(
                        "positive",
                        False
                    ) else 0,
                    review.get("text", ""),
                    now,
                    int(app_id)
                ))

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

    def get_reviewed_app_ids(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT app_id
            FROM games
            WHERE owned = 1
              AND has_review = 1
        """)

        return {
            row[0]
            for row in cursor.fetchall()
        }

    def get_game_count(
        self,
        completion_status=None,
        has_review=None,
        review_positive=None,
        library_source=None
    ):

        query = """
            SELECT COUNT(*)
            FROM games
            WHERE owned = 1
        """

        conditions = []
        parameters = []

        if completion_status is not None:
            conditions.append(
                "completion_status = ?"
            )
            parameters.append(
                completion_status
            )

        if has_review is not None:
            conditions.append(
                "has_review = ?"
            )
            parameters.append(
                int(has_review)
            )

        if review_positive is not None:
            conditions.append(
                "review_positive = ?"
            )
            parameters.append(
                int(review_positive)
            )

        if library_source is not None:
            conditions.append(
                "library_source = ?"
            )
            parameters.append(
                library_source
            )

        if conditions:
            query += " AND " + " AND ".join(
                conditions
            )

        cursor = self.connection.cursor()
        cursor.execute(
            query,
            parameters
        )

        return cursor.fetchone()[0]

    def get_games(
        self,
        limit=50,
        offset=0,
        completion_status=None,
        has_review=None,
        review_positive=None,
        library_source=None,
        order_by="playtime",
        descending=True
    ):

        query = """
            SELECT
                app_id,
                name,
                playtime_minutes,
                CAST(last_played AS INTEGER),
                playtime_2weeks,
                achievements_unlocked,
                achievements_total,
                completion_status,
                has_review,
                review_positive,
                review_text,
                library_source,
                owner_steamids,
                exclude_reason
            FROM games
            WHERE owned = 1
        """

        conditions = []
        parameters = []

        if completion_status is not None:
            conditions.append(
                "completion_status = ?"
            )
            parameters.append(
                completion_status
            )

        if has_review is not None:
            conditions.append(
                "has_review = ?"
            )
            parameters.append(
                int(has_review)
            )

        if review_positive is not None:
            conditions.append(
                "review_positive = ?"
            )
            parameters.append(
                int(review_positive)
            )

        if library_source is not None:
            conditions.append(
                "library_source = ?"
            )
            parameters.append(
                library_source
            )

        if conditions:
            query += " AND " + " AND ".join(
                conditions
            )

        if order_by == "name":
            query += " ORDER BY name COLLATE NOCASE"
        else:
            query += " ORDER BY playtime_minutes"

        query += (
            " DESC"
            if descending
            else " ASC"
        )

        query += """
            LIMIT ?
            OFFSET ?
        """

        parameters.extend([
            int(limit),
            int(offset)
        ])

        cursor = self.connection.cursor()
        cursor.execute(
            query,
            parameters
        )

        return cursor.fetchall()

    def get_games_needing_achievements(
        self,
        app_ids,
        days=7
    ):

        if not app_ids:
            return []

        placeholders = ",".join(
            "?" for _ in app_ids
        )

        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            SELECT app_id
            FROM games
            WHERE app_id IN ({placeholders})
              AND owned = 1
              AND library_source = 'own'
              AND (
                    achievements_checked_at IS NULL
                    OR datetime(achievements_checked_at)
                       < datetime('now', ?)
              )
            """,
            [
                *app_ids,
                f"-{days} days"
            ]
        )

        return [
            row[0]
            for row in cursor.fetchall()
        ]

    def close(self):
        self.connection.close()

    def clear_all_data(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            DELETE FROM games
        """)

        self.connection.commit()