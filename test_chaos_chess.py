import unittest
from utils import algebraic_to_coords, coords_to_algebraic
from pieces import Pawn, King # For testing get_revealed_squares and ability assignment
from board import Board # For context for get_revealed_squares, and LAVA_EFFECT
import abilities as abilities_module # For testing ability assignment

class TestUtils(unittest.TestCase):
    def test_algebraic_to_coords(self):
        self.assertEqual(algebraic_to_coords("a1"), (7, 0))
        self.assertEqual(algebraic_to_coords("h8"), (0, 7))
        self.assertEqual(algebraic_to_coords("d4"), (4, 3))
        self.assertEqual(algebraic_to_coords("e2"), (6, 4))
        self.assertIsNone(algebraic_to_coords("z9")) # Invalid
        self.assertIsNone(algebraic_to_coords("a")) # Too short
        self.assertIsNone(algebraic_to_coords("a12")) # Too long

    def test_coords_to_algebraic(self):
        self.assertEqual(coords_to_algebraic((7, 0)), "a1")
        self.assertEqual(coords_to_algebraic((0, 7)), "h8")
        self.assertEqual(coords_to_algebraic((4, 3)), "d4")
        self.assertEqual(coords_to_algebraic((6, 4)), "e2")
        self.assertIsNone(coords_to_algebraic((8, 0))) # Invalid row
        self.assertIsNone(coords_to_algebraic((0, 8))) # Invalid col

class MockBoard:
    """A simplified board mock for testing piece methods that need board context."""
    def __init__(self):
        self.tile_effects = [[None for _ in range(8)] for _ in range(8)]
        # Define LAVA_EFFECT if pieces directly use it via board_object.LAVA_EFFECT
        self.LAVA_EFFECT = "lava"
        self.NO_EFFECT = None

    def get_piece(self, position): # Not used by get_revealed_squares directly
        return None

class TestPieces(unittest.TestCase):
    def setUp(self):
        # A mock board is needed for get_revealed_squares if it checks board.LAVA_EFFECT
        self.mock_board = MockBoard()
        # Mock game and abilities_module for piece initialization if needed for ability assignment tests
        # This setup is a bit more involved due to dependencies.
        class MockGame:
            def __init__(self):
                self.abilities_module = abilities_module
        self.mock_game = MockGame()


    def test_pawn_get_revealed_squares_white(self):
        # White pawn at e2 (6,4)
        # Piece constructor: color, position, piece_type_name, board_ref=None, abilities_module=None
        pawn = Pawn("white", (6, 4), abilities_module=self.mock_game.abilities_module)

        # Test case 1: No blockers
        # Revealed should be d3 (5,3) and f3 (5,5)
        revealed = pawn.get_revealed_squares(self.mock_board, {})
        self.assertCountEqual(revealed, [(5, 3), (5, 5)])

        # Test case 2: Blocker at d3 (piece or lava)
        self.mock_board.tile_effects[5][3] = self.mock_board.LAVA_EFFECT
        revealed_lava_block = pawn.get_revealed_squares(self.mock_board, {})
        # d3 is still revealed (the blocking square itself)
        self.assertCountEqual(revealed_lava_block, [(5, 3), (5, 5)])
        self.mock_board.tile_effects[5][3] = self.mock_board.NO_EFFECT # Reset

        revealed_piece_block = pawn.get_revealed_squares(self.mock_board, {(5,3)})
        self.assertCountEqual(revealed_piece_block, [(5,3), (5,5)])


    def test_pawn_get_revealed_squares_black(self):
        # Black pawn at d7 (1,3)
        pawn = Pawn("black", (1, 3), abilities_module=self.mock_game.abilities_module)
        # Revealed should be c6 (2,2) and e6 (2,4)
        revealed = pawn.get_revealed_squares(self.mock_board, {})
        self.assertCountEqual(revealed, [(2, 2), (2, 4)])

    def test_pawn_get_revealed_squares_edge_board(self):
        # White pawn at a2 (6,0)
        pawn_a2 = Pawn("white", (6,0), abilities_module=self.mock_game.abilities_module)
        # Should only reveal b3 (5,1)
        revealed_a2 = pawn_a2.get_revealed_squares(self.mock_board, {})
        self.assertCountEqual(revealed_a2, [(5,1)])

        # White pawn at h2 (6,7)
        pawn_h2 = Pawn("white", (6,7), abilities_module=self.mock_game.abilities_module)
        # Should only reveal g3 (5,6)
        revealed_h2 = pawn_h2.get_revealed_squares(self.mock_board, {})
        self.assertCountEqual(revealed_h2, [(5,6)])


class TestAbilityAssignment(unittest.TestCase):
    def setUp(self):
        class MockGameForAbilities:
            def __init__(self):
                self.abilities_module = abilities_module
        self.mock_game = MockGameForAbilities()

    def test_pawn_gets_ability(self):
        # Ensure PIECE_ABILITIES for Pawn is not empty in abilities.py for this test to be meaningful
        if not abilities_module.PIECE_ABILITIES.get("PAWN"):
            self.skipTest("No abilities defined for Pawn in abilities.py")

        pawn = Pawn("white", (6,0), abilities_module=self.mock_game.abilities_module)
        pawn.assign_ability() # assign_ability uses self.abilities_module
        self.assertIsNotNone(pawn.ability, "Pawn should be assigned an ability.")
        self.assertIn(pawn.ability, [ab_w[0] for ab_w in abilities_module.PIECE_ABILITIES["PAWN"]])


    def test_king_gets_no_ability(self):
        king = King("white", (7,4), abilities_module=self.mock_game.abilities_module)
        # King's assign_ability method is overridden to explicitly set ability to None
        king.assign_ability()
        self.assertIsNone(king.ability, "King should not be assigned an ability.")


# Conceptual Review Notes (to be summarized later):
# - Interaction of Abilities and Tile Effects: Generally separate, which is simpler. Speed buff + Teleport: Teleport range is fixed. Stun + Heal Tile: Heal tile reduces ability CD, not status effects. This seems fine.
# - Fog of War and AI: AI sees true state. Standard.
# - SP Economy: Quick decision bonus (1 SP) is small. Zone control (1 SP per piece in center) can be 2-4 SP. Captures give 1-9 SP. Redeploy (10 SP), Freeze Pawns (15 SP). Seems like special moves are costly enough to require several captures or sustained zone control. This needs playtesting.
# - Clarity of Display: Text display is busy. Fog (`~~~`) helps. Piece representation `wP(A:R)` is okay. Tile effects being on a second line is good. Overall, it's functional for text.

# Areas for Future Refinement (mental notes for now, will add comments if changing code):
# - AI targeting for abilities/specials is very basic.
# - `Game.play_turn` and other handlers have grown large; could be broken down.
# - Pathfinding for sliding pieces in `is_valid_move` is duplicated (Rook, Bishop, Queen). Could be a helper.
# - `Board.create_piece_by_str_and_color` relies on `self.game.abilities_module`. This tight coupling is okay for now.

if __name__ == '__main__':
    unittest.main()
