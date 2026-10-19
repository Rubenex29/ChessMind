import argparse
import json
from pathlib import Path

import chess
import chess.pgn

from .stockfish_manager import StockfishManager
from .database import create_tables, save_game, save_moves, save_move_analysis, get_game_analysis


def import_game(pgn_path: str) -> tuple[str, str, str, list[dict]]:
    path = Path(pgn_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open(encoding="utf-8-sig") as file:
        game = chess.pgn.read_game(file)

    if game is None:
        raise ValueError("PGN file is empty")

    if game.errors:
        raise ValueError(f"Invalid PGN: {game.errors}")

    white = game.headers.get("White", "?")
    black = game.headers.get("Black", "?")
    result = game.headers.get("Result", "*")

    board = game.board()
    moves = []

    for ply, move in enumerate(game.mainline_moves(), start=1):
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move: {move}")

        move_data = {
            "ply": ply,
            "player": "white" if board.turn == chess.WHITE else "black",
            "move_uci": move.uci(),
            "move_san": board.san(move),
            "fen_before": board.fen(),
        }

        board.push(move)

        move_data["fen_after"] = board.fen()
        moves.append(move_data)

    return white, black, result, moves


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import and analyze a chess PGN game"
    )

    parser.add_argument(
        "pgn_path",
        help="Path to the PGN file"
    )

    parser.add_argument(
        "--preset",
        choices=["fast", "normal", "deep"],
        default="normal",
        help="Stockfish analysis preset"
    )

    args = parser.parse_args()

    try:
        white, black, result, moves = import_game(args.pgn_path)
        create_tables()  # Ensure the database and tables exist
        game_id = save_game(white, black, result)
        move_ids = save_moves(game_id, moves)
        manager = StockfishManager()

        try:
            results = manager.analyze_game(moves, args.preset)
            for result in results:
                save_move_analysis(
                    move_ids[result["ply"]],
                    result,
                    manager.engine.id["name"],
                    args.preset,
                    manager.PRESETS[args.preset],
                )
            print(f"\nSaved analysis for game {game_id}:")
            for row in get_game_analysis(game_id):
                (
                    ply, move_uci, move_san, fen_before, best_move,
                    before_kind, before_value, after_kind, after_value,
                    perspective, centipawn_loss, classification,
                    principal_variation, engine_version, preset, nodes,
                ) = row
                print(f"\nMove {ply}: {move_san} (UCI: {move_uci})")
                print(f"  Position before (FEN): {fen_before}")
                if classification is None:
                    print("  Analysis: not available")
                    continue
                print(f"  Best move (UCI): {best_move or 'not available'}")
                print(f"  Score perspective: {perspective}")
                print(f"  Score before: {before_value} ({before_kind})")
                print(f"  Score after: {after_value} ({after_kind})")
                loss = centipawn_loss if centipawn_loss is not None else "not applicable (mate)"
                print(f"  Centipawn loss: {loss}")
                print(f"  Classification: {classification}")
                variation = " ".join(principal_variation) if principal_variation else "none"
                print(f"  Principal variation (UCI): {variation}")
                print(f"  Engine: {engine_version}")
                print(f"  Preset: {preset} | Node limit: {nodes}")
            print("\nScore units: cp = centipawns (100 = one pawn); mate = moves to mate.")
            output = {
                "pgn_path": args.pgn_path,
                "stockfish_version": manager.engine.id,
                "nodes": manager.PRESETS[args.preset],
                "preset": args.preset,
                "results": results
            }
        finally:
            manager.close()
        with open("analysis.json", "w", encoding="utf-8") as file:
            json.dump(output, file, indent=4)

        print("\nAnalysis saved to analysis.json")

    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
