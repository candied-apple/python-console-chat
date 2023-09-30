import socket
import threading
import sqlite3
from datetime import datetime
import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init()

# Constants for colors
RESET = Style.RESET_ALL
BG_RED = Back.RED
BG_GREEN = Back.GREEN
BLUE = Fore.BLUE
RED = Fore.RED
BRIGHT_BLACK = Fore.BLACK + Style.BRIGHT


# Get the current time and date
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
MESSAGE_HISTORY_FILE = "message_history.txt"

# Function to register a new user
def register_user(username, password, cursor, conn):
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()

# Function to authenticate a user
def authenticate_user(username, password, cursor):
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    return cursor.fetchone() is not None

# Function to broadcast a message to all clients
def broadcast_message(message, clients):
    for client in clients:
        try:
            client.sendall(message.encode('utf-8'))
        except:
            # Remove the client if the send fails
            clients.remove(client)

# Function to handle a client's requests
def handle_client(client_socket, clients, username):
    try:
        # Notify user joined
        join_message = f'{current_time} {BLUE}{username} joined the chat.{RESET}'
        broadcast_message(join_message, clients)

        while True:
            # Receive data from the client
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                # Broadcast the message to all clients with time and date prefix
                message_to_broadcast = f'{current_time} {BRIGHT_BLACK}{username}{RESET} : {data}{RESET}'
                broadcast_message(message_to_broadcast, clients)
                save_to_history(message_to_broadcast)  # Save to chat history
            except ConnectionResetError:
                break

    finally:
        # Notify user left
        leave_message = f'{current_time} {RED}{username} left the chat.{RESET}'
        broadcast_message(leave_message, clients)

        # Remove the client from the list if it's still there
        if client_socket in clients:
            clients.remove(client_socket)

        client_socket.close()

# Function to save message to history file
def save_to_history(message):
    with open(MESSAGE_HISTORY_FILE, 'a', encoding='utf-8') as history_file:
        history_file.write(message + '\n')

# Main server function
def main():
    server_host = '127.0.0.1'
    server_port = 8080

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)
    print(f'Server listening on {server_host}:{server_port}')

    clients = []  # List to hold client sockets

    while True:
        client_socket, addr = server_socket.accept()
        print(f'Accepted connection from {addr[0]}:{addr[1]}')

        # Perform authentication
        authenticated = False
        username = None

        try:
            username = client_socket.recv(1024).decode('utf-8')
        except ConnectionAbortedError:
            print(f'Connection aborted by {addr[0]}:{addr[1]}')
            continue

        try:
            password = client_socket.recv(1024).decode('utf-8')
        except ConnectionAbortedError:
            print(f'Connection aborted by {addr[0]}:{addr[1]}')
            continue

        authenticated = authenticate_user(username, password, cursor)
        if not authenticated:
            client_socket.sendall(f'{BG_RED}Authentication failed. Please try again.{RESET}'.encode('utf-8'))
            continue

        print(f'User {username} authenticated.')

        # Send authentication success message after sending chat history
        client_socket.sendall(f'{BG_GREEN}Authentication successful.{RESET}'.encode('utf-8'))

        # Send chat history to the client line by line
        with open(MESSAGE_HISTORY_FILE, 'r', encoding='utf-8') as history_file:
            for line in history_file:
                client_socket.sendall(line.encode('utf-8'))

        clients.append(client_socket)

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, clients, username))
        client_thread.start()

if __name__ == '__main__':
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    main()
