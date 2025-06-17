from pieces import Piece, Pawn, Rook, Knight, Bishop, Queen, King

class Board:
    """
    Represents the chess board.
    """
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.setup_pieces()

    def setup_pieces(self):
        """
        Initializes the board with pieces in their starting positions
        and assigns them abilities.
        """
        piece_types_and_rows = {
            0: ("black", Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook), # Back rank
            1: ("black", Pawn), # Pawn rank
            6: ("white", Pawn), # Pawn rank
            7: ("white", Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook)  # Back rank
        }

        for row_idx, (color, P1_type, P2_type, P3_type, P4_type, P5_type, P6_type, P7_type, P8_type) in piece_types_and_rows.items():
            if P1_type == Pawn: # Pawn rows
                for col_idx in range(8):
                    piece = P1_type(color, (row_idx, col_idx))
                    self.grid[row_idx][col_idx] = piece
                    if piece.piece_type != "king": # Kings handle their own ability assignment (to None)
                        piece.assign_ability()
            else: # Back ranks
                piece_classes = [P1_type, P2_type, P3_type, P4_type, P5_type, P6_type, P7_type, P8_type]
                for col_idx, PieceClass in enumerate(piece_classes):
                    piece = PieceClass(color, (row_idx, col_idx))
                    self.grid[row_idx][col_idx] = piece
                    if piece.piece_type != "king":
                         piece.assign_ability()
                    # For Kings, assign_ability() is overridden in pieces.py to do nothing or set ability to None.
                    # If it's a King, its specific assign_ability method will be called.
                    elif PieceClass == King: # Explicitly ensure King's assign_ability is called if it has specific logic
                        piece.assign_ability()


        # print("Board setup with all initial pieces and abilities assigned.") # For debugging

    def display(self):
        """
        Provides a simple text-based representation of the board.
        Uses piece.__repr__() for display.
        """
        print("\n  a  b  c  d  e  f  g  h")
        print("  -------------------------") # Adjusted for potentially wider piece representation
        for i, row_val in enumerate(range(8)): # row_val goes from 0 to 7
            print(f"{8 - i}|", end="") # Row numbers 8 down to 1
            for col_val in range(8):
                piece = self.grid[row_val][col_val]
                if piece:
                    # Piece __repr__ will give about 3-6 chars e.g. wP(T:R) or bR(S:3)
                    # Center the piece representation in a 4-char wide cell for alignment
                    print(f"{str(piece):^4}", end="") 
                else:
                    print(" .. ", end="") # Empty square, 4 chars wide
            print(f"|{8 - i}")
        print("  -------------------------")
        print("  a  b  c  d  e  f  g  h\n")

    def get_piece(self, position):
        """
        Returns the piece at a given position (row, col).
        """
        row, col = position
        if 0 <= row < 8 and 0 <= col < 8:
            return self.grid[row][col]
        return None

    def move_piece(self, start_pos, end_pos):
        """
        Moves a piece from start_pos to end_pos.
        If end_pos contains an opponent's piece, it's captured.
        Updates the piece's internal position attribute.
        Returns the captured piece, if any.
        """
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        piece_to_move = self.get_piece(start_pos)
        
        if piece_to_move is None:
            return None # No piece to move

        captured_piece = self.get_piece(end_pos)
        # Note: Validation for capturing own piece should be in piece.is_valid_move or Game.play_turn

        self.grid[end_row][end_col] = piece_to_move
        self.grid[start_row][start_col] = None
        
        piece_to_move.position = end_pos
        
        return captured_piece


if __name__ == '__main__':
    board = Board()
    board.display()
    # Example: Check a piece's ability after setup
    # piece_on_e2 = board.get_piece((6,4)) # White Pawn on e2
    # if piece_on_e2 and piece_on_e2.ability:
    #     print(f"Piece at e2: {piece_on_e2} has ability: {piece_on_e2.ability.name} (Cooldown: {piece_on_e2.ability_cooldown})")
    # else:
    #     print(f"Piece at e2: {piece_on_e2} has no ability or piece not found.")

    # piece_on_a1 = board.get_piece((7,0)) # White Rook on a1
    # if piece_on_a1 and piece_on_a1.ability:
    #     print(f"Piece at a1: {piece_on_a1} has ability: {piece_on_a1.ability.name} (Cooldown: {piece_on_a1.ability_cooldown})")
    # else:
    #     print(f"Piece at a1: {piece_on_a1} has no ability or piece not found.")

    # king_on_e1 = board.get_piece((7,4)) # White King
    # if king_on_e1:
    #     print(f"Piece at e1: {king_on_e1}, Ability: {king_on_e1.ability}")

    pass
