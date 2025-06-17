from board import Board, LAVA_EFFECT 
from pieces import Piece 
from utils import algebraic_to_coords, coords_to_algebraic
import copy 

class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = "white"
        self.game_over = False
        self.winner = None
        self.utils = {'algebraic_to_coords': algebraic_to_coords, 'coords_to_algebraic': coords_to_algebraic}
        self.full_turn_counter = 0
        self._start_turn_prep() # Initial visibility update

    def _start_turn_prep(self):
        """Prepares for the start of the current player's turn."""
        self.board.update_visibility(self.current_player)
        # Any other start-of-turn logic can go here.

    def switch_player(self):
        prev_player = self.current_player
        self.current_player = "black" if self.current_player == "white" else "white"
        
        if self.current_player == "white": # Full turn cycle complete
            self.full_turn_counter += 1
            self.board.board_evolution_timer +=1
            if self.board.board_evolution_timer >= self.board.turns_before_evolution:
                self.board.generate_tile_effects(self)
        
        self._start_turn_prep() # Update visibility for the new player

    def _find_king_position(self, player_color, board_state): # Operates on given board_state
        for r_idx, row in enumerate(board_state.grid):
            for c_idx, piece in enumerate(row):
                if piece and piece.piece_type == "king" and piece.color == player_color:
                    return (r_idx, c_idx)
        return None

    def is_in_check(self, player_color, board_state): # Operates on given board_state (true state)
        king_pos = self._find_king_position(player_color, board_state)
        if not king_pos: return True 

        opponent_color = "black" if player_color == "white" else "white"
        for r_idx, row in enumerate(board_state.grid):
            for c_idx, piece in enumerate(row):
                if piece and piece.color == opponent_color:
                    if piece.is_valid_move(board_state, (r_idx, c_idx), king_pos):
                        return True
        return False

    def _decrement_cooldowns(self, player_color):
        for row in self.board.grid: # Operates on the actual board
            for piece in row:
                if piece and piece.color == player_color and piece.ability_cooldown > 0:
                    piece.ability_cooldown -= 1

    def play_turn(self, start_pos_str, end_pos_str):
        start_coords = algebraic_to_coords(start_pos_str)
        end_coords = algebraic_to_coords(end_pos_str)

        if start_coords is None or end_coords is None: print(f"Invalid input format."); return False
        if start_coords == end_coords: print("Start and end positions are the same."); return False

        # Check LAVA at destination (using the true board state)
        if self.board.tile_effects[end_coords[0]][end_coords[1]] == LAVA_EFFECT: # Direct access to LAVA_EFFECT from board
            print(f"Cannot move to LAVA tile at {end_pos_str}."); return False

        piece_to_move = self.board.get_piece(start_coords) # From true board state

        if piece_to_move is None: print(f"No piece at {start_pos_str}."); return False
        if piece_to_move.color != self.current_player: print(f"Cannot move opponent's piece."); return False

        if not piece_to_move.is_valid_move(self.board, start_coords, end_coords): # Uses true board state
            print(f"Invalid move for {piece_to_move} by piece rules."); return False
        
        hypo_board_for_check = copy.deepcopy(self.board) # True board state for hypothetical
        hypo_piece_for_check = hypo_board_for_check.get_piece(start_coords)
        if hypo_piece_for_check : hypo_piece_for_check.has_speed_buff = piece_to_move.has_speed_buff
        hypo_board_for_check.move_piece(start_coords, end_coords, self)
        if self.is_in_check(self.current_player, hypo_board_for_check): # Uses true hypothetical state
            print(f"Move would put King in check."); return False

        captured_piece = self.board.move_piece(start_coords, end_coords, self) # Modifies true board
        
        if captured_piece:
            print(f"{piece_to_move} captures {captured_piece} at {end_pos_str}.")
            if piece_to_move.ability and piece_to_move.ability_recharges_on_capture:
                if piece_to_move.ability_cooldown > 0:
                    print(f"{piece_to_move}'s ability {piece_to_move.ability.name} recharged!"); piece_to_move.ability_cooldown = 0
        else:
            print(f"{piece_to_move} moved from {start_pos_str} to {end_pos_str}.")
            
        player_who_moved = self.current_player
        self._decrement_cooldowns(player_who_moved) # Decrement before switching player context
        self.switch_player() # This now calls _start_turn_prep for new player

        if self.is_in_check(self.current_player, self.board): # Uses true board state
            print(f"{self.current_player} is in check!")
        return True

    def handle_ability_activation(self, piece_pos_str, target_pos_str=None):
        piece_coords = algebraic_to_coords(piece_pos_str)
        if not piece_coords: print(f"Invalid piece position: {piece_pos_str}"); return False
        piece = self.board.get_piece(piece_coords)

        if not piece: print(f"No piece at {piece_pos_str}."); return False
        if piece.color != self.current_player: print(f"Cannot use opponent's piece ability."); return False
        if not piece.ability: print(f"{piece} has no ability."); return False
        if piece.ability_cooldown > 0:
            print(f"{piece.ability.name} on cooldown for {piece.ability_cooldown} turn(s)."); return False

        target_coords = None
        if piece.ability.target_type != 'self':
            if not target_pos_str:
                if 'square' in piece.ability.target_type or 'piece' in piece.ability.target_type :
                    print(f"{piece.ability.name} requires a target position."); return False
            else:
                target_coords = algebraic_to_coords(target_pos_str)
                if not target_coords: print(f"Invalid target position: {target_pos_str}"); return False
                if self.board.tile_effects[target_coords[0]][target_coords[1]] == LAVA_EFFECT:
                    print(f"Ability Error: Cannot target LAVA tile at {target_pos_str}."); return False
        
        hypothetical_board_ability = copy.deepcopy(self.board)
        hypothetical_piece = hypothetical_board_ability.get_piece(piece_coords)
        hypothetical_game_context = copy.copy(self); hypothetical_game_context.board = hypothetical_board_ability
        if piece.ability.effect_logic(hypothetical_game_context, hypothetical_piece, target_coords):
            if self.is_in_check(self.current_player, hypothetical_board_ability):
                print(f"Using {piece.ability.name} would put King in check."); return False
        else: return False

        if piece.ability.effect_logic(self, piece, target_coords):
            print(f"{piece} at {piece_pos_str} used {piece.ability.name}.")
            piece.ability_cooldown = piece.ability.cooldown_max
            player_who_used_ability = self.current_player
            self._decrement_cooldowns(player_who_used_ability) # Decrement before switching
            self.switch_player()
            if self.is_in_check(self.current_player, self.board): print(f"{self.current_player} is in check!")
            return True
        else: return False

if __name__ == "__main__":
    game = Game()
    
    while not game.game_over:
        # Display is now based on current player's visibility
        game.board.display(game) 
        print(f"Player: {game.current_player}. Turn: {game.full_turn_counter+1}. Board Evo in: {game.board.turns_before_evolution - game.board.board_evolution_timer} turn(s).")
        
        if game.is_in_check(game.current_player, game.board):
            print(f"{game.current_player.upper()} IS IN CHECK!")

        action_input = input(
            "Action ('move S E', 'ability P [T]', 'togglefog', 'quit'): "
        ).lower().split()
        
        if not action_input: continue
        command = action_input[0]

        if command == 'quit': break
        
        if command == 'togglefog':
            game.board.fog_of_war_on = not game.board.fog_of_war_on
            game.board.update_visibility(game.current_player) # Refresh visibility status
            print(f"Fog of War {'ON' if game.board.fog_of_war_on else 'OFF'}.")
            continue

        if command == 'move':
            if len(action_input) == 3:
                if not game.play_turn(action_input[1], action_input[2]): print("Move failed.")
            else: print("Format: move <start_pos> <end_pos>")
        
        elif command == 'ability':
            if len(action_input) >= 2:
                target = action_input[2] if len(action_input) == 3 else None
                if not game.handle_ability_activation(action_input[1], target): print("Ability failed.")
            else: print("Format: ability <piece_pos> [target_pos]")
        else:
            print(f"Unknown command: {command}.")

    if game.winner: print(f"Game over! {game.winner} wins!")
    print("\nGame finished.")
