import reedsolo

# encode input string into bit string for given version.
def encode_bytes(data: str, version: int) -> str:
    mode_indicator = '0100'

    # character count
    char_count_bits = format(len(data), '08b')
    byte_data = data.encode('iso-8859-1', 'strict')
    data_bits = ''.join(format(b, '08b') for b in byte_data)

    return mode_indicator + char_count_bits + data_bits


# add terminator and padding to make length a multiple of 8, and fill capacity
def add_terminator_and_padding(bit_string: str, version: int) -> str:
    # data capacity. v1=19, v2=34
    data_codewords = {1: 19, 2: 34}.get(version)
    if data_codewords is None:
        raise ValueError("Unsupported version")
    data_capacity = data_codewords * 8

    # terminator
    terminator_len = min(4, data_capacity - len(bit_string))
    bit_string += '0' * terminator_len

    # pad to byte boundary
    while len(bit_string) % 8 != 0:
        bit_string += '0'

    # pad bytes 0xEC, 0x11 alternating
    pad_bytes = ['11101100', '00010001']
    i = 0
    while len(bit_string) < data_capacity:
        bit_string += pad_bytes[i % 2]
        i += 1

    return bit_string


# convert bit string into a list of integer byte values
def bits_to_bytes(bit_string: str) -> list[int]:

    return [int(bit_string[i:i+8], 2) for i in range(0, len(bit_string), 8)]


# get message coefficients and generate error correction codewords
def generate_codewords(data: str, version: int) -> tuple[list[int], list[int]]:
    bit_stream = encode_bytes(data, version)
    padded = add_terminator_and_padding(bit_stream, version)
    data_bytes = bits_to_bytes(padded)

    # ECC codeword count v1=7, v2=10
    ecc_count = {1: 7, 2: 10}.get(version)
    if ecc_count is None:
        raise ValueError("Unsupported version")
    rs = reedsolo.RSCodec(ecc_count)
    full = list(rs.encode(bytearray(data_bytes)))
    data_codewords = full[:-ecc_count]
    ecc_codewords = full[-ecc_count:]

    return data_codewords, ecc_codewords