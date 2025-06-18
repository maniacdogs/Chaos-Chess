from abc import ABC, abstractmethod
import random

# Assuming abilities.py might not be directly importable during the sequence of file creations.
# Piece.assign_ability will rely on self.abilities_module being set.
# LAVA_EFFECT_FALLBACK is for vision checks if board constants aren't available yet.
LAVA_EFFECT_FALLBACK = "lava"

class Piece(ABC):
    def __init__(self, color, position, piece_type_name, board_ref=None, abilities_module=None): # board_ref is for future use, not strictly needed by Piece itself yet
        self.color = color
        self.position = position # (row, col) tuple
        self.piece_type_name = piece_type_name.upper() # Store as uppercase e.g. "PAWN"

        self.abilities_module = abilities_module # Reference to the abilities module/object
        self.ability = None
        self.ability_cooldown = 0
        self.ability_recharges_on_capture = True

        self.has_speed_buff = False
        self.status_effects = {} # e.g., {'frozen': 2} means frozen for 2 more of this player's turns

    def assign_ability(self):
        """Assigns an ability based on piece type using self.abilities_module."""
        if not self.abilities_module or not hasattr(self.abilities_module, 'PIECE_ABILITIES') or \
           not self.piece_type_name in self.abilities_module.PIECE_ABILITIES:
            self.ability = None
            self.ability_cooldown = 0
            return

        possible_abilities_with_weights = self.abilities_module.PIECE_ABILITIES.get(self.piece_type_name, [])

        if possible_abilities_with_weights:
            # Ensure items in list are (Ability object, weight)
            # And Ability object has a 'name' attribute
            valid_options = [(item[0], item[1]) for item in possible_abilities_with_weights if hasattr(item[0], 'name')]
            if not valid_options:
                 self.ability = None; self.ability_cooldown = 0; return

            abilities = [item[0] for item in valid_options]
            weights = [item[1] for item in valid_options]

            if not abilities: # Should not happen if valid_options was populated
                 self.ability = None; self.ability_cooldown = 0; return

            chosen_ability_list = random.choices(abilities, weights=weights, k=1)
            if chosen_ability_list:
                 self.ability = chosen_ability_list[0]
                 self.ability_cooldown = 0
            else: # Should not be reached if random.choices works as expected with valid inputs
                 self.ability = None; self.ability_cooldown = 0;
        else:
            self.ability = None
            self.ability_cooldown = 0

    def is_action_allowed(self):
        """Checks if status effects prevent any action."""
        if 'frozen' in self.status_effects and self.status_effects['frozen'] > 0:
            # print(f"{self} is frozen for {self.status_effects['frozen']} more turn(s).") # Debug
            return False
        return True

    @abstractmethod
    def is_valid_move(self, board, start_pos, end_pos):
        pass

    @abstractmethod
    def get_revealed_squares(self, board_object, all_pieces_positions):
        pass

    def _is_on_board(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def __repr__(self):
        # Using piece_type_name which should be like "PAWN" -> "P"
        type_initial = self.piece_type_name[0].upper() if self.piece_type_name else "?"
        base_repr = f"{self.color[0].lower()}{type_initial}"

        ability_str = ""
        if self.ability and hasattr(self.ability, 'name'):
            ability_initial = self.ability.name[0].upper()
            cooldown_status = str(self.ability_cooldown) if self.ability_cooldown > 0 else "R"
            ability_str = f"({ability_initial}:{cooldown_status})"

        status_str = ""
        if 'frozen' in self.status_effects and self.status_effects['frozen'] > 0:
            status_str = "(F)"

        return f"{base_repr}{ability_str}{status_str}"


# Subclasses will call super().__init__ with their specific piece_type_name.

class Pawn(Piece):
    def __init__(self, color, position, board_ref=None, abilities_module=None):
        super().__init__(color, position, "Pawn", board_ref, abilities_module)

    def is_valid_move(self, board, start_pos, end_pos):
        if not self.is_action_allowed(): return False
        # (Previous logic for is_valid_move)
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        target_piece = board.get_piece(end_pos)
        direction = -1 if self.color == "white" else 1
        if start_col == end_col and target_piece is None:
            if end_row == start_row + direction * 1: return True
            if self.has_speed_buff and end_row == start_row + direction * 2 and \
               board.get_piece((start_row + direction, start_col)) is None and \
               board.tile_effects[start_row + direction][start_col] != lava_val: return True
        starting_row = 6 if self.color == "white" else 1
        if start_row == starting_row and start_col == end_col and target_piece is None:
            path_step1_clear = board.get_piece((start_row + direction, start_col)) is None and \
                               board.tile_effects[start_row + direction][start_col] != lava_val
            if end_row == start_row + 2 * direction and path_step1_clear: return True
            if self.has_speed_buff and end_row == start_row + 3 * direction and path_step1_clear:
                path_step2_clear = board.get_piece((start_row + 2 * direction, start_col)) is None and \
                                   board.tile_effects[start_row + 2 * direction][start_col] != lava_val
                if path_step2_clear: return True
        if abs(start_col - end_col) == 1 and end_row == start_row + direction:
            if target_piece is not None and target_piece.color != self.color: return True
        return False

    def get_revealed_squares(self, board_object, all_pieces_positions):
        revealed = []
        r_start, c_start = self.position
        direction = -1 if self.color == "white" else 1
        diag_left_r, diag_left_c = r_start + direction, c_start - 1
        diag_right_r, diag_right_c = r_start + direction, c_start + 1
        if self._is_on_board(diag_left_r, diag_left_c): revealed.append((diag_left_r, diag_left_c))
        if self._is_on_board(diag_right_r, diag_right_c): revealed.append((diag_right_r, diag_right_c))
        return list(set(revealed))

class Rook(Piece):
    def __init__(self, color, position, board_ref=None, abilities_module=None):
        super().__init__(color, position, "Rook", board_ref, abilities_module)

    def is_valid_move(self, board, start_pos, end_pos):
        if not self.is_action_allowed(): return False
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        if start_row != end_row and start_col != end_col: return False
        target_piece = board.get_piece(end_pos)
        if target_piece is not None and target_piece.color == self.color: return False
        if start_row == end_row:
            step = 1 if end_col > start_col else -1
            for col_val in range(start_col + step, end_col, step): # Corrected variable name
                if board.get_piece((start_row, col_val)) is not None or board.tile_effects[start_row][col_val] == lava_val: return False
        else:
            step = 1 if end_row > start_row else -1
            for row_val in range(start_row + step, end_row, step): # Corrected variable name
                if board.get_piece((row_val, start_col)) is not None or board.tile_effects[row_val][start_col] == lava_val: return False
        return True

    def get_revealed_squares(self, board_object, all_pieces_positions):
        revealed = []
        r_start, c_start = self.position
        try: lava_val = board_object.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r_start + dr * i, c_start + dc * i
                if not self._is_on_board(nr, nc): break
                revealed.append((nr, nc))
                if (nr, nc) in all_pieces_positions or board_object.tile_effects[nr][nc] == lava_val: break
        return list(set(revealed))

class Knight(Piece):
    def __init__(self, color, position, board_ref=None, abilities_module=None):
        super().__init__(color, position, "Knight", board_ref, abilities_module)

    def is_valid_move(self, board, start_pos, end_pos):
        if not self.is_action_allowed(): return False
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        row_diff = abs(start_row - end_row); col_diff = abs(start_col - end_col)
        if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)): return False
        target_piece = board.get_piece(end_pos)
        if target_piece is not None and target_piece.color == self.color: return False
        return True

    def get_revealed_squares(self, board_object, all_pieces_positions):
        revealed = []
        r_start, c_start = self.position
        possible_moves = [(r_start+2,c_start+1),(r_start+2,c_start-1),(r_start-2,c_start+1),(r_start-2,c_start-1),
                          (r_start+1,c_start+2),(r_start+1,c_start-2),(r_start-1,c_start+2),(r_start-1,c_start-2)]
        for r, c in possible_moves:
            if self._is_on_board(r, c): revealed.append((r,c))
        return list(set(revealed))

class Bishop(Piece):
    def __init__(self, color, position, board_ref=None, abilities_module=None):
        super().__init__(color, position, "Bishop", board_ref, abilities_module)

    def is_valid_move(self, board, start_pos, end_pos):
        if not self.is_action_allowed(): return False
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        if abs(start_row - end_row) != abs(start_col - end_col): return False
        target_piece = board.get_piece(end_pos)
        if target_piece is not None and target_piece.color == self.color: return False
        row_step = 1 if end_row > start_row else -1; col_step = 1 if end_col > start_col else -1
        cr, cc = start_row + row_step, start_col + col_step
        while cr != end_row:
            if board.get_piece((cr, cc)) is not None or board.tile_effects[cr][cc] == lava_val: return False
            cr += row_step; cc += col_step
        return True

    def get_revealed_squares(self, board_object, all_pieces_positions):
        revealed = []
        r_start, c_start = self.position
        try: lava_val = board_object.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        directions = [(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r_start + dr*i, c_start + dc*i
                if not self._is_on_board(nr, nc): break
                revealed.append((nr,nc))
                if (nr, nc) in all_pieces_positions or board_object.tile_effects[nr][nc] == lava_val: break
        return list(set(revealed))

class Queen(Piece):
    def __init__(self, color, position, board_ref=None, abilities_module=None):
        super().__init__(color, position, "Queen", board_ref, abilities_module)

    def is_valid_move(self, board, start_pos, end_pos):
        if not self.is_action_allowed(): return False
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        target_piece = board.get_piece(end_pos)
        if target_piece is not None and target_piece.color == self.color: return False
        if start_row == end_row or start_col == end_col: # Rook-like
            if start_row == end_row:
                step = 1 if end_col > start_col else -1
                for col_val in range(start_col + step, end_col, step):
                    if board.get_piece((start_row, col_val)) is not None or board.tile_effects[start_row][col_val] == lava_val: return False
            else:
                step = 1 if end_row > start_row else -1
                for row_val in range(start_row + step, end_row, step):
                    if board.get_piece((row_val, start_col)) is not None or board.tile_effects[row_val][start_col] == lava_val: return False
            return True
        if abs(start_row - end_row) == abs(start_col - end_col): # Bishop-like
            row_step = 1 if end_row > start_row else -1; col_step = 1 if end_col > start_col else -1
            cr, cc = start_row + row_step, start_col + col_step
            while cr != end_row:
                if board.get_piece((cr, cc)) is not None or board.tile_effects[cr][cc] == lava_val: return False
                cr += row_step; cc += col_step
            return True
        return False

    def get_revealed_squares(self, board_object, all_pieces_positions):
        revealed = []
        r_start, c_start = self.position
        try: lava_val = board_object.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        directions = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r_start + dr*i, c_start + dc*i
                if not self._is_on_board(nr, nc): break
                revealed.append((nr,nc))
                if (nr, nc) in all_pieces_positions or board_object.tile_effects[nr][nc] == lava_val: break
        return list(set(revealed))

class King(Piece):
    def __init__(self, color, position, board_ref=None, abilities_module=None):
        super().__init__(color, position, "King", board_ref, abilities_module)
        self.ability = None; self.ability_recharges_on_capture = False

    def assign_ability(self): self.ability = None; self.ability_cooldown = 0

    def is_valid_move(self, board, start_pos, end_pos):
        if not self.is_action_allowed(): return False
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        row_diff = abs(start_row - end_row); col_diff = abs(start_col - end_col)
        if not (row_diff <= 1 and col_diff <= 1 and (row_diff + col_diff > 0)): return False
        target_piece = board.get_piece(end_pos)
        if target_piece is not None and target_piece.color == self.color: return False
        return True

    def get_revealed_squares(self, board_object, all_pieces_positions):
        revealed = []
        r_start, c_start = self.position
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r_start + dr, c_start + dc
                if self._is_on_board(nr, nc): revealed.append((nr,nc))
        return list(set(revealed))
