# applies inversion if condition met, applies mask to qr matrix and returns new matrix
def apply_mask(matrix: list[list[int]], reserved: list[list[bool]], mask_pattern: int) -> list[list[int]]:
    size = len(matrix)
    masked = [row.copy() for row in matrix]
    for r in range(size):
        for c in range(size):
            if not reserved[r][c] and masked[r][c] is not None:
                apply = False
                if   mask_pattern == 0: apply = (r + c) % 2 == 0
                elif mask_pattern == 1: apply =  (r % 2) == 0
                elif mask_pattern == 2: apply =  (c % 3) == 0
                elif mask_pattern == 3: apply = ((r + c) % 3) == 0
                elif mask_pattern == 4: apply = ((r//2 + c//3) % 2) == 0
                elif mask_pattern == 5: apply = ((r*c) % 2 + (r*c) % 3) == 0
                elif mask_pattern == 6: apply = (((r*c) % 2 + (r*c) % 3) % 2) == 0
                elif mask_pattern == 7: apply = (((r + c) % 2 + (r*c) % 3) % 2) == 0
                if apply:
                    masked[r][c] = 1 - masked[r][c]

    return masked


# calculates the score for each mask rule
# count consecutive modules in rows and columns of the same colour
def penalty_rule1(matrix: list[list[int]]) -> int:
    size = len(matrix)
    penalty = 0

    # rows
    for r in range(size):
        run_color = matrix[r][0]
        run_length = 1
        for c in range(1, size):
            if matrix[r][c] == run_color:
                run_length += 1
            else:
                if run_length >= 5:
                    penalty += 3 + (run_length - 5)
                run_color = matrix[r][c]
                run_length = 1
        if run_length >= 5:
            penalty += 3 + (run_length - 5)

    # columns
    for c in range(size):
        run_color = matrix[0][c]
        run_length = 1
        for r in range(1, size):
            if matrix[r][c] == run_color:
                run_length += 1
            else:
                if run_length >= 5:
                    penalty += 3 + (run_length - 5)
                run_color = matrix[r][c]
                run_length = 1
        if run_length >= 5:
            penalty += 3 + (run_length - 5)

    return penalty


# count 2x2 blocks of the same colour, apply 3 penalty for each block
def penalty_rule2(matrix: list[list[int]]) -> int:
    size = len(matrix)
    penalty = 0
    for r in range(size - 1):
        for c in range(size - 1):
            v = matrix[r][c]
            if matrix[r][c+1] == v and matrix[r+1][c] == v and matrix[r+1][c+1] == v:
                penalty += 3

    return penalty


# find patterns in rows and columns, apply 40 penalty for each match
def penalty_rule3(matrix: list[list[int]]) -> int:
    size = len(matrix)
    penalty = 0
    pattern = [1,0,1,1,1,0,1]

    # rows
    for r in range(size):
        for c in range(size - 6):
            if [matrix[r][c+i] for i in range(7)] == pattern:
                # Check 4 light modules before
                if c >= 4 and all(matrix[r][c-1-i] == 0 for i in range(4)):
                    penalty += 40
                # Check 4 light modules after
                if c + 7 <= size - 4 and all(matrix[r][c+7+i] == 0 for i in range(4)):
                    penalty += 40

    # columns
    for c in range(size):
        for r in range(size - 6):
            if [matrix[r+i][c] for i in range(7)] == pattern:
                if r >= 4 and all(matrix[r-1-i][c] == 0 for i in range(4)):
                    penalty += 40
                if r + 7 <= size - 4 and all(matrix[r+7+i][c] == 0 for i in range(4)):
                    penalty += 40

    return penalty


# penalty for deviation from 50% black modules, apply 10 points for each 5% away
def penalty_rule4(matrix: list[list[int]]) -> int:
    size = len(matrix)
    total = size * size
    dark = sum(1 for r in matrix for v in r if v == 1)
    percent = (dark * 100) / total
    prev = int(percent/5) * 5
    next = prev + 5
    diff = min(abs(prev - 50), abs(next - 50))

    return (diff // 5) * 10


# calculate total mask penalty 
def calculate_penalty(matrix: list[list[int]]) -> int:

    return (penalty_rule1(matrix) +
            penalty_rule2(matrix) +
            penalty_rule3(matrix) +
            penalty_rule4(matrix))