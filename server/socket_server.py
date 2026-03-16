import socket
import threading
import random

PORT = 8000
SERVER = socket.gethostbyname(socket.gethostname())

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((SERVER, PORT))


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    msg = f"hello, your token no is {random.randint(1, 100)}"
    print(msg)
    conn.send(msg.encode())
    # conn.close()


def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(conn, addr), daemon=True
        )
        client_thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    print("starting socket server...")
    start()
