import chess.engine

from .domain import EngineScore, MoveAnalysis


class StockfishManager:
    def __init__(self):
        self.engine = chess.engine.SimpleEngine.popen_uci(
            "/opt/homebrew/bin/stockfish"
        )
        self.PRESETS = {
            "fast": 10_000,
            "normal": 100_000,
            "deep": 1_000_000,
        }

    def analyze(self, board, preset: str = "normal"):
        if preset not in self.PRESETS:
            raise ValueError(f"Invalid preset: {preset}")
        max_nodes = self.PRESETS.get(preset, self.PRESETS["normal"])
        return self.engine.analyse(
            board,
            chess.engine.Limit(nodes=max_nodes)
        )

    def close(self):
        self.engine.quit()

    def normalize_score(self, info, color=chess.WHITE):
        score = info["score"].pov(color)

        perspective = "white" if color == chess.WHITE else "black"

        if score.is_mate():
            return EngineScore(
                kind="mate",
                value=score.mate(),
                perspective=perspective
            )

        return EngineScore(
            kind="cp",
            value=score.score(),
            perspective=perspective
        )

    def get_best_line(self, info):
        pv = info.get("pv", [])

        return {
            "best_move": pv[0].uci() if pv else None,
            "pv": [move.uci() for move in pv]
        }

    def calculate_cpl(self, info_before, info_after, color):
        before = info_before["score"].pov(color)
        after = info_after["score"].pov(color)

        if before.is_mate() or after.is_mate():
            return None

        return max(0, before.score() - after.score())

    def classify_move(self, cpl):
        if cpl is None:
            return "unclassified"
        if cpl <= 20:
            return "good"
        if cpl <= 50:
            return "inaccuracy"
        if cpl <= 100:
            return "mistake"
        return "blunder"

    def analyse_move(self, board, move_uci, preset="normal"):
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move: {move_uci}")

        color = board.turn

        # Analisar antes da jogada
        info_before = self.analyze(board, preset)
        best_line = self.get_best_line(info_before)

        # Executar a jogada do jogador
        board.push(move)
        # Analisar depois da jogada
        info_after = self.analyze(board, preset)

        # Calcular CPL e classificação
        cpl = self.calculate_cpl(
            info_before,
            info_after,
            color
        )
        if board.is_checkmate():
            label = "checkmate"
        elif cpl is None:
            label = self.classify_mate(
                info_before,
                info_after,
                color
            )
        else:
            label = self.classify_move(cpl)

        return {
            "played_move": move_uci,
            "best_move": best_line["best_move"],
            "pv": best_line["pv"],
            "score_before": self.normalize_score(info_before, color).model_dump(),
            "score_after": self.normalize_score(info_after, color).model_dump(),
            "cpl": cpl,
            "label": label
        }

    def analyze_game(self, moves, preset="normal"):
        results = []
        total = len(moves)

        for index, move_data in enumerate(moves, start=1):
            board = chess.Board(move_data["fen_before"])
            color = board.turn

            # Analisar antes da jogada
            info_before = self.analyze(board, preset)
            best_line = self.get_best_line(info_before)

            # Executar a jogada do jogador
            move = chess.Move.from_uci(move_data["move_uci"])
            board.push(move)
            # Analisar depois da jogada
            info_after = self.analyze(board, preset)

            # Calcular CPL e classificação
            cpl = self.calculate_cpl(
                info_before,
                info_after,
                color
            )
            if board.is_checkmate():
                label = "checkmate"
            elif cpl is None:
                label = self.classify_mate(
                    info_before,
                    info_after,
                    color
                )
            else:
                label = self.classify_move(cpl)

            results.append(MoveAnalysis(
                ply=move_data["ply"],
                fen_before=move_data["fen_before"],
                played_move=move_data["move_uci"],
                best_move=best_line["best_move"],
                score_before=self.normalize_score(info_before, color),
                score_after=self.normalize_score(info_after, color),
                centipawn_loss=cpl,
                classification=label,
                principal_variation=best_line["pv"],
                evidence=[]
            ).model_dump())

            print(f"[{index}/{total}] {move_data['move_san']} - {label}")

        return results

    def classify_mate(self, info_before, info_after, color):
        before = info_before["score"].pov(color)
        after = info_after["score"].pov(color)

        before_mate = before.mate()
        after_mate = after.mate()

        if before_mate is None and after_mate is None:
            return None

        # Evitar classificar Mate(0) sem contexto do tabuleiro
        if before_mate == 0 or after_mate == 0:
            return "unclassified"

        # Tinha mate a favor
        if before_mate is not None and before_mate > 0:
            if after_mate is None or after_mate < 0:
                return "missed_win"
            return "good"

        # Tinha mate contra
        if before_mate is not None and before_mate < 0:
            if after_mate is None or after_mate > 0:
                return "escaped_mate"
            return "unclassified"

        # Antes não existia mate forçado identificado
        if after_mate is not None:
            if after_mate > 0:
                return "found_mate"
            return "blunder"

        return "unclassified"
