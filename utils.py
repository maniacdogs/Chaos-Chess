def algebraic_to_coords(algebraic_notation_str):
    """
    Converts algebraic notation (e.g., "e2") to board coordinates (row, col).
    (0,0) is 'a8', (7,7) is 'h1'.
    Row index maps from '8' (0) down to '1' (7).
    Col index maps from 'a' (0) to 'h' (7).
    """
    if not isinstance(algebraic_notation_str, str) or len(algebraic_notation_str) != 2:
        # print(f"Invalid algebraic notation format: {algebraic_notation_str}")
        return None

    col_char = algebraic_notation_str[0].lower()
    row_char = algebraic_notation_str[1]

    if not ('a' <= col_char <= 'h' and '1' <= row_char <= '8'):
        # print(f"Invalid algebraic notation values: {algebraic_notation_str}")
        return None

    col = ord(col_char) - ord('a')
    row = 8 - int(row_char) # '8' becomes row 0, '1' becomes row 7

    return (row, col)

def coords_to_algebraic(coords_tuple):
    """
    Converts board coordinates (row, col) to algebraic notation (e.g., "e2").
    (0,0) is 'a8', (7,7) is 'h1'.
    """
    if not isinstance(coords_tuple, tuple) or len(coords_tuple) != 2:
        # print(f"Invalid coordinate format: {coords_tuple}")
        return None

    row, col = coords_tuple

    if not (0 <= row <= 7 and 0 <= col <= 7):
        # print(f"Invalid coordinate values: {coords_tuple}")
        return None

    col_char = chr(ord('a') + col)
    row_char = str(8 - row)

    return col_char + row_char

if __name__ == '__main__':
    # Test cases
    print("Testing algebraic_to_coords:")
    print(f"'a8' -> {algebraic_to_coords('a8')} (Expected: (0, 0))")
    print(f"'h1' -> {algebraic_to_coords('h1')} (Expected: (7, 7))")
    print(f"'e2' -> {algebraic_to_coords('e2')} (Expected: (6, 4))")
    print(f"'d4' -> {algebraic_to_coords('d4')} (Expected: (4, 3))")
    print(f"'A8' -> {algebraic_to_coords('A8')} (Expected: (0, 0))") # Case-insensitivity for column
    print(f"'H1' -> {algebraic_to_coords('H1')} (Expected: (7, 7))")
    print(f"'g5' -> {algebraic_to_coords('g5')} (Expected: (3, 6))")
    print(f"'b2' -> {algebraic_to_coords('b2')} (Expected: (6, 1))")

    print("\nTesting invalid algebraic_to_coords:")
    print(f"'a9' -> {algebraic_to_coords('a9')} (Expected: None)")
    print(f"'i1' -> {algebraic_to_coords('i1')} (Expected: None)")
    print(f"'e22' -> {algebraic_to_coords('e22')} (Expected: None)")
    print(f"'e' -> {algebraic_to_coords('e')} (Expected: None)")
    print(f"12 -> {algebraic_to_coords(12)} (Expected: None)")


    print("\nTesting coords_to_algebraic:")
    print(f"(0, 0) -> {coords_to_algebraic((0, 0))} (Expected: a8)")
    print(f"(7, 7) -> {coords_to_algebraic((7, 7))} (Expected: h1)")
    print(f"(6, 4) -> {coords_to_algebraic((6, 4))} (Expected: e2)")
    print(f"(4, 3) -> {coords_to_algebraic((4, 3))} (Expected: d4)")
    print(f"(3, 6) -> {coords_to_algebraic((3, 6))} (Expected: g5)")
    print(f"(6, 1) -> {coords_to_algebraic((6, 1))} (Expected: b2)")

    print("\nTesting invalid coords_to_algebraic:")
    print(f"(0, 8) -> {coords_to_algebraic((0, 8))} (Expected: None)")
    print(f"(-1, 0) -> {coords_to_algebraic((-1, 0))} (Expected: None)")
    print(f"('a', 'b') -> {coords_to_algebraic(('a', 'b'))} (Expected: None)")
    print(f"((1,2), (3,4)) -> {coords_to_algebraic(((1,2), (3,4)))} (Expected: None)")
