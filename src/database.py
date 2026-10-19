import json
import sqlite3


def create_tables(db_path="chessmind.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                white TEXT NOT NULL,
                black TEXT NOT NULL,
                result TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moves (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                ply INTEGER NOT NULL,
                move_uci TEXT NOT NULL,
                move_san TEXT NOT NULL,
                fen_before TEXT NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games(id),
                UNIQUE (game_id, ply)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS move_analysis (
                id INTEGER PRIMARY KEY,
                move_id INTEGER NOT NULL UNIQUE,
                best_move TEXT,
                score_before_kind TEXT NOT NULL,
                score_before_value INTEGER NOT NULL,
                score_after_kind TEXT NOT NULL,
                score_after_value INTEGER NOT NULL,
                perspective TEXT NOT NULL,
                centipawn_loss INTEGER,
                classification TEXT NOT NULL,
                principal_variation TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                preset TEXT NOT NULL,
                nodes INTEGER NOT NULL,
                FOREIGN KEY (move_id) REFERENCES moves(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_game(white, black, result, db_path="chessmind.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        # Pass values separately using ? placeholders.
        cursor.execute(
            "INSERT INTO games (white, black, result) VALUES (?, ?, ?)",
            (white, black, result),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def save_moves(game_id, moves, db_path="chessmind.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        move_ids = {}
        for move in moves:
            cursor.execute(
                "INSERT INTO moves (game_id, ply, move_uci, move_san, fen_before) VALUES (?, ?, ?, ?, ?)",
                (game_id, move["ply"], move["move_uci"], move["move_san"], move["fen_before"]),
            )
            move_ids[move["ply"]] = cursor.lastrowid
        conn.commit()
        return move_ids
    finally:
        conn.close()

def save_move_analysis(move_id, analysis, engine_version, preset, nodes, db_path="chessmind.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO move_analysis (
                move_id,
                best_move,
                score_before_kind,
                score_before_value,
                score_after_kind,
                score_after_value,
                perspective,
                centipawn_loss,
                classification,
                principal_variation,
                engine_version,
                preset,
                nodes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                move_id,
                analysis["best_move"],
                analysis["score_before"]["kind"],
                analysis["score_before"]["value"],
                analysis["score_after"]["kind"],
                analysis["score_after"]["value"],
                analysis["score_before"]["perspective"],
                analysis["centipawn_loss"],
                analysis["classification"],
                json.dumps(analysis["principal_variation"]),
                engine_version,
                preset,
                nodes
            )
        )
        conn.commit()
    finally:
        conn.close()


def get_game_analysis(game_id, db_path="chessmind.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.ply, m.move_uci, m.move_san, m.fen_before,
                   ma.best_move, ma.score_before_kind, ma.score_before_value,
                   ma.score_after_kind, ma.score_after_value, ma.perspective,
                   ma.centipawn_loss, ma.classification, ma.principal_variation,
                   ma.engine_version, ma.preset, ma.nodes
            FROM moves m
            LEFT JOIN move_analysis ma ON m.id = ma.move_id
            WHERE m.game_id = ?
            ORDER BY m.ply
            """,
            (game_id,)
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            row = list(row)
            # Column 12 is principal_variation; LEFT JOIN may return NULL.
            if row[12] is not None:
                row[12] = json.loads(row[12])
            results.append(row)
        return results
    finally:
        conn.close()


def list_games(db_path="chessmind.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, white, black, result FROM games ORDER BY id")
        return cursor.fetchall()
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()
    print("Games table created. Saved games:")
    print(list_games())

# Run from the project folder: uv run python -m src.database
# View saved moves: sqlite3 -header -column chessmind.db "SELECT game_id, ply, move_uci, move_san FROM moves ORDER BY game_id, ply;"
