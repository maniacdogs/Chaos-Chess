from pieces import Piece, Pawn, Rook, Knight, Bishop, Queen, King # Assuming pieces.py is in the same directory
import random

# --- Tile Effect Constants ---
NO_EFFECT = None
LAVA_EFFECT = "lava"
BUFF_SPEED_EFFECT = "speed"
HEAL_TILE_EFFECT = "heal"

TILE_EFFECT_SYMBOLS = {
    NO_EFFECT: "..",
    LAVA_EFFECT: "LAVA",
    BUFF_SPEED_EFFECT: "SPD+",
    HEAL_TILE_EFFECT: "HEAL",
}
FOG_SYMBOL = "~~~" # For Fog of War

ALL_TILE_EFFECTS = [LAVA_EFFECT, BUFF_SPEED_EFFECT, HEAL_TILE_EFFECT]
TILE_EFFECT_WEIGHTS = [0.2, 0.4, 0.4]


class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.tile_effects = [[NO_EFFECT for _ in range(8)] for _ in range(8)]
        self.board_evolution_timer = 0
        self.turns_before_evolution = 5
        
        # Fog of War attributes
        self.visibility_grid = [[False for _ in range(8)] for _ in range(8)]
        self.fog_of_war_on = True # Default to ON

        # Make constants accessible for methods if needed, e.g. piece.get_revealed_squares
        self.LAVA_EFFECT = LAVA_EFFECT 
        self.NO_EFFECT = NO_EFFECT

        self.setup_pieces()

    def get_all_pieces(self):
        """Returns a list of all piece objects currently on the board."""
        pieces = []
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece:
                    pieces.append(piece)
        return pieces

    def update_visibility(self, current_player_color):
        """Updates the visibility grid based on the current player's pieces."""
        # Clear previous visibility
        self.visibility_grid = [[False for _ in range(8)] for _ in range(8)]

        if not self.fog_of_war_on:
            self.visibility_grid = [[True for _ in range(8)] for _ in range(8)]
            return

        all_board_pieces_pos = {p.position for p in self.get_all_pieces() if p}
        current_player_pieces = [p for p in self.get_all_pieces() if p and p.color == current_player_color]

        for piece in current_player_pieces:
            # Piece's own square is always visible to itself
            if self._is_on_board(piece.position[0], piece.position[1]):
                 self.visibility_grid[piece.position[0]][piece.position[1]] = True
            
            # Get squares revealed by this piece
            # piece.get_revealed_squares now takes (self [as board_object], all_pieces_positions)
            revealed_by_piece = piece.get_revealed_squares(self, all_board_pieces_pos) 
            for r, c in revealed_by_piece:
                if self._is_on_board(r,c): # Ensure revealed square is on board (should be handled by piece)
                    self.visibility_grid[r][c] = True
    
    def _is_on_board(self, r, c): # Helper for internal use if needed
        return 0 <= r < 8 and 0 <= c < 8

    def setup_pieces(self):
        piece_types_and_rows = {
            0: ("black", Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook),
            1: ("black", Pawn),
            6: ("white", Pawn),
            7: ("white", Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook)
        }
        for row_idx, content in piece_types_and_rows.items():
            color = content[0]
            if content[1] == Pawn: 
                for col_idx in range(8):
                    piece = Pawn(color, (row_idx, col_idx))
                    self.grid[row_idx][col_idx] = piece
                    if piece.piece_type != "king": piece.assign_ability()
            else: 
                piece_classes = content[1:]
                for col_idx, PieceClass in enumerate(piece_classes):
                    piece = PieceClass(color, (row_idx, col_idx))
                    self.grid[row_idx][col_idx] = piece
                    if piece.piece_type != "king": piece.assign_ability()
                    elif PieceClass == King: piece.assign_ability()

    def generate_tile_effects(self, game_instance):
        print("\n--- The Board is Evolving! ---")
        num_effects_to_generate = random.randint(2, 4)
        generated_count = 0; attempts = 0
        occupied_by_king = {p.position for p in self.get_all_pieces() if p and p.piece_type == "king"}
        newly_affected_squares = []

        while generated_count < num_effects_to_generate and attempts < 50:
            attempts += 1
            row, col = random.randint(0, 7), random.randint(0, 7)
            chosen_effect = random.choices(ALL_TILE_EFFECTS, weights=TILE_EFFECT_WEIGHTS, k=1)[0]

            if chosen_effect == self.LAVA_EFFECT:
                if (row, col) in occupied_by_king: continue
                if self.get_piece((row,col)) is not None: continue # Don't place lava under any piece initially

            self.tile_effects[row][col] = chosen_effect
            generated_count += 1
            square_name = game_instance.utils['coords_to_algebraic']((row, col))
            print(f"Square {square_name} is now {chosen_effect.upper()}!")
            newly_affected_squares.append( ( (row,col), chosen_effect) )
        
        for (pos, effect) in newly_affected_squares:
            if effect == self.LAVA_EFFECT:
                piece_on_lava = self.get_piece(pos)
                if piece_on_lava: # Should only happen if rules change or lava spreads
                    print(f"{piece_on_lava} at {game_instance.utils['coords_to_algebraic'](pos)} is on new LAVA! It is destroyed.")
                    self.grid[pos[0]][pos[1]] = None
        self.board_evolution_timer = 0

    def display(self, game_instance):
        print("\n  a    b    c    d    e    f    g    h")
        print("  -----------------------------------------")
        for r_idx in range(8):
            line1_str = f"{8 - r_idx}|" # Piece info
            line2_str = " |" # Tile effect / Fog info
            for c_idx in range(8):
                is_visible = not self.fog_of_war_on or self.visibility_grid[r_idx][c_idx]
                
                if is_visible:
                    piece = self.get_piece((r_idx, c_idx))
                    if piece:
                        line1_str += f"{str(piece):^5}"
                    else:
                        line1_str += "     " 
                    
                    effect = self.tile_effects[r_idx][c_idx]
                    if effect != self.NO_EFFECT:
                        line2_str += f"{TILE_EFFECT_SYMBOLS[effect]:^5}"
                    else:
                        if piece is None: line2_str += " ..  " 
                        else: line2_str += "     " 
                else: # Not visible due to Fog of War
                    line1_str += f"{FOG_SYMBOL:^5}"
                    line2_str += f"{FOG_SYMBOL:^5}" # Or "     " if fog only hides pieces not terrain

            line1_str += f"|{8 - r_idx}"
            print(line1_str)
            line2_str += "|"
            print(line2_str)
            if r_idx < 7:
                print(" |-----|-----|-----|-----|-----|-----|-----|-----|")

        print("  -----------------------------------------")
        print("  a    b    c    d    e    f    g    h\n")
        tile_key = "Tiles: LAVA=Unplayable, SPD+=Speed, HEAL=Cooldown"
        fow_status = f"Fog of War: {'ON' if self.fog_of_war_on else 'OFF'}"
        print(f"{tile_key} | {fow_status}")


    def get_piece(self, position):
        row, col = position
        if self._is_on_board(row,col): return self.grid[row][col]
        return None

    def move_piece(self, start_pos, end_pos, game_instance):
        piece_to_move = self.get_piece(start_pos)
        if not piece_to_move: return None

        if piece_to_move.has_speed_buff:
            # print(f"{piece_to_move} used its speed buff.") # Already printed by game logic potentially
            piece_to_move.has_speed_buff = False 

        captured_piece = self.get_piece(end_pos)
        start_row, start_col = start_pos; end_row, end_col = end_pos
        
        self.grid[end_row][end_col] = piece_to_move
        self.grid[start_row][start_col] = None
        piece_to_move.position = (end_row, end_col) # Ensure tuple format

        landed_tile_effect = self.tile_effects[end_row][end_col]
        if landed_tile_effect == BUFF_SPEED_EFFECT:
            if not piece_to_move.has_speed_buff:
                piece_to_move.has_speed_buff = True
                print(f"{piece_to_move} landed on Speed Tile at {game_instance.utils['coords_to_algebraic'](end_pos)}! Next move buffed.")
        elif landed_tile_effect == HEAL_TILE_EFFECT:
            if piece_to_move.ability and piece_to_move.ability_cooldown > 0:
                reduction = 2; original_cooldown = piece_to_move.ability_cooldown
                piece_to_move.ability_cooldown = max(0, piece_to_move.ability_cooldown - reduction)
                print(f"{piece_to_move} landed on Heal Tile. Cooldown {original_cooldown} -> {piece_to_move.ability_cooldown}.")
        return captured_piece

if __name__ == '__main__': # Basic test
    class MockGame:
        def __init__(self): self.utils = {'coords_to_algebraic': lambda c: f"({c[0]},{c[1]})"}
    mock_game = MockGame()
    board = Board()
    # board.fog_of_war_on = True # default
    board.update_visibility("white") # Simulate white's turn
    board.display(mock_game)
    
    print("\nSwitching to black's view (conceptual, no actual move made):")
    board.update_visibility("black")
    board.display(mock_game)

    print("\nTurning Fog of War OFF:")
    board.fog_of_war_on = False
    board.update_visibility("white") # Player doesn't matter if FoW is off
    board.display(mock_game)
