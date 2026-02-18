import socket
import threading
import time

from src.graph_manager.bitstring_generator import HashGenerator
from src.graph_manager.node import Node
from src.graph_manager.range import Range
from src.parsing.linearize import Linearize
from src.parsing.parser import Parser
from src.server_structure.acceptor import Acceptor
from src.server_structure.connection_handler import ConnectionHandler


class GraphManager:
    package_received_event = threading.Event()
    def __init__(self, address:tuple[str, int], depth:int, max_package_size:int, timeout:int):
        self.acceptor = Acceptor(address, max_package_size)
        self.bitstring = HashGenerator.generate_bitstring(address)
        self.hash_value = HashGenerator.generate_hash_value(address)
        self.address = address
        print(self.bitstring)
        print(self.hash_value)
        self.depth = min(depth, 128)
        self.timeout_time = timeout
        self.waiting_for_address = []
        self.contact_nodes = []
        self.contact_nodes_lock = threading.Lock()
        self.ranges = [Range(i, self.hash_value, self.bitstring, self.address) for i in range(self.depth)]
        self.connected_nodes = {} #dict of nodes in range with count of ranges
        self.packages_received_lock = threading.Lock()
        self.packages_received = []
        self.handle_nodes_lock = threading.Lock()
        self.handle_nodes_thread = threading.Thread(target=self.handle_nodes)
        self.handle_nodes_thread.start()
        self.timeout_thread = threading.Thread(target=self.timeout)
        self.timeout_thread.start()

    def join(self, address:tuple[str, int]):
        self.handle_nodes_lock.acquire()
        self.update_ranges(Linearize(address))
        self.handle_nodes_lock.release()

    def timeout(self):
        while True:
            time.sleep(self.timeout_time * 0.001)
            self.handle_nodes_lock.acquire()
            n = self.acceptor.get_new_clients()
            while n is not None:
                self.waiting_for_address.append(n)
                n = self.acceptor.get_new_clients()
            remove_waiting_list = []
            for n in self.waiting_for_address:
                messages_from_node = n.connection_handler.get_messages()
                if len(messages_from_node) > 0:
                    for m in messages_from_node:
                        pkg = Parser.parse_package(m)
                        if pkg.package_type == "linearize":
                            self.update_ranges(pkg)
                            remove_waiting_list.append(n)
                            break
            self.contact_nodes_lock.acquire()
            for n in remove_waiting_list:
                self.contact_nodes.append(n)
                self.waiting_for_address.remove(n)
            self.contact_nodes_lock.release()
            delete_list = []
            for n in self.connected_nodes.values():
                if n[0].connection_handler is not None:
                    if n[0].connection_handler.failed_event:
                        delete_list.append(n[0].address)
                else:
                    delete_list.append(n[0].address)
            for a in delete_list:
                self.handle_node_failure(a)
            for r in self.ranges:
                r.linearize_range()
            self.handle_nodes_lock.release()
            for r in self.ranges:
                r.print_range()

    def handle_node_failure(self, address:tuple[str, int]):
        for r in self.ranges:
            r.delete_node_from_range(address)
        del self.connected_nodes[address]

    def get_node_from_address(self, address:tuple[str, int]) -> (Node, bool):
        n = self.connected_nodes.get(address, None)
        found = False
        if n is not None:
            n = n[0]
            found = True
        else:
            n = self.contact(Linearize(address))
        return n, found

    def contact(self, linearize_package:Linearize) -> Node:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(linearize_package.address)
            n = Node(linearize_package.address, ConnectionHandler(s, linearize_package.address, self.acceptor.max_package_size))
            n.connection_handler.send_message(Linearize(self.address).to_json())
            return n
        except Exception:
            print("Failed to connect to node")
            return Node(linearize_package.address, None)

    def update_ranges(self, linearize_package:Linearize):
        node, found = self.get_node_from_address(linearize_package.address)
        if node is not None:
            if not found:
                self.connected_nodes[node.address] = [node, self.depth]
            else:
                node, _ = self.connected_nodes[node.address]
                self.connected_nodes[node.address][1] = self.depth
            dropped_nodes = []
            for level_range in self.ranges:
                dropped_nodes.extend(level_range.update_range(node))
            for n in dropped_nodes:
                self.connected_nodes[n.address][1] -= 1
                if self.connected_nodes[n.address][1] == 0:
                    self.get_best_fit_next(n).connection_handler.send_message(Linearize(n.address).to_json())
                    del self.connected_nodes[n.address] #Possible source of dictionary size changes during iteration for future problems!!!

    def handle_nodes(self):
        while True:
            ConnectionHandler.received_message_event.wait()
            self.handle_nodes_lock.acquire()
            self.contact_nodes_lock.acquire()
            msgs = []
            for n in self.connected_nodes.values():
                msgs.extend(n[0].connection_handler.get_messages())
            for n in self.contact_nodes:
                msgs.extend(n.connection_handler.get_messages())
            if len(msgs) > 0:
                for msg in msgs:
                    package = Parser.parse_package(msg)
                    if package.package_type == "linearize":
                        self.update_ranges(package)
                    elif package.package_type != "none":
                        self.packages_received_lock.acquire()
                        self.packages_received.append(package)
                        self.packages_received_lock.release()
            ConnectionHandler.received_message_event.clear()
            self.handle_nodes_lock.release()
            self.contact_nodes_lock.release()

    def get_received_package(self):
        self.packages_received_lock.acquire()
        package = self.packages_received.pop(0)
        self.packages_received_lock.release()
        return package

    def get_best_fit_next(self, node:Node) -> Node:
        best_fit_bitstring = -1
        current_distance = 1
        result = None
        for n in self.connected_nodes.values():
            if Node.fit_level(node, n[0]) - 1 > best_fit_bitstring:
                result = n[0]
                best_fit_bitstring = Node.fit_level(node, n[0])
                current_distance = Node.node_distance(node, n[0])
            elif current_distance > Node.node_distance(node, n[0]) and Node.fit_level(node, n[0]) - 1 == best_fit_bitstring:
                result = n[0]
                best_fit_bitstring = Node.fit_level(node, n[0])
                current_distance = Node.node_distance(node, n[0])
        return result

    def linearize_ranges(self):
        for r in self.ranges:
            r.linearize_range()