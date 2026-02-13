import time

from src.graph_manager.graph_manager import GraphManager

g2 =GraphManager(("127.0.0.1", 5001), 8, 256, 500)

while True:
    time.sleep(200)