from src.graph_manager.node import Node
from src.parsing.linearize import Linearize


class Range:
    def __init__(self, level:int, parent_hash:float, parent_bitstring:str, parent_address:tuple[str, int]):
        self.level = level
        self.connected_nodes = []
        self.borders_0 = (0,1)
        self.borders_1 = (0,1)
        self.border_nodes_0 = [None, None]
        self.border_nodes_1 = [None, None]
        self.parent = parent_hash
        self.parent_address = parent_address
        self.parent_bitstring = parent_bitstring

    @staticmethod
    def prevent_nil_border(node:Node, floor:bool) -> int:
        if node is None:
            if floor:
                return 0
            else:
                return 1
        else:
            return node.position

    def calculate_range_borders(self):
        self.borders_0 = (Range.prevent_nil_border(self.border_nodes_0[0], True), Range.prevent_nil_border(self.border_nodes_0[1], False))
        self.borders_1 = (Range.prevent_nil_border(self.border_nodes_1[0], True), Range.prevent_nil_border(self.border_nodes_1[1], False))

    def update_range(self, n:Node) -> list[Node]:
        dropped_list = []
        self.calculate_range_borders()
        if n.bitstring[0:self.level] != self.parent_bitstring[0:self.level]:
            dropped_list.append(n)
        elif n.position > self.borders_0[1] and n.position > self.borders_1[1] or n.position < self.borders_0[0] and n.position < self.borders_1[0]:
            dropped_list.append(n)
        elif n.position == self.parent:
            pass
        else:
            found = False
            for node in self.connected_nodes:
                if node.position == n.position:
                    found = True
            if not found:
                self.connected_nodes.append(n)
            if n.bitstring[self.level] == "0":
                if self.borders_0[0] < n.position < self.parent:
                    self.border_nodes_0[0] = n
                elif self.borders_0[1] > n.position > self.parent:
                    self.border_nodes_0[1] = n
            else:
                if self.borders_1[0] < n.position < self.parent:
                    self.border_nodes_1[0] = n
                elif self.borders_1[1] > n.position > self.parent:
                    self.border_nodes_1[1] = n
        for node in dropped_list:
            if node in self.connected_nodes:
                self.connected_nodes.remove(node)
        dropped_list.extend(self.cleanup_range())
        return dropped_list

    def range_borders(self):
        range_borders = []
        if min(self.prevent_nil_border(self.border_nodes_0[0], True), self.prevent_nil_border(self.border_nodes_1[0], True)) > 0:
            range_borders.append(min(self.prevent_nil_border(self.border_nodes_0[0], True), self.prevent_nil_border(self.border_nodes_1[0], True)))
        else:
            range_borders.append(0.0)
        if max(self.prevent_nil_border(self.border_nodes_0[1], False), self.prevent_nil_border(self.border_nodes_1[1], False)) < 1:
            range_borders.append(max(self.prevent_nil_border(self.border_nodes_0[1], False), self.prevent_nil_border(self.border_nodes_1[1], False)))
        else:
            range_borders.append(1.0)
        return range_borders

    def cleanup_range(self) -> list[Node]:
        self.connected_nodes = sorted(self.connected_nodes)
        i = 0
        dropped_list = []
        range_borders = self.range_borders()
        while -1 < i < len(self.connected_nodes):
            if self.connected_nodes[i].position >= range_borders[0]:
                break
            dropped_list.append(self.connected_nodes[i])
            i += 1
        i = len(self.connected_nodes) - 1
        while -1 < i < len(self.connected_nodes):
            if self.connected_nodes[i].position <= range_borders[1]:
                break
            dropped_list.append(self.connected_nodes[i])
            i -= 1
        for node in dropped_list:
            self.connected_nodes.remove(node)
        return dropped_list

    def linearize_range(self):
        self.connected_nodes = sorted(self.connected_nodes)
        passed_middle = False
        middle_upper = -1
        for i in range(len(self.connected_nodes)):
            if self.connected_nodes[i].position > self.parent and not passed_middle:
                middle_upper = i
                passed_middle = True
                self.connected_nodes[i].connection_handler.send_message(Linearize(self.parent_address).to_json())
                if i > 0:
                    self.connected_nodes[i-1].connection_handler.send_message(Linearize(self.parent_address).to_json())
            if i == 0:
                pass
            if i > 0:
                if not passed_middle:
                    self.connected_nodes[i - 1].connection_handler.send_message(
                        Linearize(self.connected_nodes[i].address).to_json())
                else:
                    self.connected_nodes[i].connection_handler.send_message(
                        Linearize(self.connected_nodes[i-1].address).to_json())
        if len(self.connected_nodes) > 0 and not passed_middle:
            self.connected_nodes[len(self.connected_nodes) - 1].connection_handler.send_message(
                Linearize(self.parent_address).to_json())
        if middle_upper != -1:
            for n in self.connected_nodes:
                if n.position < self.parent:
                    n.connection_handler.send_message(Linearize(self.connected_nodes[middle_upper].address).to_json())
                elif middle_upper > 0:
                    n.connection_handler.send_message(Linearize(self.connected_nodes[middle_upper - 1].address).to_json())
        if self.border_nodes_0[0] is not None and self.border_nodes_1[1] is not None:
            self.border_nodes_0[0].connection_handler.send_message(Linearize(self.border_nodes_1[1].address).to_json())
            self.border_nodes_1[1].connection_handler.send_message(Linearize(self.border_nodes_0[0].address).to_json())
        if self.border_nodes_0[1] is not None and self.border_nodes_1[0] is not None:
            self.border_nodes_0[1].connection_handler.send_message(Linearize(self.border_nodes_1[0].address).to_json())
            self.border_nodes_1[0].connection_handler.send_message(Linearize(self.border_nodes_0[1].address).to_json())

    def delete_node_from_range(self, address:tuple[str, int]):
        for n in self.connected_nodes:
            if n.address == address:
                self.connected_nodes.remove(n)
        if self.border_nodes_0[0] is not None:
            if address == self.border_nodes_0[0].address:
                self.border_nodes_0[0] = None
        elif self.border_nodes_0[1] is not None:
            if address == self.border_nodes_0[1].address:
                self.border_nodes_0[1] = None
        elif self.border_nodes_1[0] is not None:
            if address == self.border_nodes_1[0].address:
                self.border_nodes_1[0] = None
        elif self.border_nodes_1[1] is not None:
            if address == self.border_nodes_1[1].address:
                self.border_nodes_1[1] = None

    def print_range(self):
        print("-------------------------------------------------------------------------------------------------------")
        print(self.level)
        print("Range borders 0: " + str(self.borders_0))
        print("Range borders 1: " + str(self.borders_1))
        print("Total borders: " + str(self.range_borders()))
        print("Border nodes 0: " + str([(n.position, n.bitstring[0:2]) for n in self.border_nodes_0 if n is not None]))
        print("Border nodes 1: " + str([(n.position, n.bitstring[0:2]) for n in self.border_nodes_1 if n is not None]))
        print([n.address for n in self.connected_nodes])
        print("-------------------------------------------------------------------------------------------------------")