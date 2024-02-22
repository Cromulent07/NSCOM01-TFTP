import socket
import os

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


def sendRequest(sock, serverAddress, f1, f2, mode, blkSize, isWrite):
    opcode = OPCODE["WRQ"] if isWrite else OPCODE["RRQ"]
    filenameBytes = bytearray(f2.encode("utf-8"))
    modeBytes = bytearray(mode.encode("utf-8"))
    blksizeBytes = bytearray(
        "blksize\x00".encode("utf-8") +
        str(blkSize).encode("utf-8"))

    requestMessage = bytearray()
    requestMessage.append(0)
    requestMessage.append(opcode & 0xFF)
    requestMessage += filenameBytes
    requestMessage.append(0)
    requestMessage += modeBytes
    requestMessage.append(0)
    requestMessage += blksizeBytes
    requestMessage.append(0)

    if opcode == 2:
        tsizeBytes = bytearray("tsize".encode("utf-8"))
        fileSizeBytes = bytearray(
            str(os.path.getsize(f1)).encode("utf-8"))
        requestMessage += tsizeBytes
        requestMessage.append(0)
        requestMessage += fileSizeBytes
        requestMessage.append(0)

    sock.sendto(requestMessage, serverAddress)


def sendAck(sock, serverAddress, seqNum):
    ackMessage = bytearray()
    ackMessage.append(0)
    ackMessage.append(OPCODE["ACK"])
    ackMessage.extend(seqNum.to_bytes(2, 'big'))
    sock.sendto(ackMessage, serverAddress)


def sendData(sock, serverAddress, seqNum, data):
    dataMessage = bytearray()
    dataMessage.append(0)
    dataMessage.append(OPCODE["DATA"])
    dataMessage.extend((seqNum % 65536).to_bytes(2, 'big'))
    dataMessage += data
    sock.sendto(dataMessage, serverAddress)


def sendError(sock, serverAddress, errorCode, errorMessage):
    errorMessageBytes = bytearray(errorMessage.encode("utf-8"))
    errorPacket = bytearray()
    errorPacket.append(0)
    errorPacket.append(OPCODE["ERROR"])
    errorPacket.append(0)
    errorPacket.append(errorCode)
    errorPacket += errorMessageBytes
    errorPacket.append(0)
    sock.sendto(errorPacket, serverAddress)


def setCustomBlkSize():
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


def getMode():
    while True:
        print("[1] Netascii")
        print("[2] Octet")
        mode = int(input(("Enter mode: ")))
        if 1 <= mode <= 2:
            break
        else:
            print("Error: Enter valid choice.")
    return "netascii" if mode == 1 else "octet"


def getOackBlksize(data):
    nullByteIndex = data.find(b'blksize')+8
    nextNullByte = data[nullByteIndex:].find(b'\x00')
    blkSize = int(data[nullByteIndex:nullByteIndex+nextNullByte].decode())
    blksize_code = [i for i, j in enumerate(BLOCK_SIZE.values()) if j == blkSize][0]+1
    return blksize_code


def main():
    print("Welcome to the TFTP Client!")
    finished = False
    oackFinished = False

    while True and not finished:

        server_ip = input("Enter the server IP address: ")
        # server_ip = "127.0.0.1"
        try:
            while True:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_address = (server_ip, DEFAULT_PORT)
                sock.settimeout(5)

                print("[1] Get")
                print("[2] Put")
                print("[3] Exit")
                choice = int(input("Enter choice: "))

                completed = False

                if choice == 1:  # Get
                    fileName = input("Filename: ")
                    fileName = os.path.join(
                        os.path.dirname(__file__), fileName)
                    fileName = os.path.basename(fileName)
                    mode = getMode()
                    blkSize = setCustomBlkSize()
                    try:
                        sendRequest(
                            sock,
                            server_address,
                            fileName,
                            fileName,
                            mode,
                            BLOCK_SIZE[blkSize],
                            isWrite=False)
                        file = open(fileName, "wb")
                        completed = True
                    except FileNotFoundError:
                        print("Error: No such file or directory.")
                        continue
                    seqNum = 0
                    print(f"Downloading {fileName} from the server...")

                elif choice == 2:  # Put
                    fileName = input("Filename: ")
                    fileNamePath = os.path.join(
                        os.path.dirname(__file__), fileName)
                    serverFilename = input(
                        "Server filename: ")
                    serverFilenamePath = os.path.basename(serverFilename)
                    mode = getMode()
                    blkSize = setCustomBlkSize()
                    try:
                        sendRequest(
                            sock,
                            server_address,
                            fileNamePath,
                            serverFilenamePath,
                            mode,
                            BLOCK_SIZE[blkSize],
                            isWrite=True)
                        file = open(fileNamePath, "rb")
                        completed = True
                    except FileNotFoundError:
                        print("Error: No such file or directory.")
                        continue
                    seqNum = 1
                    print(f"Uploading {fileName} to the server as {serverFilename}...")

                elif choice == 3:  # Exit
                    finished = True
                    break

                try:
                    while True:
                        try:
                            data, server = sock.recvfrom(
                                BLOCK_SIZE[blkSize] + 4)
                        except BaseException:
                            print(
                                "Error: Failed to receive data from the TFTP server. Please make sure the server is running and reachable.")
                            completed = False
                            break

                        opcode = int.from_bytes(data[:2], "big")

                        if opcode == OPCODE["DATA"]:
                            seqNum = int.from_bytes(data[2:4], "big")
                            if oackFinished:
                                sendAck(sock, server, seqNum)
                            else:
                                sendAck(sock, server, seqNum + 1)
                            fileBlock = data[4:]
                            file.write(fileBlock)

                            if len(fileBlock) < BLOCK_SIZE[blkSize]:
                                break
                        elif opcode == OPCODE["ACK"]:
                            seqNum = int.from_bytes(data[2:4], "big")
                            fileBlock = file.read(BLOCK_SIZE[blkSize])

                            sendData(sock, server, seqNum + 1, fileBlock)
                            if len(fileBlock) < BLOCK_SIZE[blkSize]:
                                break
                        elif opcode == OPCODE["ERROR"]:
                            errorCode = int.from_bytes(
                                data[2:4], byteorder="big")
                            errorMesage = data[4:-1].decode("utf-8")
                            sendError(sock, server, errorCode, errorMesage)
                            print("ERROR: " + ERROR_CODE[errorCode])
                            completed = False
                            break
                        elif opcode == OPCODE["OACK"]:
                            blkSize = getOackBlksize(data)
                            if choice == 1:
                                sendAck(sock, server, seqNum)
                            elif choice == 2:
                                fileBlock = file.read(BLOCK_SIZE[blkSize])
                                sendData(sock, server, seqNum, fileBlock)
                            oackFinished = True
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
