import logging

from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move

from agents.Group23.Alpha_Zero_NN import Alpha_Zero_NN
from agents.Group23.alpha_zero_mcts import MCTS

class AlphaZeroAgent(AgentBase):
    logger = logging.getLogger(__name__)

    _board_size: int = 11
    _trained_policy_value_network = None # store a trained policy and value network
    _agent_in_training = False # flag to indicate if agent is in training mode
    tree = None

    def __init__(self, colour: Colour, custom_trained_network: Alpha_Zero_NN = None, turn_length_s: int = 2.5):
        super().__init__(colour)
        if custom_trained_network is not None:
            self._trained_policy_value_network = custom_trained_network
            self._agent_in_training = True
        else:
            # create a NN using the best model saved
            self._trained_policy_value_network = Alpha_Zero_NN(board_size=self._board_size)
        self.turn_length = turn_length_s # max length of a turn in seconds
        self.tree = None # MCTS tree


    def get_board_vector(self, board: Board) -> list[list[int]]:
        """generate input vector for neural network
        based on current and recent board states

        Args:
            board (Board): current board state

        Returns:
            list[int]: input vector for neural network
        """
        
        # convert board state to input vector
        board_vector = []
        for i in range(self._board_size):
            new_line = []
            for j in range(self._board_size):
                tile = board.tiles[i][j].colour
                if tile == None:
                    new_line.append(0)
                elif tile == self.colour:
                    new_line.append(1)
                else:
                    new_line.append(-1)
            board_vector.append(new_line)

        return board_vector
    
    def _record_experience(self, board_state: Board, mcts_probs: list[list[float]]):
        """Record the experience for the given board state

        Args:
            board_state (list[list[int]]): experienced board states
            mcts_probs (list[list[float]]): mcts probabilities for the given board state
        """
        print(f"Recording experience ({self.colour})")
        board_vector_state = self.get_board_vector(board_state)
        self._trained_policy_value_network._add_experience_to_buffer(board_vector_state, mcts_probs, self.colour)

    def make_move(self, turn: int, board: Board, opp_move: Move | None) -> Move:
        allowed_time = self.allowed_time(turn_number=turn)

        mcts = MCTS(self.colour, max_simulation_length=allowed_time, custom_trained_network=self._trained_policy_value_network, in_training=self._agent_in_training)
        best_move, visit_count_normalised_distribution = mcts.run(board) # normalised distribution is None if not in training mode

        if self._agent_in_training:
            # add data to training buffer before modifying board
            self._record_experience(board, visit_count_normalised_distribution)

        return best_move
    

    def allowed_time(self, turn_number, total_turns=121, total_time=300):
        """
        Calculate the allowed time for a turn in a game, giving more time to earlier turns
        and less to later ones.

        Args:
            turn_number (int): The current turn number (1-indexed).
            total_turns (int): Total number of turns in the game (default: 121).
            total_time (float): Total allowed time in seconds (default: 300 seconds).

        Returns:
            float: Allowed time in seconds for the given turn.
        """
        # Parameter controlling the decay rate (higher values give more time to early turns).
        decay_rate = 0.97

        # Calculate the weight for each turn based on the decay rate.
        weights = [decay_rate ** i for i in range(total_turns)]
        total_weight = sum(weights)

        # Calculate the allowed time for the current turn.
        turn_weight = weights[turn_number - 1]  # Turn number is 1-indexed.
        turn_time = (turn_weight / total_weight) * total_time

        return turn_time