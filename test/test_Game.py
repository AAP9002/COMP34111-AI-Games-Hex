import unittest
from unittest.mock import Mock, patch

from src.Board import Board
from src.Colour import Colour
from src.EndState import EndState
from src.Game import Game
from src.Move import Move
from src.Player import Player

# NOTE: LLM generated tests not checked by human

class TestGame(unittest.TestCase):
    def setUp(self):
        self.player1 = Player("Player1", Mock())
        self.player2 = Player("Player2", Mock())
        self.game = Game(self.player1, self.player2)
        self.board = self.game.board

    def test_init(self):
        self.assertEqual(self.game._turn, 0)
        self.assertIsInstance(self.game._board, Board)
        self.assertEqual(self.game.current_player, Colour.RED)
        self.assertFalse(self.game.has_swapped)
        self.assertEqual(self.game.players[Colour.RED], self.player1)
        self.assertEqual(self.game.players[Colour.BLUE], self.player2)

    @patch("src.Game.time")
    def test_play_timeout(self, mock_time):
        mock_time.side_effect = [1e9, 10e9, 20e9, 400e9, 500e9]
        self.game._start_time = 0
        self.player1.agent.make_move.return_value = Move(1, 1)
        self.player2.agent.make_move.return_value = Move(2, 2)
        result = self.game._play()

        self.assertEqual(result["winner"], "Player1")
        self.assertEqual(result["win_method"], "TIMEOUT")
        self.assertEqual(result["player1_move_time"], 9)
        self.assertEqual(result["player2_move_time"], 380)
        self.assertEqual(result["total_game_time"], 500)

    def test_make_move(self):
        move = Move(0, 0)
        self.game._make_move(move)
        self.assertEqual(self.game._board.tiles[0][0].colour, Colour.RED)

    def test_make_swap_move(self):
        move = Move(-1, -1)
        self.game._make_move(move)
        self.assertTrue(self.game.has_swapped)
        self.assertEqual(self.game.current_player, Colour.BLUE)

    def test_end_game_win(self):
        result = self.game._end_game(EndState.WIN)
        self.assertEqual(result["winner"], "Player1")
        self.assertEqual(result["win_method"], "WIN")

    def test_end_game_bad_move(self):
        self.game.current_player = Colour.BLUE
        result = self.game._end_game(EndState.BAD_MOVE)
        self.assertEqual(result["winner"], "Player1")
        self.assertEqual(result["win_method"], "BAD_MOVE")

    def test_end_game_timeout(self):
        self.game.current_player = Colour.BLUE
        result = self.game._end_game(EndState.TIMEOUT)
        self.assertEqual(result["winner"], "Player1")
        self.assertEqual(result["win_method"], "TIMEOUT")

    def test_ns_to_s(self):
        self.assertEqual(Game.ns_to_s(1e9), 1.0)
        self.assertEqual(Game.ns_to_s(1.5e9), 1.5)

    def test_is_valid_move(self):
        self.game = Game(self.player1, self.player2)
        self.board = self.game.board
        # Test valid move
        self.assertTrue(self.game.is_valid_move(Move(0, 0), 0, self.board))

        # Test invalid move (out of bounds)
        self.assertFalse(self.game.is_valid_move(Move(-1, 0), 0, self.board))
        self.assertFalse(self.game.is_valid_move(Move(0, -1), 0, self.board))
        self.assertFalse(self.game.is_valid_move(Move(self.game._board.size, 0), 0, self.board))
        self.assertFalse(self.game.is_valid_move(Move(0, self.game._board.size), 0, self.board))

        # Test invalid move (occupied tile)
        self.game._make_move(Move(1, 1))
        self.assertFalse(self.game.is_valid_move(Move(1, 1), 0, self.board))

        # Test invalid swap move
        self.assertFalse(self.game.is_valid_move(Move(-1, -1), 0, self.board))


if __name__ == "__main__":
    unittest.main()
