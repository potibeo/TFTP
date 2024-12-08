#!/usr/bin/python3
import socket
import struct
import os

# TFTP Opcodes
RRQ = 1
WRQ = 2
DATA = 3
ACK = 4
ERROR = 5

BUFFER_SIZE = 516  # TFTP packet size
TIMEOUT = 5  # 5 seconds timeout for socket


def create_request(opcode, filename, mode='octet'):
    """Create RRQ or WRQ packet."""
    return struct.pack(f"!H{len(filename) + 1}s{len(mode) + 1}s", opcode, filename.encode(), mode.encode())


def create_ack(block_number):
    """Create ACK packet."""
    return struct.pack("!HH", ACK, block_number)


def parse_data_packet(packet):
    """Parse DATA packet to get block number and data."""
    opcode, block_number = struct.unpack("!HH", packet[:4])
    data = packet[4:]
    return opcode, block_number, data


def send_file(s, filename, server_address):
    """Handle TFTP PUT (upload) operation."""
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return

    block_number = 0
    with open(filename, 'rb') as f:
        while True:
            data = f.read(512)
            block_number += 1
            packet = struct.pack("!HH", DATA, block_number) + data
            s.sendto(packet, server_address)

            try:
                response, _ = s.recvfrom(BUFFER_SIZE)
                opcode, ack_block = struct.unpack("!HH", response)
                if opcode != ACK or ack_block != block_number:
                    print("Unexpected response or block number mismatch.")
                    break
            except socket.timeout:
                print("Timeout waiting for ACK.")
                break

            if len(data) < 512:
                print("Upload complete.")
                break


def receive_file(s, filename, server_address):
    """Handle TFTP GET (download) operation."""
    with open(filename, 'wb') as f:
        block_number = 0
        while True:
            try:
                response, _ = s.recvfrom(BUFFER_SIZE)
                opcode, received_block, data = parse_data_packet(response)

                if opcode != DATA or received_block != block_number + 1:
                    print("Unexpected response or block number mismatch.")
                    break

                f.write(data)
                block_number = received_block
                ack_packet = create_ack(block_number)
                s.sendto(ack_packet, server_address)

                if len(data) < 512:
                    print("Download complete.")
                    break

            except socket.timeout:
                print("Timeout")
                break


def main():
    print("=== TFTP Client ===")
    host = input("Enter TFTP server IP : ").strip()
    port = input("Enter TFTP server port : ").strip()
    port = int(port) if port else 69

    operation = input("Enter operation [get|put]: ").strip().lower()
    filename = input("Enter filename: ").strip()

    server_address = (host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(TIMEOUT)

    try:
        if operation == "get":
            print(f"Downloading '{filename}' from {host}:{port}...")
            request_packet = create_request(RRQ, filename)
            s.sendto(request_packet, server_address)
            receive_file(s, filename, server_address)

        elif operation == "put":
            print(f"Uploading '{filename}' to {host}:{port}...")
            request_packet = create_request(WRQ, filename)
            s.sendto(request_packet, server_address)
            send_file(s, filename, server_address)

        else:
            print("Invalid operation. Please use 'get' or 'put'.")
    finally:
        s.close()


if __name__ == "__main__":
    main()
