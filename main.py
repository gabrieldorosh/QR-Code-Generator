# README:
# Modular QR Code Generator V1-L and V2-L
#
# This generates QR codes from a given text input. 
#
# version 1-L QR code - Byte Mode           = Binary
#                     - Byte mode indicator = '0100'
#                     - Data bit capacity   = 19*8 = 152
#                     - QR code size        = 21*21 modules
#
# version 2-L         - Byte Mode           = Binary
#                     - Byte mode indicator = ''
#                     - Data bit capacity   = 34*8 = 272
#                     - QR code size        = 25*25 modules
#
# Usage:
#   python main.py "text" --version 1 --output qr.png
#
# Arguments:
#   text: The text to put in the QR code.
#   --version: 1 or 2, default is 2
#   --output: The output file name, default is 'qr.png'

import argparse

from encoding import generate_codewords
from matrix import create_full_matrix
from masking import apply_mask, calculate_penalty
from image_utils import save_matrix_as_image

# calculates the format information bit string
def get_format_info_bits(ec_level: str, mask_pattern: int) -> str:
    """
    Calculates the format information bit string based on the error correction level and mask pattern.

    Args:
        ec_level: L, M, Q, or H
        mask_pattern: 0 to 7

    Returns:
        A 15-bit string representing the format information.
    """
    # EC level bits
    ec_bits_map = {'L': 0b01, 'M': 0b00, 'Q': 0b11, 'H': 0b10}
    if ec_level not in ec_bits_map:
        raise ValueError(f"Invalid error correction level: {ec_level}. Must be L, M, Q, or H.")
    ec_bits = ec_bits_map[ec_level]

    # Combine EC bits and mask bits
    fmt = (ec_bits << 3) | mask_pattern

    poly = 0b10100110111  # Polynomial for format info
    data = fmt << 10
    # Polynomial division to calculate remainder
    for i in range(14, 9, -1):
        if (data >> i) & 1:
            data ^= (poly << (i - 10))

    # Append remainder and fixed mask 0b101010000010010
    format_info = ((fmt << 10) | data) ^ 0b101010000010010

    return format(format_info, '015b')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Version 1-L or 2-L QR code.")
    parser.add_argument("text", help="Text to encode (byte mode).")
    parser.add_argument("--version", type=int, choices=[1, 2], default=1, 
                        help="QR code version (1 or 2).")
    parser.add_argument("--output", "-o", default="qr_output.png",
                        help="Output PNG file name.")
    args = parser.parse_args()

    data = args.text
    version = args.version
    output_file = args.output

    # generate data and ECC codewords
    data_codewords, ecc_codewords = generate_codewords(data, version)

    # convert codewords to bit strings
    data_bits = ''.join(format(b, '08b') for b in data_codewords)
    ecc_bits = ''.join(format(b, '08b') for b in ecc_codewords)

    # build the base QR matrix and place data bits
    base_matrix, reserved = create_full_matrix(version, data_bits, ecc_bits)

    # try all masks and pick the lowest penalty
    best_mask = 0
    best_matrix = None
    lowest_penalty = float('inf')
    for mask in range(8):
        masked_matrix = apply_mask(base_matrix, reserved, mask)
        penalty = calculate_penalty(masked_matrix)
        if penalty < lowest_penalty:
            lowest_penalty = penalty
            best_mask = mask
            best_matrix = masked_matrix

    # place format information for the chosen mask
    format_bits = get_format_info_bits('L', best_mask)

    #map format bits to matrix positions
    fmt_positions = [(8, i) for i in range(6)] + [(8, 7), (8, 8), (7, 8)] + [(i, 8) for i in range(5, -1, -1)]
    for idx, (r, c) in enumerate(fmt_positions):
        best_matrix[r][c] = int(format_bits[idx])

    # save the final QR code image
    save_matrix_as_image(best_matrix, output_file)
    print(f"QR code saved to {output_file} (version {version}, mask {best_mask}).")