# draw border around each finder
def add_separators(matrix: list[list[int]], reserved: list[list[bool]]):
    size = len(matrix)
    from patterns import get_finder_pattern_positions
    for row, col in get_finder_pattern_positions(size):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                r, c = row + dr, col + dc
                if 0 <= r < size and 0 <= c < size and not reserved[r][c]:
                    if dr in (-1, 7) or dc in (-1, 7):
                        matrix[r][c] = 0
                        reserved[r][c] = True

# build a square pattern matrix
def generate_pattern_matrix(outer_size: int, inner_size: int) -> list[list[int]]:
    # init with 0s
    m = [[0] * outer_size for _ in range(outer_size)]
    # outer
    for i in range(outer_size):
        m[0][i] = 1
        m[outer_size - 1][i] = 1
        m[i][0] = 1
        m[i][outer_size - 1] = 1
    # inner
    start = (outer_size - inner_size) // 2
    end = start + inner_size
    for i in range(start, end):
        for j in range(start, end):
            m[i][j] = 1
    return m


# top left corners
def get_finder_pattern_positions(size: int) -> list[tuple[int,int]]:

    return [(0,0), (0, size - 7), (size - 7, 0)]


# return top left corners 5x5
def get_alignment_pattern_positions(version: int, size: int) -> list[tuple[int,int]]: 
    if version < 2:
        return []
    coords = [6, size - 7]
    positions = []
    for r in coords:
        for c in coords:
            if (r == 6 and c == 6) or (r == 6 and c == size-7) or (r == size-7 and c == 6):
                continue
            positions.append((r - 2, c - 2))
    return positions


# place small into big at each row/col in positions and marking as reserved
def place_matrix_in_positions(
        big: list[list[int]],
        small: list[list[int]],
        positions: list[tuple[int, int]],
        reserved: list[list[bool]]
) -> tuple[list[list[int]], list[list[bool]]]:
    bh, bw = len(big), len(big[0])
    sh, sw = len(small), len(small[0])
    for (r, c) in positions:
        if r+sh > bh or c+sw > bw:
            continue
        for dr in range(sh):
            for dc in range(sw):
                if not reserved[r+dr][c+dc]:
                    big[r+dr][c+dc] = small[dr][dc]
                    reserved[r+dr][c+dc] = True

    return big, reserved


# applies timing pattern after placing seperators
def add_timing_pattern(matrix: list[list[int]], reserved: list[list[bool]]):
    size = len(matrix)
    for i in range(8, size - 8):
        if not reserved[6][i]:
            matrix[6][i] = 1 if i % 2 == 0 else 0
            reserved[6][i] = True
        if not reserved[i][6]:
            matrix[i][6] = 1 if i % 2 == 0 else 0
            reserved[i][6] = True


# applies dark module after placing timing pattern
def add_dark_module(matrix: list[list[int]], reserved: list[list[bool]], version: int):
    size = len(matrix)
    r = 8
    c = 4 * version + 9
    if 0 <= r < size and 0 <= c < size:
        matrix[r][c] = 1
        reserved[r][c] = True


# reserve area for format info
def reserve_format_info(reserved: list[list[bool]]):
    size = len(reserved)
    for i in range(9):
        reserved[8][i] = True
        reserved[i][8] = True
    for i in range(8):
        reserved[8][size - 1 - i] = True
        reserved[size - 1 - i][8] = True