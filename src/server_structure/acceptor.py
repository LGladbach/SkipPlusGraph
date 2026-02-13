import socket
import threading

from src.graph_manager.node import Node
from src.server_structure.connection_handler import ConnectionHandler


class Acceptor:
    def __init__(self, address:tuple[str, int], max_package_size:int):
        self.address = address
        self.max_package_size = max(max_package_size, 128)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.new_clients_lock = threading.Lock()
        self.new_clients = []
        self.run_thread = threading.Thread(target=self.run)
        self.run_thread.start()

    def run(self):
        self.server_socket.bind(self.address)
        self.server_socket.listen()
        while True:
            try:
                client, address = self.server_socket.accept()
                self.new_clients_lock.acquire()
                self.new_clients.append(Node(address, ConnectionHandler(client, address, self.max_package_size)))
                self.new_clients_lock.release()
            except Exception:
                pass

    def get_new_clients(self) -> Node:
        client = None
        self.new_clients_lock.acquire()
        if len(self.new_clients) > 0:
            client  = self.new_clients.pop(0)
        self.new_clients_lock.release()
        return client

    def close(self):
        self.server_socket.close()