from board import Board
from pieces import Piece 
from utils import algebraic_to_coords, coords_to_algebraic
import copy 

class Game:
    """
    Manages the chess game logic, including abilities.
    """
    def __init__(self):
        self.board = Board() # Board setup and ability assignment happens in Board's __init__
        self.current_player = "white"
        self.game_over = False
        self.winner = None
        # For abilities.py to use utils like coords_to_algebraic if needed in effects
        self.utils = {'algebraic_to_coords': algebraic_to_coords, 'coords_to_algebraic': coords_to_algebraic}


    def switch_player(self):
        self.current_player = "black" if self.current_player == "white" else "white"

    def _find_king_position(self, player_color, board_state):
        for r_idx, row in enumerate(board_state.grid):
            for c_idx, piece in enumerate(row):
                if piece and piece.piece_type == "king" and piece.color == player_color:
                    return (r_idx, c_idx)
        return None

    def is_in_check(self, player_color, board_state):
        king_pos = self._find_king_position(player_color, board_state)
        if not king_pos:
            return True # Should be treated as an error or loss

        opponent_color = "black" if player_color == "white" else "white"
        for r_idx, row in enumerate(board_state.grid):
            for c_idx, piece in enumerate(row):
                if piece and piece.color == opponent_color:
                    if piece.is_valid_move(board_state, (r_idx, c_idx), king_pos):
                        return True
        return False

    def _decrement_cooldowns(self, player_color):
        """Decrements ability cooldowns for all pieces of the given player."""
        for row in self.board.grid:
            for piece in row:
                if piece and piece.color == player_color and piece.ability_cooldown > 0:
                    piece.ability_cooldown -= 1
                    # print(f"Decremented cooldown for {piece} to {piece.ability_cooldown}") # Debug

    def play_turn(self, start_pos_str, end_pos_str):
        start_coords = algebraic_to_coords(start_pos_str)
        end_coords = algebraic_to_coords(end_pos_str)

        if start_coords is None or end_coords is None:
            print(f"Invalid input format: '{start_pos_str}' or '{end_pos_str}'. Use algebraic notation (e.g., 'e2').")
            return False
        
        if start_coords == end_coords:
            print("Invalid move: Start and end positions are the same.")
            return False

        piece_to_move = self.board.get_piece(start_coords)

        if piece_to_move is None:
            print(f"No piece at {start_pos_str}.")
            return False

        if piece_to_move.color != self.current_player:
            print(f"Cannot move opponent's piece. It's {self.current_player}'s turn.")
            return False

        if not piece_to_move.is_valid_move(self.board, start_coords, end_coords):
            print(f"Invalid move for {piece_to_move} from {start_pos_str} to {end_pos_str} by piece rules.")
            return False
        
        hypothetical_board = copy.deepcopy(self.board)
        if hypothetical_board.move_piece(start_coords, end_coords) is not None: # move_piece returns captured piece
             # Check for self-check only if move_piece was successful (which it should be given prior checks)
            if self.is_in_check(self.current_player, hypothetical_board):
                print(f"Invalid move: {start_pos_str} to {end_pos_str} would put your King in check.")
                return False
        else: # This case implies move_piece failed for some reason, e.g. internal error
            # If piece_to_move.is_valid_move passed, this path should ideally not be taken unless
            # move_piece has additional constraints not covered.
            # One such case: if is_valid_move doesn't check if target is own piece (but it should).
            # For now, let's assume is_valid_move is comprehensive.
            # If hypothetical_board.move_piece returns None when no capture, but still valid.
            # The check for self-check should happen regardless of capture.

            # Re-evaluating the hypothetical move logic:
            # We need to make the move, then check for self-check.
            # The return value of move_piece (captured_piece) is for the actual move.
            # For hypothetical, we just care if the state changes.
            # Let's assume move_piece on hypothetical board always "succeeds" if is_valid_move was true.
            # The previous `if ... is not None` was potentially flawed for non-capture moves.
            # Corrected logic:
            pass # The move on hypothetical_board is made. Now check for check.
        
        # Ensure the hypothetical move is made before checking for check
        # (The previous logic was a bit convoluted here)
        # Create a fresh hypothetical board for this check
        hypo_board_for_check = copy.deepcopy(self.board)
        hypo_board_for_check.move_piece(start_coords, end_coords) # Make the move
        if self.is_in_check(self.current_player, hypo_board_for_check):
            print(f"Invalid move: {start_pos_str} to {end_pos_str} would put your King in check.")
            return False


        # Actual move
        captured_piece = self.board.move_piece(start_coords, end_coords)
        if captured_piece:
            print(f"{piece_to_move} from {start_pos_str} captures {captured_piece} at {end_pos_str}.")
            if piece_to_move.ability and piece_to_move.ability_recharges_on_capture:
                if piece_to_move.ability_cooldown > 0:
                    print(f"{piece_to_move}'s ability {piece_to_move.ability.name} recharged due to capture!")
                    piece_to_move.ability_cooldown = 0
        else:
            print(f"{piece_to_move} moved from {start_pos_str} to {end_pos_str}.")
        
        player_who_moved = self.current_player
        self.switch_player()
        self._decrement_cooldowns(player_who_moved) # Decrement cooldowns for player who just moved

        if self.is_in_check(self.current_player, self.board):
            print(f"{self.current_player} is in check!")
        return True

    def handle_ability_activation(self, piece_pos_str, target_pos_str=None):
        """
        Handles the activation of a piece's ability.
        piece_pos_str: Algebraic notation of the piece using the ability.
        target_pos_str: Optional algebraic notation for the target, if required by the ability.
        """
        piece_coords = algebraic_to_coords(piece_pos_str)
        if not piece_coords:
            print(f"Invalid piece position: {piece_pos_str}")
            return False

        piece = self.board.get_piece(piece_coords)

        if not piece:
            print(f"No piece at {piece_pos_str}.")
            return False
        
        if piece.color != self.current_player:
            print(f"Cannot use opponent's piece ability. It's {self.current_player}'s turn.")
            return False

        if not piece.ability:
            print(f"{piece} at {piece_pos_str} has no ability.")
            return False

        if piece.ability_cooldown > 0:
            print(f"{piece.ability.name} for {piece} is on cooldown for {piece.ability_cooldown} more turn(s).")
            return False

        target_coords = None
        if piece.ability.target_type != 'self': # Abilities that target something else
            if not target_pos_str:
                # Some abilities might not need a target string if they have fixed targets (e.g. "Heal Self")
                # Or if target is implicit (e.g. "Stun all adjacent enemies")
                # For now, let's assume target_types like 'empty_square' or 'ally_piece' need a target_pos_str
                if 'square' in piece.ability.target_type or 'piece' in piece.ability.target_type:
                     print(f"{piece.ability.name} requires a target position.")
                     return False
            else:
                target_coords = algebraic_to_coords(target_pos_str)
                if not target_coords:
                    print(f"Invalid target position: {target_pos_str}")
                    return False
        
        # Simulate ability use for check validation
        hypothetical_board_ability = copy.deepcopy(self.board)
        # The piece on the hypothetical board needs to be the one using the ability
        hypothetical_piece = hypothetical_board_ability.get_piece(piece_coords)
        
        # We need a way for effect_logic to work on this hypothetical board/game state
        # This is tricky. For now, let's assume effect_logic can take a board.
        # Let's modify effect_logic to take 'game' and then it can use game.board or a passed board.
        # For this check, we'll pass a temporary game-like object or just the board.
        # The current effect_logic takes (game, piece, target_coords).
        # For the check, we need to ensure the 'piece' object is from the hypothetical board.
        
        # Create a lightweight game context for the hypothetical check
        hypothetical_game_context = copy.copy(self) # Shallow copy is enough as we replace board
        hypothetical_game_context.board = hypothetical_board_ability

        # Call effect logic on the hypothetical context
        # Note: piece.ability.effect_logic might modify hypothetical_piece and hypothetical_board_ability
        if piece.ability.effect_logic(hypothetical_game_context, hypothetical_piece, target_coords):
            # If effect was hypothetically successful, check if it caused self-check
            if self.is_in_check(self.current_player, hypothetical_board_ability):
                print(f"Using {piece.ability.name} by {piece} (targeting {target_pos_str or 'self'}) would put your King in check.")
                # No actual change was made to the real board yet.
                return False
            # Hypothetical check passed, proceed with actual ability use
        else:
            # The ability effect itself deemed the move invalid (e.g., teleport out of range)
            # The effect_logic should have printed the reason.
            return False


        # Execute ability on the actual board
        if piece.ability.effect_logic(self, piece, target_coords): # Pass the real game object
            print(f"{piece.color} {piece.piece_type} at {piece_pos_str} used {piece.ability.name} "
                  f"{('targeting ' + target_pos_str) if target_pos_str else ''}.")
            piece.ability_cooldown = piece.ability.cooldown_max
            
            player_who_used_ability = self.current_player
            self.switch_player()
            self._decrement_cooldowns(player_who_used_ability)

            if self.is_in_check(self.current_player, self.board):
                print(f"{self.current_player} is in check!")
            return True
        else:
            # This typically means the conditions for the ability weren't met (e.g., target invalid).
            # The effect_logic function should have printed a message.
            # print(f"Failed to use {piece.ability.name} for {piece} at {piece_pos_str}.") # Generic message
            return False


if __name__ == "__main__":
    game = Game()
    
    while not game.game_over:
        game.board.display()
        print(f"Current player: {game.current_player}")
        
        if game.is_in_check(game.current_player, game.board):
            print(f"{game.current_player} is IN CHECK!")

        action_input = input(
            "Enter action ('move <start> <end>' or 'ability <piece_pos> [target_pos]' or 'quit'): "
        ).lower().split()
        
        if not action_input:
            print("No input received. Try again.")
            continue

        command = action_input[0]

        if command == 'quit':
            print("Game exited by user.")
            break
        
        if command == 'move':
            if len(action_input) == 3:
                start_pos_str, end_pos_str = action_input[1], action_input[2]
                if not game.play_turn(start_pos_str, end_pos_str):
                    print("Move failed. Try again.")
            else:
                print("Invalid move format. Use: move <start_pos> <end_pos> (e.g., move e2 e4)")
        
        elif command == 'ability':
            if len(action_input) >= 2:
                piece_pos_str = action_input[1]
                target_pos_str = action_input[2] if len(action_input) == 3 else None
                if not game.handle_ability_activation(piece_pos_str, target_pos_str):
                    print("Ability activation failed. Try again.")
            else:
                print("Invalid ability format. Use: ability <piece_pos> [target_pos] (e.g., ability e2 e4)")
        
        else:
            print(f"Unknown command: {command}. Valid commands: 'move', 'ability', 'quit'.")

    if game.winner:
        print(f"Game over! {game.winner} wins!")
    print("\nGame finished.")
