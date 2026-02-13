import time
import socket

from src.graph_manager.node import Node
from src.server_structure.connection_handler import ConnectionHandler
for i in range(1000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 5000))
    Node(("127.0.0.1", 5000), ConnectionHandler(s, ("127.0.0.1", 5000), 256))

while True:
    time.sleep(100)