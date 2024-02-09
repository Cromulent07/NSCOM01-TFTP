import socket
import os
from struct import pack

DEFAULT_PORT = 69

OPCODE = {
    "RRQ": 1,
    "WRQ": 2,
    "DATA": 3,
    "ACK": 4,
    "ERROR": 5,
    "OACK": 6,
}

BLOCK_SIZE = {
    1: 128,
    2: 512,
    3: 1024,
    4: 1428,
    5: 2048,
    6: 4096,
    7: 8192,
    8: 16384,
    9: 32768,
}

ERROR_CODE = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}


def sendRequest(sock, server_address, filename, mode, blk_size, is_write):
    opcode = OPCODE["WRQ"] if is_write else OPCODE["RRQ"]
    if opcode == 2:
        file_name = os.path.join(os.path.dirname(__file__), filename)
        tsize = bytearray('tsize'.encode("utf-8"))
        t_size = bytearray(str(os.path.getsize(file_name)).encode("utf-8"))
    filename = bytearray(filename.encode("utf-8"))
    mode = bytearray(mode.encode("utf-8"))
    blksize = bytearray('blksize'.encode("utf-8"))
    blk_size = bytearray(str(blk_size).encode("utf-8"))
    request_message = bytearray()
    request_message.append(0)
    request_message.append(opcode & 0xFF)
    request_message += filename
    request_message.append(0)
    request_message += mode
    request_message.append(0)
    request_message += blksize
    request_message.append(0)
    request_message += blk_size
    request_message.append(0)
    if opcode == 2:
        request_message += tsize
        request_message.append(0)
        request_message += t_size
        request_message.append(0)
    print(request_message)
    sock.sendto(request_message, server_address)


def sendAck(sock, server_address, seq_num):
    ack_message = bytearray()
    ack_message.append(0)
    ack_message.append(OPCODE["ACK"])
    ack_message.append(0)
    ack_message.append(seq_num)
    sock.sendto(ack_message, server_address)


def sendData(sock, server_address, seq_num, data):
    data_message = bytearray()
    data_message.append(0)
    data_message.append(OPCODE["DATA"])
    data_message.append(0)
    data_message.append(seq_num)
    data_message += data
    sock.sendto(data_message, server_address)


def sendError(sock, server_address, error_code, error_message):
    error_message_bytes = bytearray(error_message.encode("utf-8"))
    error_packet = bytearray()
    error_packet.append(0)
    error_packet.append(OPCODE["ERROR"])
    error_packet.append(0)
    error_packet.append(error_code)
    error_packet += error_message_bytes
    error_packet.append(0)
    sock.sendto(error_packet, server_address)


def set_custom_blk_size():
    while True:
        print("[1] 128")
        print("[2] 512 (Default)")
        print("[3] 1024")
        print("[4] 1428")
        print("[5] 2048")
        print("[6] 4096")
        print("[7] 8192")
        print("[8] 16384")
        print("[9] 32768")
        choice = int(input("Enter desired block size: "))
        if 1 <= choice <= 9:
            break
        else:
            print("Error: Enter valid choice.")
    return choice


def get_mode():
    while True:
        print("[1] Netascii")
        print("[2] Octet")
        mode = int(input(("Enter mode: ")))
        if 1 <= mode <= 2:
            break
        else:
            print("Error: Enter valid choice.")
    return "netascii" if mode == 1 else "octet"


def main():
    print("Welcome to the TFTP Client!")
    finished = False
    tapos_na_oack = False

    while True and not finished:

        # server_ip = input("Enter the server IP address: ")
        server_ip = "127.0.0.1"
        try:
            while True:
                # Connect to server
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_address = (server_ip, DEFAULT_PORT)
                sock.settimeout(5)

                print("[1] Get")
                print("[2] Put")
                print("[3] Exit")
                choice = int(input("Enter choice: "))

                completed = False

                if choice == 1:  # Get
                    filename = input("Filename: ")
                    filename = os.path.join(
                        os.path.dirname(__file__), filename)
                    mode = get_mode()
                    blk_size = set_custom_blk_size()
                    file_name = os.path.basename(filename)
                    try:
                        sendRequest(
                            sock,
                            server_address,
                            file_name,
                            mode,
                            BLOCK_SIZE[blk_size],
                            is_write=False)
                        file = open(filename, "wb")
                        completed = True
                    except FileNotFoundError:
                        print("Error: No such file or directory.")
                        continue
                    seq_number = 0
                    print(f"Downloading {filename} from the server...")

                elif choice == 2:  # Put
                    filename = input("Filename: ")
                    filename = os.path.join(
                        os.path.dirname(__file__), filename)
                    server_filename = input(
                        "Enter the filename to be used on the server: ")
                    mode = get_mode()
                    blk_size = set_custom_blk_size()
                    server_filename = os.path.basename(server_filename)
                    try:
                        sendRequest(
                            sock,
                            server_address,
                            server_filename,
                            mode,
                            BLOCK_SIZE[blk_size],
                            is_write=True)
                        file = open(filename, "rb")
                        completed = True
                    except FileNotFoundError:
                        print("Error: No such file or directory.")
                        continue
                    seq_number = 1
                    print(f"Uploading {filename} to the server...")

                elif choice == 3:  # Exit
                    finished = True
                    break

                try:
                    while True:
                        try:
                            data, server = sock.recvfrom(
                                BLOCK_SIZE[blk_size] + 4)
                        except BaseException:
                            print(
                                "Error: Failed to receive data from the TFTP server. Please make sure the server is running and reachable.")
                            completed = False
                            break

                        opcode = int.from_bytes(data[:2], "big")

                        if opcode == OPCODE["DATA"]:
                            seq_number = int.from_bytes(data[2:4], "big")
                            if tapos_na_oack:
                                sendAck(sock, server, seq_number + 1)
                            else:
                                sendAck(sock, server, seq_number)
                            file_block = data[4:]
                            file.write(file_block)

                            if len(file_block) < BLOCK_SIZE[blk_size]:
                                break
                        elif opcode == OPCODE["ACK"]:
                            seq_number = int.from_bytes(data[2:4], "big")
                            file_block = file.read(BLOCK_SIZE[blk_size])

                            if len(file_block) == 0:
                                break

                            sendData(sock, server, seq_number + 1, file_block)
                            if len(file_block) < BLOCK_SIZE[blk_size]:
                                break
                        elif opcode == OPCODE["ERROR"]:
                            error_code = int.from_bytes(
                                data[2:4], byteorder="big")
                            error_message = data[4:-1].decode("utf-8")
                            sendError(sock, server, error_code, error_message)
                            print("ERROR: " + ERROR_CODE[error_code])
                            completed = False
                            break
                        elif opcode == OPCODE["OACK"]:
                            if choice == 1:
                                sendAck(sock, server, seq_number)
                            elif choice == 2:
                                file_block = file.read(BLOCK_SIZE[blk_size])
                                sendData(sock, server, seq_number, file_block)
                        else:
                            break

                except socket.timeout:
                    completed = False
                    print(
                        "Error: Failed to connect to the TFTP server. Please make sure the server is running and reachable.")
                finally:
                    file.close()
                if completed:
                    print(f"{"Get" if choice ==
                             1 else "Put"} completed successfully.")
        except socket.gaierror:
            print("Error: Invalid server IP address. Please try again.")

    sock.close()


if __name__ == "__main__":
    main()
