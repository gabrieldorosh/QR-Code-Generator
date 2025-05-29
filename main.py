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
#   --version: 1 or 2, default is 1
#   --output: The output file name, default is 'qr.png'

import argparse

from encoding import generate_codewords
from matrix import initialise_matrix, place_data_bits
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
    parser = argparse.ArgumentParser(description="Generate QR codes with optional slideshow and customisation.")
    parser.add_argument("text", help="Text to encode (byte mode).")
    parser.add_argument("--version", "-v", type=int, choices=[1, 2], default=None, 
                        help="QR code version (auto if not set).")
    parser.add_argument("--output", "-o", default="qr_output.png",
                        help="Output PNG file name.")
    parser.add_argument("--foreground", "-fg", default="#000000",
                        help="Foreground colour in hex")
    parser.add_argument("--background", "-bg", default="#ffffff",
                        help="Background colour in hex")
    parser.add_argument("--shape", "-s", choices=["square", "circle"], default="square",
                        help="Module shape (square or circle).")
    parser.add_argument("--pixel", "-p", type=int, default=10,
                        help="Pixel size.")
    parser.add_argument("--slideshow", "-sl", action="store_true",
                        help="Show step by step slideshow of QR code generation.")
    args = parser.parse_args()

    raw = args.text.encode('iso-8859-1', 'strict')
    if args.version is None:
        # auto detect version based on input length
        if len(raw) <= 19:
            version = 1
        elif len(raw) <= 34:
            version = 2
        else:
            raise ValueError("Input too long (max 34 bytes for version 2).")
    else:
        version = args.version

    # generate data and ECC codewords
    data_codewords, ecc_codewords = generate_codewords(args.text, version)
    bits = ''.join(format(b, '08b') for b in data_codewords + ecc_codewords)

    matrix, reserved = initialise_matrix(version)
    if args.slideshow:
        save_matrix_as_image(matrix, f"step0_patterns.png", args.pixel)
    place_data_bits(matrix, reserved, bits)
    if args.slideshow:
        save_matrix_as_image(matrix, f"step1_data_bits,png", args.pixel)

    best = min(
        ((mask, apply_mask(matrix, reserved, mask), calculate_penalty(apply_mask(matrix, reserved, mask)))
         for mask in range(8)), key=lambda x: x[2]
    )
    mask, matrix, _ = best
    if args.slideshow:
        save_matrix_as_image(matrix, f"step2_mask_{mask}.png", args.pixel)

    fmt = get_format_info_bits('L', mask)
    fmt_positions = [(8, i) for i in range(6)] + [(8, 7), (8, 8), (7, 8)] + [(i, 8) for i in range(5, -1, -1)]
    for idx, (r, c) in enumerate(fmt_positions):
        matrix[r][c] = int(fmt[idx])
    if args.slideshow:
        save_matrix_as_image(matrix, f"step3_format.png", args.pixel)

    save_matrix_as_image(matrix, args.output, args.pixel)
    print(f"QR code saved to {args.output} (version {version}, mask {mask}).")
