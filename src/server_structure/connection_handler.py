import math
import threading

from src.parsing.package_number import PackageNumber
from src.parsing.parser import Parser


class ConnectionHandler:
    received_message_event = threading.Event()

    def __init__(self, com_socket, address, max_package_size:int):
        self.com_socket = com_socket
        self.address = address
        self.max_package_size = max_package_size
        self.send_message_lock = threading.Lock()
        self.receive_message_lock = threading.Lock()
        self.pending_messages_in = []
        self.pending_messages_out = []
        self.handle_receive_thread = threading.Thread(target=self.handle_socket)
        self.handle_receive_thread.start()
        self.failed_event = False
        self.send_message_event = threading.Event()
        self.handle_send_thread = threading.Thread(target=self.handle_send)
        self.handle_send_thread.start()

    def send_message(self, msg:str):
        self.send_message_lock.acquire()
        shard_message = self.shard(msg)
        self.pending_messages_in.extend(shard_message)
        self.send_message_event.set()
        self.send_message_lock.release()

    def handle_socket(self):
        recv_buffer = []
        wait_packages = 0
        try:
            while True:
                data = self.com_socket.recv(self.max_package_size)
                if wait_packages == 0:
                    parsed = Parser.parse_package(data)
                    if parsed.package_type == "package_number":
                        wait_packages = parsed.number_of_packages
                    if len(recv_buffer) > 0:
                        msg = ConnectionHandler.glue(recv_buffer)
                        recv_buffer.clear()
                        self.receive_message_lock.acquire()
                        self.pending_messages_out.append(msg)
                        self.receive_message_lock.release()
                        ConnectionHandler.received_message_event.set()
                else:
                    recv_buffer.append(data)
                    wait_packages -= 1
        except Exception:
            print(str(self.address) + " connection failed.")
            self.failed_event = True

    def handle_send(self):
        try:
            while True:
                self.send_message_event.wait()
                self.send_message_lock.acquire()
                for msg in self.pending_messages_in:
                    self.com_socket.send(msg)
                self.pending_messages_in.clear()
                self.send_message_lock.release()
                self.send_message_event.clear()
        except Exception:
            print(str(self.address) + " connection failed.")
            self.failed_event = True

    def get_messages(self):
        self.receive_message_lock.acquire()
        msgs = self.pending_messages_out.copy()
        self.pending_messages_out.clear()
        self.receive_message_lock.release()
        return msgs

    @staticmethod
    def glue(sharded_message:list[bytes]):
        msg = ""
        for smp in sharded_message:
            msg += smp.decode()
        return msg

    def shard(self, msg:str) -> list[bytes]:
        msg_encoded = msg.encode()
        num_packages = math.ceil(len(msg_encoded) / self.max_package_size)
        pn = PackageNumber(num_packages)
        package_list = [pn.to_json().encode()]
        package_list.extend(
            [msg_encoded[i * self.max_package_size:(i + 1) * self.max_package_size] for i in range(num_packages)])
        return package_list