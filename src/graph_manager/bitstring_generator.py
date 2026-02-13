import hashlib
from zlib import crc32

class HashGenerator:
    @staticmethod
    def generate_bitstring(address:tuple[str, int]):
        b = hashlib.sha3_256((address[0] + str(address[1])).encode()).digest()
        bit_string = ""
        for bt in b:
            n = int(bt)
            for i in range(1, 9):
                r = n - 2**(8 - i)
                if r >= 0:
                    bit_string += "1"
                    n = n - 2**(8 - i)
                else:
                    bit_string += "0"
        return bit_string

    @staticmethod
    def generate_hash_value(address:tuple[str, int]):
        h = crc32((address[0] + str(address[1])).encode())
        return h / 2**32