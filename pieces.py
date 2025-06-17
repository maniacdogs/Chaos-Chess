from abc import ABC, abstractmethod
import random
try:
    from abilities import ABILITIES_POOL, PIECE_ABILITIES, Ability
except ImportError:
    ABILITIES_POOL = {}
    PIECE_ABILITIES = {}
    Ability = None 

# It's better if board effect constants are defined centrally, but pieces need to know about LAVA.
# We will rely on board_object.LAVA_EFFECT being available.
# A fallback can be defined if direct import from board is problematic during multi-file generation.
LAVA_EFFECT_FALLBACK = "lava" 

class Piece(ABC):
    def __init__(self, color, piece_type, position):
        self.color = color
        self.piece_type = piece_type
        self.position = position
        self.ability = None
        self.ability_cooldown = 0
        self.ability_recharges_on_capture = True
        self.has_speed_buff = False

    def assign_ability(self):
        if not Ability or not PIECE_ABILITIES: return
        possible_abilities_with_weights = PIECE_ABILITIES.get(self.piece_type, [])
        if possible_abilities_with_weights:
            abilities = [item[0] for item in possible_abilities_with_weights]
            weights = [item[1] for item in possible_abilities_with_weights]
            chosen_ability = random.choices(abilities, weights=weights, k=1)[0]
            self.ability = chosen_ability
            self.ability_cooldown = 0
        else:
            self.ability = None
            self.ability_cooldown = 0

    @abstractmethod
    def is_valid_move(self, board, start_pos, end_pos):
        pass

    @abstractmethod
    def get_revealed_squares(self, board_object, all_pieces_positions):
        """
        Calculates squares revealed by this piece.
        board_object: The Board instance, to check for LAVA tiles.
        all_pieces_positions: A set of (r, c) tuples indicating where any piece is.
        Returns a list of (r,c) tuples.
        """
        pass

    def _is_on_board(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def __repr__(self):
        base_repr = f"{self.color[0].lower()}{self.piece_type[0].upper()}"
        ability_str = ""
        if self.ability:
            ability_initial = self.ability.name[0].upper()
            cooldown_status = str(self.ability_cooldown) if self.ability_cooldown > 0 else "R"
            ability_str = f"({ability_initial}:{cooldown_status})"
        return f"{base_repr}{ability_str}"


class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, "pawn", position)

    def is_valid_move(self, board, start_pos, end_pos):
        # (Previous logic for is_valid_move, unchanged by Fog of War)
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        try: lava_val = board.LAVA_EFFECT 
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False

        target_piece = board.get_piece(end_pos)
        direction = -1 if self.color == "white" else 1
        
        if start_col == end_col and target_piece is None:
            if end_row == start_row + direction * 1: return True
            if self.has_speed_buff and end_row == start_row + direction * 2 and \
               board.get_piece((start_row + direction, start_col)) is None and \
               board.tile_effects[start_row + direction][start_col] != lava_val:
                return True 

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
        direction = -1 if self.color == "white" else 1 # White moves towards row 0, Black towards row 7

        # One square diagonally forward left and right
        diag_left_r, diag_left_c = r_start + direction, c_start - 1
        diag_right_r, diag_right_c = r_start + direction, c_start + 1

        if self._is_on_board(diag_left_r, diag_left_c):
            revealed.append((diag_left_r, diag_left_c))
        if self._is_on_board(diag_right_r, diag_right_c):
            revealed.append((diag_right_r, diag_right_c))
        
        # Optional: 1 square directly forward (can be blocked by lava/piece for vision)
        # forward_r, forward_c = r_start + direction, c_start
        # if self._is_on_board(forward_r, forward_c):
        #     revealed.append((forward_r, forward_c))
            # No vision blocking for this single square as per prompt for non-sliding.

        return list(set(revealed)) # Ensure unique squares

class Knight(Piece):
    def __init__(self, color, position):
        super().__init__(color, "knight", position)

    def is_valid_move(self, board, start_pos, end_pos):
        # (Previous logic, unchanged)
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
        possible_moves = [
            (r_start + 2, c_start + 1), (r_start + 2, c_start - 1),
            (r_start - 2, c_start + 1), (r_start - 2, c_start - 1),
            (r_start + 1, c_start + 2), (r_start + 1, c_start - 2),
            (r_start - 1, c_start + 2), (r_start - 1, c_start - 2),
        ]
        for r, c in possible_moves:
            if self._is_on_board(r, c):
                revealed.append((r, c))
                # Knights reveal their landing squares. Vision is not blocked to these squares.
        return list(set(revealed))

class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, "king", position)
        self.ability = None; self.ability_recharges_on_capture = False

    def assign_ability(self): self.ability = None; self.ability_cooldown = 0 

    def is_valid_move(self, board, start_pos, end_pos):
        # (Previous logic, unchanged)
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
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue # Skip self
                nr, nc = r_start + dr, c_start + dc
                if self._is_on_board(nr, nc):
                    revealed.append((nr, nc))
                    # King reveals adjacent squares. Vision is not blocked to these squares.
        return list(set(revealed))

class Rook(Piece):
    def __init__(self, color, position):
        super().__init__(color, "rook", position)

    def is_valid_move(self, board, start_pos, end_pos):
        # (Previous logic, unchanged - already checks lava in path)
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT 
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        if start_row != end_row and start_col != end_col: return False
        target_piece = board.get_piece(end_pos)
        if target_piece is not None and target_piece.color == self.color: return False
        if start_row == end_row:
            step = 1 if end_col > start_col else -1
            for col in range(start_col + step, end_col, step):
                if board.get_piece((start_row, col)) is not None or board.tile_effects[start_row][col] == lava_val: return False 
        else:
            step = 1 if end_row > start_row else -1
            for row in range(start_row + step, end_row, step):
                if board.get_piece((row, start_col)) is not None or board.tile_effects[row][start_col] == lava_val: return False
        return True

    def get_revealed_squares(self, board_object, all_pieces_positions):
        revealed = []
        r_start, c_start = self.position
        try: lava_val = board_object.LAVA_EFFECT 
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Right, Left, Down, Up
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r_start + dr * i, c_start + dc * i
                if not self._is_on_board(nr, nc): break
                revealed.append((nr, nc))
                if (nr, nc) in all_pieces_positions or board_object.tile_effects[nr][nc] == lava_val:
                    break 
        return list(set(revealed))

class Bishop(Piece):
    def __init__(self, color, position):
        super().__init__(color, "bishop", position)

    def is_valid_move(self, board, start_pos, end_pos):
        # (Previous logic, unchanged - already checks lava in path)
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

        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)] # Diagonal
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r_start + dr * i, c_start + dc * i
                if not self._is_on_board(nr, nc): break
                revealed.append((nr, nc))
                if (nr, nc) in all_pieces_positions or board_object.tile_effects[nr][nc] == lava_val:
                    break
        return list(set(revealed))

class Queen(Piece):
    def __init__(self, color, position):
        super().__init__(color, "queen", position)

    def is_valid_move(self, board, start_pos, end_pos):
        # (Previous logic, unchanged - already checks lava in path)
        start_row, start_col = start_pos; end_row, end_col = end_pos
        try: lava_val = board.LAVA_EFFECT 
        except AttributeError: lava_val = LAVA_EFFECT_FALLBACK
        if board.tile_effects[end_row][end_col] == lava_val: return False
        target_piece = board.get_piece(end_pos)
        if target_piece is not None and target_piece.color == self.color: return False
        if start_row == end_row or start_col == end_col: # Rook-like
            if start_row == end_row:
                step = 1 if end_col > start_col else -1
                for col in range(start_col + step, end_col, step):
                    if board.get_piece((start_row, col)) is not None or board.tile_effects[start_row][col] == lava_val: return False
            else:
                step = 1 if end_row > start_row else -1
                for row in range(start_row + step, end_row, step):
                    if board.get_piece((row, start_col)) is not None or board.tile_effects[row][start_col] == lava_val: return False
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

        directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)] # All 8
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r_start + dr * i, c_start + dc * i
                if not self._is_on_board(nr, nc): break
                revealed.append((nr, nc))
                if (nr, nc) in all_pieces_positions or board_object.tile_effects[nr][nc] == lava_val:
                    break
        return list(set(revealed))
