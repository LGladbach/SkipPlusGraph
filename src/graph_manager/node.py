from src.graph_manager.bitstring_generator import HashGenerator
from src.server_structure.connection_handler import ConnectionHandler


class Node:
    def __init__(self, address:tuple[str, int], connection_handler:ConnectionHandler):
        self.address = address
        self.bitstring = HashGenerator.generate_bitstring(address)
        self.position = HashGenerator.generate_hash_value(address)
        self.connection_handler = connection_handler

    def __le__(self, other):
        return self.position <= other.position

    def __lt__(self, other):
        return self.position < other.position

    def __ge__(self, other):
        return self.position >= other.position

    def __gt__(self, other):
        return self.position > other.position

    @staticmethod
    def node_distance(node0, node1) -> float:
        return abs(node0.position - node1.position)

    @staticmethod
    def fit_level(node0, node1) -> int: #max index where it fits + 1
        i = 0
        while i < len(node0.bitstring):
            if node0.bitstring[i] != node1.bitstring[i]:
                break
            i += 1
        return i