from patterns import (
    generate_pattern_matrix,
    get_finder_pattern_positions,
    get_alignment_pattern_positions,
    place_matrix_in_positions,
    add_separators,
    add_timing_pattern, 
    add_dark_module, 
    reserve_format_info
)

# create empty QR matrix for given version with function patterns
# calculates the size of qr code based on the version
def initialise_matrix(version: int) -> tuple[list[list[int]], list[list[bool]]]:
    if version == 1:
        size = 21
    elif version == 2:
        size = 25
    else:
        raise ValueError("Unsupported version")
    
    # create blank matrix and reserved
    matrix = [[None]*size for _ in range(size)]
    reserved = [[False]*size for _ in range(size)]

    # add finder patterns
    finder_pattern_matrix = generate_pattern_matrix(7, 3)
    finder_pattern_positions = get_finder_pattern_positions(size)
    matrix, reserved = place_matrix_in_positions(matrix, finder_pattern_matrix, finder_pattern_positions, reserved)
    

    # add alignment patterns (version 2)
    alignment_pattern_matrix = generate_pattern_matrix(5, 1)
    alignment_pattern_positions = get_alignment_pattern_positions(version, size)
    matrix, reserved = place_matrix_in_positions(matrix, alignment_pattern_matrix, alignment_pattern_positions, reserved)
    add_separators(matrix, reserved)

    # add timing patterns
    add_timing_pattern(matrix, reserved)

    # add dark module
    add_dark_module(matrix, reserved, version)

    # reserve format information areas
    reserve_format_info(reserved)

    return matrix, reserved


# applies data and ECC bits after all patterns and reservations applied
def place_data_bits(matrix: list[list[int]], reserved: list[list[bool]], bitstream: str):
    size = len(matrix)
    direction = -1
    col = size - 1
    bit_index = 0
    while col > 0:
        if col == 6:
            col -= 1  # skip vertical timing column
        for i in range(size):
            row = (size - 1 - i) if direction == -1 else i
            for c in [col, col - 1]:
                if 0 <= row < size and 0 <= c < size and not reserved[row][c]:
                    if bit_index < len(bitstream):
                        matrix[row][c] = int(bitstream[bit_index])
                        bit_index += 1
        col -= 2
        direction *= -1


# complete QR matrix with all function patterns and data bits
def create_full_matrix(version: int, data_bits: str, ecc_bits: str) -> tuple[list[list[int]], list[list[bool]]]:
    matrix, reserved = initialise_matrix(version)
    full_bits = data_bits + ecc_bits
    place_data_bits(matrix, reserved, full_bits)

    return matrix, reserved