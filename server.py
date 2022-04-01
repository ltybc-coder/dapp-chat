import asyncio
import socket
from _thread import *

from handler import handle_requests


class Server:
    def __init__(self, hostname, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hostname = hostname
        self.port = port

    def start(self):
        asyncio.run(self.start_async())

    async def start_async(self):
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(10)

        while True:
            conn, address = self.socket.accept()
            data = conn.recv(4096).decode('utf-8')
            conn.close()
            if data == "":
                continue
            else:
                start_new_thread(handle_requests, (data, address))

