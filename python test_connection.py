import socket


try:
    # Attempt to connect to the language server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 2087))  # Ensure the port is correct
        print("Successfully connected to the language server!")

except ConnectionRefusedError:
    print("Connection refused: The language server may not be running on the specified port.")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
