#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from collections import deque


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")

                for user in self.server.clients:
                    if login == user.login:
                        self.transport.write(
                            f"Логин {login} занят, попробуйте другой\n".encode()
                        )
                        return
                self.login = login

                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )
                self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        self.add_history(message)
        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for text in list(self.server.messages):
            self.transport.write(
                    text.encode()
            )

    def add_history(self, message):
        self.server.messages.append(message)


class Server:
    clients: list
    messages: deque

    def __init__(self):
        self.clients = []
        self.messages = deque('', 10)

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
