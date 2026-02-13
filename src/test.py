import time

from src.graph_manager.graph_manager import GraphManager

g1 = GraphManager(("127.0.0.1", 5000), 8, 256, 500)
g1.join(("127.0.0.1", 5001))
while True:
    time.sleep(200)