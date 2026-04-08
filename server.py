import socket
import threading

clients = []


def handle_client(conn, addr):
    print(f"[SERWER] Nowy gracz połączył się z adresu: {addr}")
    clients.append(conn)

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            for c in clients:
                if c != conn:
                    c.sendall(data)
        except:
            break

    print(f"[SERWER] Gracz rozłączył się: {addr}")
    clients.remove(conn)
    conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 5555))
    server.listen()
    print("[SERWER] Serwer TCP uruchomiony. Oczekuje na graczy na porcie 5555...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    start_server()