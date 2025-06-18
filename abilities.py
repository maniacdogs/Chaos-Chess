from collections import namedtuple

# Using a class for Ability for potential future methods, though namedtuple is also good.
class Ability:
    def __init__(self, name, description, effect_logic, cooldown_max, target_type, range_limit=None):
        self.name = name
        self.description = description
        self.effect_logic = effect_logic
        self.cooldown_max = cooldown_max
        self.target_type = target_type # e.g., 'empty_square_range_2', 'ally_piece_adjacent'
        self.range_limit = range_limit # For abilities like Teleport

    def __repr__(self):
        return f"Ability({self.name}, CD:{self.cooldown_max}, Target:{self.target_type})"

# --- Effect Logic Functions ---
# These functions will modify the board and piece states.
# They should return True if the ability was successfully used, False otherwise.

def teleport_effect(game, piece, target_coords):
    """
    Effect: Moves the piece to an empty target_coords if it's within range_limit.
    game: The current Game instance (provides access to board, etc.)
    piece: The piece activating the ability.
    target_coords: The (row, col) tuple for the destination.
    """
    board = game.board
    range_limit = piece.ability.range_limit if piece.ability and piece.ability.range_limit is not None else 2 # Default range

    if not target_coords: # Basic check if a target is even provided (might be handled by input parser too)
        print("Teleport failed: No target square provided.")
        return False

    start_pos = piece.position
    row_diff = abs(start_pos[0] - target_coords[0])
    col_diff = abs(start_pos[1] - target_coords[1])

    # Check if target is empty and within range (using Chebyshev distance for square range)
    if board.get_piece(target_coords) is None and max(row_diff, col_diff) <= range_limit:
        if start_pos == target_coords: # Cannot teleport to own square
            print(f"{piece} Teleport failed: Cannot teleport to the same square.")
            return False

        board.grid[start_pos[0]][start_pos[1]] = None # Empty old square
        board.grid[target_coords[0]][target_coords[1]] = piece # Place piece in new square
        piece.position = target_coords
        print(f"{piece} at {game.utils.coords_to_algebraic(start_pos)} teleported to {game.utils.coords_to_algebraic(target_coords)}.")
        return True
    else:
        if board.get_piece(target_coords) is not None:
            print(f"{piece} Teleport failed: Target square {game.utils.coords_to_algebraic(target_coords)} is occupied by {board.get_piece(target_coords)}.")
        else: # Out of range
            print(f"{piece} Teleport failed: Target {game.utils.coords_to_algebraic(target_coords)} is out of range (max {range_limit} units).")
        return False

def swap_ally_effect(game, piece, target_ally_coords):
    """
    Effect: Swaps the position of 'piece' with an allied piece at 'target_ally_coords'.
    game: The current Game instance.
    piece: The piece activating the ability.
    target_ally_coords: The (row, col) of the allied piece to swap with.
    """
    board = game.board

    if not target_ally_coords:
        print("Swap failed: No target piece provided.")
        return False

    start_pos_piece1 = piece.position
    piece2 = board.get_piece(target_ally_coords)

    if piece2 is None:
        print(f"{piece} Swap failed: No piece at target square {game.utils.coords_to_algebraic(target_ally_coords)}.")
        return False
    if piece2.color != piece.color:
        print(f"{piece} Swap failed: Cannot swap with opponent's piece {piece2} at {game.utils.coords_to_algebraic(target_ally_coords)}.")
        return False
    if piece == piece2: # Cannot swap with oneself
        print(f"{piece} Swap failed: Cannot swap with itself.")
        return False

    # Perform swap
    board.grid[start_pos_piece1[0]][start_pos_piece1[1]] = piece2
    board.grid[target_ally_coords[0]][target_ally_coords[1]] = piece

    piece.position = target_ally_coords
    piece2.position = start_pos_piece1

    print(f"{piece} at {game.utils.coords_to_algebraic(start_pos_piece1)} swapped with {piece2} at {game.utils.coords_to_algebraic(target_ally_coords)}.")
    return True

# --- Ability Definitions ---
ABILITIES_POOL = {
    "Teleport_R2": Ability(name="Teleport (2)",
                           description="Teleport to an empty square within 2 units.",
                           effect_logic=teleport_effect,
                           cooldown_max=4,
                           target_type='empty_square', # Generic, actual validation in effect_logic
                           range_limit=2),
    "SwapWithAlly_Adj": Ability(name="Swap Ally (Adj)",
                                description="Swap places with an adjacent allied piece.",
                                effect_logic=swap_ally_effect,
                                cooldown_max=5,
                                target_type='ally_piece_adjacent'), # Adjacency check could be part of effect or pre-check
    # Future abilities:
    # "Stun": Ability("Stun", "Stun an adjacent enemy piece for 1 turn.", stun_effect, cooldown_max=3, target_type='enemy_piece_adjacent'),
}

# --- Piece Ability Assignments ---
# Defines which abilities pieces can get, and the weight for random selection.
# (Ability_Object, weight)
PIECE_ABILITIES = {
    "Pawn": [
        (ABILITIES_POOL["Teleport_R2"], 0.6),
        (ABILITIES_POOL["SwapWithAlly_Adj"], 0.4), # Pawns might swap with other pawns or backline pieces
    ],
    "Rook": [
        (ABILITIES_POOL["Teleport_R2"], 0.5), # Could be a shorter range teleport for rooks or a different ability
        # (ABILITIES_POOL["Barricade"], 0.5),
    ],
    "Knight": [
        (ABILITIES_POOL["SwapWithAlly_Adj"], 0.7),
        (ABILITIES_POOL["Teleport_R2"], 0.3), # Knights are already mobile, so teleport is less impactful or differently used
    ],
    "Bishop": [
        (ABILITIES_POOL["Teleport_R2"], 0.5),
        (ABILITIES_POOL["SwapWithAlly_Adj"], 0.5), # Bishops swapping could open diagonal lines
    ],
    "Queen": [
        (ABILITIES_POOL["Teleport_R2"], 0.8), # Queen with teleport is very strong
        (ABILITIES_POOL["SwapWithAlly_Adj"], 0.2),
    ],
    "King": [] # Kings do not get abilities
}

if __name__ == '__main__':
    # Basic test for ability definition
    # Note: Effect logic functions need a 'game' object and 'piece' object to run,
    # so they can't be tested directly here without mocks or simple game setup.

    print("Available abilities in the pool:")
    for name, ability in ABILITIES_POOL.items():
        print(f"- {name}: {ability.description} (Target: {ability.target_type}, Cooldown: {ability.cooldown_max})")

    print("\nAbilities for piece types:")
    for piece_type, abilities_with_weights in PIECE_ABILITIES.items():
        print(f"\n{piece_type}:")
        if abilities_with_weights:
            for ability, weight in abilities_with_weights:
                print(f"  - {ability.name} (Weight: {weight})")
        else:
            print("  - None")

    # Example of how an ability might be stored on a piece (conceptual)
    # class MockPiece:
    #     def __init__(self, ptype, ability_obj):
    #         self.ptype = ptype
    #         self.ability = ability_obj
    #         self.ability_cooldown = 0
    #         self.position = (0,0) # dummy
    #         self.color = "white"
    #     def __repr__(self):
    #         return f"{self.color} {self.ptype}"


    # mock_pawn = MockPiece("Pawn", ABILITIES_POOL["Teleport_R2"])
    # print(f"\nMock Pawn has ability: {mock_pawn.ability.name}")

    # The effect functions teleport_effect and swap_ally_effect expect a 'game' object
    # which has 'board' and 'utils', and a 'piece' object.
    # A full test would require more setup.
    print("\nNote: Effect logic functions require a game context to be fully tested.")
