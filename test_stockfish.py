from unittest.mock import Mock

import chess
import chess.engine
import pytest

from src.chessmind import import_game
from src.stockfish_manager import StockfishManager


@pytest.fixture
def manager(monkeypatch):
    # O construtor recebe um motor simulado: nenhum processo é iniciado.
    engine = Mock()
    monkeypatch.setattr(chess.engine.SimpleEngine, "popen_uci", lambda *args: engine)
    return StockfishManager()


def evaluation(score, color=chess.WHITE):
    return {"score": chess.engine.PovScore(score, color)}


@pytest.mark.parametrize("color", [chess.WHITE, chess.BLACK])
@pytest.mark.parametrize("before,after,expected", [
    (100, 40, 60), (40, 100, 0), (100, 100, 0), (-20, -90, 70),
])
def test_calculate_cpl(manager, color, before, after, expected):
    assert manager.calculate_cpl(
        evaluation(chess.engine.Cp(before), color),
        evaluation(chess.engine.Cp(after), color), color,
    ) == expected


def test_cpl_converts_opponent_perspective(manager):
    assert manager.calculate_cpl(
        evaluation(chess.engine.Cp(100), chess.WHITE),
        evaluation(chess.engine.Cp(-40), chess.BLACK), chess.WHITE,
    ) == 60


@pytest.mark.parametrize("before,after", [
    (chess.engine.Mate(3), chess.engine.Cp(100)),
    (chess.engine.Cp(100), chess.engine.Mate(-2)),
    (chess.engine.Mate(3), chess.engine.Mate(2)),
])
def test_cpl_with_mate(manager, before, after):
    assert manager.calculate_cpl(evaluation(before), evaluation(after), chess.WHITE) is None


@pytest.mark.parametrize("color", [chess.WHITE, chess.BLACK])
@pytest.mark.parametrize("before,after,expected", [
    (chess.engine.Cp(100), chess.engine.Cp(40), None),
    (chess.engine.Mate(3), chess.engine.Cp(100), "missed_win"),
    (chess.engine.Mate(3), chess.engine.Mate(-2), "missed_win"),
    (chess.engine.Cp(100), chess.engine.Mate(-2), "blunder"),
    (chess.engine.Mate(3), chess.engine.Mate(2), "good"),
    (chess.engine.Mate(-3), chess.engine.Mate(-2), "unclassified"),
    (chess.engine.Mate(-3), chess.engine.Cp(-100), "escaped_mate"),
    (chess.engine.Mate(-3), chess.engine.Mate(2), "escaped_mate"),
    (chess.engine.Cp(100), chess.engine.Mate(2), "found_mate"),
    (chess.engine.Cp(100), chess.engine.Mate(0), "unclassified"),
    (chess.engine.Mate(1), chess.engine.MateGiven, "unclassified"),
])
def test_classify_mate(manager, color, before, after, expected):
    assert manager.classify_mate(
        evaluation(before, color), evaluation(after, color), color,
    ) == expected


@pytest.mark.parametrize("cpl,label", [
    (0, "good"), (20, "good"), (21, "inaccuracy"), (50, "inaccuracy"),
    (51, "mistake"), (100, "mistake"), (101, "blunder"), (None, "unclassified"),
])
def test_classify_move(manager, cpl, label):
    assert manager.classify_move(cpl) == label


@pytest.mark.parametrize("preset,nodes", [("fast", 10_000), ("normal", 100_000), ("deep", 1_000_000)])
def test_fixed_node_presets(manager, preset, nodes):
    board = chess.Board()
    manager.analyze(board, preset)
    args = manager.engine.analyse.call_args.args
    assert args[0] is board
    assert args[1].nodes == nodes


def test_invalid_preset(manager):
    with pytest.raises(ValueError, match="Invalid preset"):
        manager.analyze(chess.Board(), "invalid")
    manager.engine.analyse.assert_not_called()


def test_analyse_one_move(manager):
    board = chess.Board()
    expected_board = board.copy()
    expected_board.push_uci("e2e4")
    manager.engine.analyse.side_effect = [
        {**evaluation(chess.engine.Cp(100)), "pv": [chess.Move.from_uci("e2e4"), chess.Move.from_uci("e7e5")]},
        evaluation(chess.engine.Cp(-40), chess.BLACK),
    ]
    result = manager.analyse_move(board, "e2e4", "fast")
    # A API atual executa a jogada no tabuleiro recebido.
    assert board.fen() == expected_board.fen()
    assert result["played_move"] == "e2e4"
    assert result["best_move"] == "e2e4"
    assert result["pv"] == ["e2e4", "e7e5"]
    assert result["score_after"] == {"kind": "cp", "value": 40, "perspective": "white"}
    assert result["cpl"] == 60
    assert result["label"] == "mistake"
    assert manager.engine.analyse.call_count == 2
    assert all(call.args[1].nodes == 10_000 for call in manager.engine.analyse.call_args_list)


def test_illegal_move(manager):
    board = chess.Board()
    original_fen = board.fen()
    with pytest.raises(ValueError, match="Illegal move"):
        manager.analyse_move(board, "e2e5")
    assert board.fen() == original_fen
    manager.engine.analyse.assert_not_called()


def test_full_game_with_progress(manager, capsys):
    white, black, result, moves = import_game("games/test_game.pgn")
    manager.engine.analyse.return_value = evaluation(chess.engine.Cp(0))
    results = manager.analyze_game(moves, "fast")
    assert len(results) == len(moves) == 4
    assert [result["ply"] for result in results] == [1, 2, 3, 4]
    assert results[-1]["classification"] == "checkmate"
    assert "[4/4] Qh4# - checkmate" in capsys.readouterr().out
    assert manager.engine.analyse.call_count == 8


def test_normalize_mate_and_empty_pv(manager):
    assert manager.normalize_score(evaluation(chess.engine.Mate(-2)), chess.BLACK).model_dump() == {
        "kind": "mate", "value": 2, "perspective": "black",
    }
    assert manager.get_best_line({}) == {"best_move": None, "pv": []}
