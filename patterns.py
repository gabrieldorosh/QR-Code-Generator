
# draw finder pattern in top left corner
def add_finder_pattern(matrix: list, reserved: list, top: int, left: int):
    size = len(matrix)
    for r in range(-1, 8):
        for c in range(-1, 8):
            rr = top + r
            cc = left + c
            if 0 <= rr < size and 0 <= cc < size:
                if 0 <= r <= 6 and 0 <= c <= 6:
                    # finder pattern structure
                    if r in [0, 6] or c in [0, 6] or (2 <= r <= 4 and 2 <= c <= 4):
                        matrix[rr][cc] = 1  # black
                    else:
                        matrix[rr][cc] = 0  # white
                else:
                    # separator (white)
                    matrix[rr][cc] = 0
                reserved[rr][cc] = True


# add alignment patterns for v2
def add_alignment_patterns(matrix: list, reserved: list, version: int):
    size = len(matrix)
    if version < 2:
        return
    centers = [6, size - 7]
    for r in centers:
        for c in centers:
            # skip patterns overlapping finders at corners
            if (r <= 6 and c <= 6) or (r <= 6 and c >= size-7) or (r >= size-7 and c <= 6):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    rr = r + dr
                    cc = c + dc
                    if 0 <= rr < size and 0 <= cc < size:
                        if abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0):
                            matrix[rr][cc] = 1
                        else:
                            matrix[rr][cc] = 0
                        reserved[rr][cc] = True


# applies timing pattern after placing seperators
def add_timing_pattern(matrix: list, reserved: list):
    size = len(matrix)
    for i in range(8, size - 8):
        if not reserved[6][i]:
            matrix[6][i] = 1 if i % 2 == 0 else 0
            reserved[6][i] = True
        if not reserved[i][6]:
            matrix[i][6] = 1 if i % 2 == 0 else 0
            reserved[i][6] = True


# applies dark module after placing timing pattern
def add_dark_module(matrix: list, reserved: list, version: int):
    size = len(matrix)
    r = 8
    c = 4 * version + 9
    if 0 <= r < size and 0 <= c < size:
        matrix[r][c] = 1
        reserved[r][c] = True


# reserve area for format info
def reserve_format_info(reserved: list):
    size = len(reserved)
    for i in range(9):
        reserved[8][i] = True
        reserved[i][8] = True
    for i in range(8):
        reserved[8][size - 1 - i] = True
        reserved[size - 1 - i][8] = True