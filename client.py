import socket
import threading
import os
import signal
import time
import getpass
import ctypes
import colorama
from colorama import Fore, Back, Style
import platform
import sts
# Initialize colorama
colorama.init()

# Constants for colors
RESET = Style.RESET_ALL
BG_YELLOW = Back.YELLOW
BG_GREEN = Back.GREEN
BG_RED = Back.RED



# Function to set the console title
def set_console_title(title):
    if platform.system() == 'Windows':
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    elif platform.system() == 'Linux' or platform.system() == 'Darwin':  # 'Darwin' for macOS
        sys.stdout.write("\x1b]2;{}\x07".format(title))
    else:
        print(f"Unsupported operating system: {platform.system()}")


# Function to register a new user
# Function to register a new user
def register_user(client_socket):
    username = input('Enter your username: ')
    password = getpass.getpass('Enter your password: ')

    client_socket.sendall(username.encode('utf-8'))
    client_socket.sendall(password.encode('utf-8'))

    response = client_socket.recv(1024).decode('utf-8')
    print(f'{BG_YELLOW}Server:{RESET}', response)

    if response == f'{BG_RED}Authentication failed. Please try again.{RESET}':
        print('Exiting.')
        client_socket.close()
        exit()
    elif response != f'{BG_GREEN}Authentication successful.{RESET}':
        print(f'Unexpected response from the server: {response}. Exiting.')
        client_socket.close()
        exit()


# Function to receive messages from the server
def receive_messages(client_socket):
    try:
        while True:
            # Receive and display messages from the server
            message = client_socket.recv(1024).decode('utf-8')
            print(message)
    except ConnectionResetError:
        print(f'{BG_RED}Server Closed.{RESET}')
        client_socket.close()
        exit()

# Function to handle user input
def get_user_input(client_socket):
    try:
        while True:
            # Get user input and send it to the server
            message = input('')
            client_socket.sendall(message.encode('utf-8'))
            clear_console_line()
    except EOFError:
        pass  # Handle EOFError (Ctrl+C) gracefully
    except KeyboardInterrupt:
        print('\nExiting...')
        client_socket.sendall('exit'.encode('utf-8'))  # Send a special message to the server
        client_socket.close()

# Function to clear the console line
def clear_console_line():
    print('\033[A                             \033[A')  # Move cursor up and clear line

# Main client function
def main():
    # Set the console title
    set_console_title("Luthien Chat")

    server_host = '127.0.0.1'
    server_port = 8080

    while True:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client_socket.connect((server_host, server_port))
        except ConnectionRefusedError:
            print('Server is offline. Retrying in 5 seconds...')
            time.sleep(5)
            continue

        # Successfully connected to the server
        print(f'Connected to the server {server_host}:{server_port}')
        register_user(client_socket)

        # Start a new thread to receive messages from the server
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receive_thread.start()

        # Start a new thread to handle user input
        input_thread = threading.Thread(target=get_user_input, args=(client_socket,))
        input_thread.start()

        # Set up a signal handler for Ctrl+C
        signal.signal(signal.SIGINT, lambda sig, frame: client_socket.close())

        # Wait for threads to complete
        receive_thread.join()
        input_thread.join()

if __name__ == '__main__':
    main()
