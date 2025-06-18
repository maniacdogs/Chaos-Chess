from pieces import Piece, Pawn, Rook, Knight, Bishop, Queen, King
import random

NO_EFFECT = None
LAVA_EFFECT = "lava"
BUFF_SPEED_EFFECT = "speed"
HEAL_TILE_EFFECT = "heal"

TILE_EFFECT_SYMBOLS = {
    NO_EFFECT: "..", LAVA_EFFECT: "LAVA", BUFF_SPEED_EFFECT: "SPD+", HEAL_TILE_EFFECT: "HEAL",
}
FOG_SYMBOL = "~~~"
ALL_TILE_EFFECTS = [LAVA_EFFECT, BUFF_SPEED_EFFECT, HEAL_TILE_EFFECT]
TILE_EFFECT_WEIGHTS = [0.2, 0.4, 0.4]

class Board:
    def __init__(self, game_ref): # game_ref is the Game instance
        self.game = game_ref # Store reference to game instance
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.tile_effects = [[NO_EFFECT for _ in range(8)] for _ in range(8)]
        self.board_evolution_timer = 0
        self.turns_before_evolution = 5
        self.visibility_grid = [[False for _ in range(8)] for _ in range(8)]
        self.fog_of_war_on = True
        self.LAVA_EFFECT = LAVA_EFFECT
        self.NO_EFFECT = NO_EFFECT
        self.PIECE_CLASS_MAP = { # For create_piece_by_str_and_color
            "PAWN": Pawn, "ROOK": Rook, "KNIGHT": Knight,
            "BISHOP": Bishop, "QUEEN": Queen, "KING": King
        }
        self.setup_pieces()

    def create_piece_by_str_and_color(self, piece_type_name_str, color, position_tuple):
        """Creates and returns a new piece instance."""
        piece_type_upper = piece_type_name_str.upper()
        PieceClass = self.PIECE_CLASS_MAP.get(piece_type_upper)
        if PieceClass:
            # Piece constructor: color, position, piece_type_name, board_ref=None, abilities_module=None
            # abilities_module comes from game instance
            new_piece = PieceClass(color, position_tuple, abilities_module=self.game.abilities_module)
            return new_piece
        # print(f"Error: Unknown piece type '{piece_type_name_str}' for creation.") # Debug
        return None

    def get_all_pieces(self):
        pieces = []
        for r in range(8):
            for c in range(8):
                if self.grid[r][c]: pieces.append(self.grid[r][c])
        return pieces

    def update_visibility(self, current_player_color):
        self.visibility_grid = [[False for _ in range(8)] for _ in range(8)]
        if not self.fog_of_war_on:
            self.visibility_grid = [[True for _ in range(8)] for _ in range(8)]; return

        all_board_pieces_pos = {p.position for p in self.get_all_pieces() if p}
        current_player_pieces = [p for p in self.get_all_pieces() if p and p.color == current_player_color]

        for piece in current_player_pieces:
            if self._is_on_board(piece.position[0], piece.position[1]):
                 self.visibility_grid[piece.position[0]][piece.position[1]] = True
            revealed_by_piece = piece.get_revealed_squares(self, all_board_pieces_pos)
            for r, c in revealed_by_piece:
                if self._is_on_board(r,c): self.visibility_grid[r][c] = True

    def _is_on_board(self, r, c): return 0 <= r < 8 and 0 <= c < 8

    def setup_pieces(self):
        # Piece type names (strings) for the constructor
        piece_configs = {
            0: ("black", [("Rook", Rook), ("Knight", Knight), ("Bishop", Bishop), ("Queen", Queen),
                          ("King", King), ("Bishop", Bishop), ("Knight", Knight), ("Rook", Rook)]),
            1: ("black", [("Pawn", Pawn)] * 8),
            6: ("white", [("Pawn", Pawn)] * 8),
            7: ("white", [("Rook", Rook), ("Knight", Knight), ("Bishop", Bishop), ("Queen", Queen),
                          ("King", King), ("Bishop", Bishop), ("Knight", Knight), ("Rook", Rook)])
        }

        for row_idx, (color, piece_row_config) in piece_configs.items():
            for col_idx, (type_name, PieceClass) in enumerate(piece_row_config if isinstance(piece_row_config[0], tuple) else [(name_class[0], name_class[1]) for name_class in piece_row_config for _i in range(1)] if row_idx == 1 or row_idx == 6 else []):
                # Corrected enumeration for pawn rows
                if row_idx == 1 or row_idx == 6: # Pawn rows
                     type_name_for_pawn_row = piece_row_config[0][0] # "Pawn"
                     PieceClass_for_pawn_row = piece_row_config[0][1] # Pawn class
                     # Piece constructor: color, position, piece_type_name, board_ref=None, abilities_module=None
                     piece = PieceClass_for_pawn_row(color, (row_idx, col_idx), abilities_module=self.game.abilities_module)


                else: # Back ranks
                     piece = PieceClass(color, (row_idx, col_idx), abilities_module=self.game.abilities_module)

                self.grid[row_idx][col_idx] = piece
                # assign_ability is now called within Piece.__init__ if abilities_module is provided,
                # or can be called after if abilities_module is resolved later.
                # Let's ensure it's called after piece creation if not in init.
                # Current Piece.__init__ does not call assign_ability. It expects abilities_module for later call.
                # The plan was "assign_ability(self, abilities_module)"
                # The pieces.py has assign_ability(self) which uses self.abilities_module.
                # So, Piece.__init__ correctly stores abilities_module, then assign_ability is called.
                piece.assign_ability() # This should now work as abilities_module is set on piece.


    def generate_tile_effects(self, game_instance): # game_instance is self.game from Board's perspective
        print("\n--- The Board is Evolving! ---")
        num_effects = random.randint(2,4); generated=0; attempts=0
        kings = {p.position for p in self.get_all_pieces() if p.piece_type_name == "KING"}
        newly_affected = []
        while generated < num_effects and attempts < 50:
            attempts+=1; r,c = random.randint(0,7), random.randint(0,7)
            effect = random.choices(ALL_TILE_EFFECTS, weights=TILE_EFFECT_WEIGHTS, k=1)[0]
            if effect == self.LAVA_EFFECT and ((r,c) in kings or self.get_piece((r,c)) is not None): continue
            self.tile_effects[r][c] = effect; generated+=1
            sq_name = self.game.utils['coords_to_algebraic']((r,c))
            print(f"Square {sq_name} is now {effect.upper()}!")
            newly_affected.append(((r,c), effect))
        for (pos, effect) in newly_affected:
            if effect == self.LAVA_EFFECT:
                p = self.get_piece(pos)
                if p : print(f"{p} at {self.game.utils['coords_to_algebraic'](pos)} is on new LAVA! Destroyed."); self.grid[pos[0]][pos[1]] = None
        self.board_evolution_timer = 0

    def display(self, game_instance): # game_instance is self.game
        print("\n  a    b    c    d    e    f    g    h")
        print("  -----------------------------------------")
        for r_idx in range(8):
            l1=f"{8-r_idx}|"; l2=" |"
            for c_idx in range(8):
                vis = not self.fog_of_war_on or self.visibility_grid[r_idx][c_idx]
                if vis:
                    p = self.get_piece((r_idx,c_idx)); l1+=f"{str(p):^5}" if p else "     "
                    eff = self.tile_effects[r_idx][c_idx]
                    l2+=f"{TILE_EFFECT_SYMBOLS[eff]:^5}" if eff!=self.NO_EFFECT else (" ..  " if not p else "     ")
                else: l1+=f"{FOG_SYMBOL:^5}"; l2+=f"{FOG_SYMBOL:^5}"
            print(l1+f"|{8-r_idx}"); print(l2+"|")
            if r_idx<7: print(" |-----|-----|-----|-----|-----|-----|-----|-----|")
        print("  -----------------------------------------")
        print("  a    b    c    d    e    f    g    h\n")
        print(f"Tiles: LAVA | SPD+ | HEAL | FoW: {'ON' if self.fog_of_war_on else 'OFF'}")


    def get_piece(self, position):
        r,c = position; return self.grid[r][c] if self._is_on_board(r,c) else None

    def move_piece(self, start_pos, end_pos, game_instance): # game_instance is self.game
        piece_to_move = self.get_piece(start_pos)
        if not piece_to_move: return None
        if piece_to_move.has_speed_buff: piece_to_move.has_speed_buff = False

        captured_piece = self.get_piece(end_pos)
        if captured_piece:
            # Use game_instance (which is self.game) to access SP values and methods
            sp_val = self.game.PIECE_SP_VALUES.get(captured_piece.piece_type_name.upper(), 0)
            self.game.add_sp(piece_to_move.color, sp_val)
            self.game.add_lost_piece(captured_piece.color, captured_piece.piece_type_name.upper())
            # print(f"{piece_to_move.color} gains {sp_val} SP for capturing {captured_piece.piece_type_name}") # Debug
            # print(f"{captured_piece.color} lost pieces: {self.game.player_lost_pieces[captured_piece.color]}") # Debug

        sr,sc = start_pos; er,ec = end_pos
        self.grid[er][ec] = piece_to_move; self.grid[sr][sc] = None
        piece_to_move.position = (er,ec)

        eff = self.tile_effects[er][ec]
        if eff == BUFF_SPEED_EFFECT and not piece_to_move.has_speed_buff:
            piece_to_move.has_speed_buff = True; print(f"{piece_to_move} landed on Speed Tile! Next move buffed.")
        elif eff == HEAL_TILE_EFFECT and piece_to_move.ability and piece_to_move.ability_cooldown > 0:
            orig_cd = piece_to_move.ability_cooldown
            piece_to_move.ability_cooldown = max(0, orig_cd - 2)
            print(f"{piece_to_move} on Heal Tile. Cooldown {orig_cd} -> {piece_to_move.ability_cooldown}.")
        return captured_piece
