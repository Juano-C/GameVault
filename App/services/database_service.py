import json
import sqlite3

from datetime import datetime, timedelta
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

    # ==================================================
    # TABLES
    # ==================================================

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

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS family_playtime_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL,
                playtime_minutes INTEGER NOT NULL DEFAULT 0,
                captured_at TEXT NOT NULL
            )
        """)

        self.connection.commit()

    # ==================================================
    # MIGRATIONS
    # ==================================================

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

    # ==================================================
    # INDEXES
    # ==================================================

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

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_family_playtime_history
            ON family_playtime_history(app_id, captured_at)
        """)

        self.connection.commit()

    # ==================================================
    # EXISTING APP IDS
    # ==================================================

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

    # ==================================================
    # FAMILY PLAYTIME - LAST 14 DAYS
    # ==================================================

    def update_family_playtime_history(
        self,
        family_games
    ):

        if not family_games:
            return {}

        now = datetime.now()

        now_text = now.isoformat(
            timespec="seconds"
        )

        cutoff = (
            now - timedelta(days=14)
        )

        cutoff_text = cutoff.isoformat(
            timespec="seconds"
        )

        cursor = self.connection.cursor()

        result = {}

        for game in family_games:

            app_id = int(
                game["app_id"]
            )

            current_minutes = int(
                game.get(
                    "playtime_minutes",
                    0
                )
            )

            # ------------------------------------------
            # BUSCAR EL ÚLTIMO VALOR GUARDADO
            # ------------------------------------------

            cursor.execute("""
                SELECT
                    playtime_minutes,
                    last_synced
                FROM games
                WHERE app_id = ?
                  AND library_source = 'family'
                LIMIT 1
            """, (
                app_id,
            ))

            previous_game = (
                cursor.fetchone()
            )

            baseline = None

            # ------------------------------------------
            # SI EL JUEGO YA EXISTÍA Y FUE SINCRONIZADO
            # HACE MENOS DE 14 DÍAS, USAMOS ESE VALOR
            # ------------------------------------------

            if previous_game:

                previous_minutes = int(
                    previous_game[0] or 0
                )

                previous_synced = (
                    previous_game[1]
                )

                if previous_synced:

                    try:

                        previous_datetime = (
                            datetime.fromisoformat(
                                previous_synced
                            )
                        )

                        if previous_datetime >= cutoff:

                            baseline = previous_minutes

                    except (
                        ValueError,
                        TypeError
                    ):

                        pass

            # ------------------------------------------
            # SI NO HAY BASELINE RECIENTE,
            # BUSCAMOS UN SNAPSHOT DE HACE <= 14 DÍAS
            # ------------------------------------------

            if baseline is None:

                cursor.execute("""
                    SELECT playtime_minutes
                    FROM family_playtime_history
                    WHERE app_id = ?
                      AND captured_at <= ?
                    ORDER BY captured_at DESC
                    LIMIT 1
                """, (
                    app_id,
                    cutoff_text
                ))

                old_snapshot = (
                    cursor.fetchone()
                )

                if old_snapshot:

                    baseline = int(
                        old_snapshot[0] or 0
                    )

            # ------------------------------------------
            # CALCULAR LAS ÚLTIMAS 2 SEMANAS
            # ------------------------------------------

            if baseline is None:

                playtime_2weeks = 0

            else:

                playtime_2weeks = max(
                    0,
                    current_minutes - baseline
                )

            result[app_id] = (
                playtime_2weeks
            )

            # ------------------------------------------
            # GUARDAR SNAPSHOT ACTUAL
            # ------------------------------------------

            cursor.execute("""
                INSERT INTO family_playtime_history (
                    app_id,
                    playtime_minutes,
                    captured_at
                )
                VALUES (?, ?, ?)
            """, (
                app_id,
                current_minutes,
                now_text
            ))

        self.connection.commit()

        return result

    # ==================================================
    # SAVE OWN GAMES
    # ==================================================

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
                    app_id,
                    name,
                    playtime_minutes,
                    last_played,
                    playtime_2weeks,
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
                    playtime_minutes =
                        excluded.playtime_minutes,
                    last_played =
                        excluded.last_played,
                    playtime_2weeks =
                        excluded.playtime_2weeks,
                    owned = 1,
                    library_source = 'own',
                    owner_steamids =
                        excluded.owner_steamids,
                    exclude_reason =
                        excluded.exclude_reason,
                    last_synced =
                        excluded.last_synced
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
                json.dumps(
                    game.owner_steamids
                ),
                game.exclude_reason
            ))

        self.connection.commit()

    # ==================================================
    # SAVE FAMILY GAMES
    # ==================================================

    def save_family_games(self, games):

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor = self.connection.cursor()

        for game in games:

            cursor.execute("""
                INSERT INTO games (
                    app_id,
                    name,
                    playtime_minutes,
                    last_played,
                    playtime_2weeks,
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
                    last_synced =
                        excluded.last_synced
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
                json.dumps(
                    game.owner_steamids
                ),
                game.exclude_reason
            ))

        self.connection.commit()

    # ==================================================
    # MARK NOT OWNED
    # ==================================================

    def mark_games_not_owned(
        self,
        current_app_ids
    ):

        cursor = self.connection.cursor()

        if not current_app_ids:

            cursor.execute("""
                UPDATE games
                SET owned = 0
            """)

        else:

            placeholders = ",".join(
                "?"
                for _ in current_app_ids
            )

            cursor.execute(
                f"""
                UPDATE games
                SET owned = 0
                WHERE app_id NOT IN (
                    {placeholders}
                )
                """,
                list(current_app_ids)
            )

        self.connection.commit()

    # ==================================================
    # ACHIEVEMENTS
    # ==================================================

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

    # ==================================================
    # REVIEWS
    # ==================================================

    def replace_reviews(
        self,
        reviews
    ):

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor = self.connection.cursor()

        try:

            cursor.execute(
                "BEGIN"
            )

            cursor.execute("""
                UPDATE games
                SET
                    has_review = 0,
                    review_positive = NULL,
                    review_text = NULL,
                    review_checked_at = ?
                WHERE owned = 1
            """, (
                now,
            ))

            for review in reviews:

                app_id = review.get(
                    "app_id"
                )

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
                    review.get(
                        "text",
                        ""
                    ),
                    now,
                    int(app_id)
                ))

            self.connection.commit()

        except Exception:

            self.connection.rollback()
            raise

    # ==================================================
    # REVIEWED APP IDS
    # ==================================================

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

    # ==================================================
    # GAME COUNT
    # ==================================================

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

            query += (
                " AND "
                + " AND ".join(
                    conditions
                )
            )

        cursor = self.connection.cursor()

        cursor.execute(
            query,
            parameters
        )

        return cursor.fetchone()[0]

    # ==================================================
    # GET GAMES
    # ==================================================

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

            query += (
                " AND "
                + " AND ".join(
                    conditions
                )
            )

        if order_by == "name":

            query += (
                " ORDER BY "
                "name COLLATE NOCASE"
            )

        else:

            query += (
                " ORDER BY "
                "playtime_minutes"
            )

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

    # ==================================================
    # ACHIEVEMENTS TO CHECK
    # ==================================================

    def get_games_needing_achievements(
        self,
        app_ids,
        days=7
    ):

        if not app_ids:
            return []

        placeholders = ",".join(
            "?"
            for _ in app_ids
        )

        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            SELECT app_id
            FROM games
            WHERE app_id IN (
                {placeholders}
            )
              AND owned = 1
              AND library_source IN (
                  'own',
                  'family'
              )
              AND (
                    achievements_checked_at IS NULL
                    OR datetime(
                        achievements_checked_at
                    )
                    < datetime(
                        'now',
                        ?
                    )
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

    # ==================================================
    # CLOSE
    # ==================================================

    def close(self):

        self.connection.close()

    # ==================================================
    # CLEAR DATA
    # ==================================================

    def clear_all_data(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            DELETE FROM games
        """)

        cursor.execute("""
            DELETE FROM family_playtime_history
        """)

        self.connection.commit()