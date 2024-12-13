import socket
import struct
import os

# TFTP Opcodes
RRQ = 1
WRQ = 2
DATA = 3
ACK = 4
ERROR = 5

BUFFER_SIZE = 516  # 패킷의 최대 크기
TIMEOUT = 5  #  타임아웃 설정


def create_request(opcode, filename, mode='octet'): # TFTP 요청 패킷을 생성합니다.

    return struct.pack(f"!H{len(filename) + 1}s{len(mode) + 1}s", opcode, filename.encode(), mode.encode())


def create_ack(block_number): #  ACK 패킷을 생성합니다.


    return struct.pack("!HH", ACK, block_number)


def parse_data_packet(packet): #수신한 데이터 패킷을 분석합니다.

    opcode, block_number = struct.unpack("!HH", packet[:4])
    data = packet[4:]
    return opcode, block_number, data


def send_file(s, filename, server_address):#서버로 파일을 업로드합니다.


    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return

    block_number = 0
    with open(filename, 'rb') as f:
        while True:
            # 512 바이트씩 읽어서 패킷 생성
            data = f.read(512)
            block_number += 1
            packet = struct.pack("!HH", DATA, block_number) + data
            s.sendto(packet, server_address)

            try:
                # ACK 패킷 대기
                response, _ = s.recvfrom(BUFFER_SIZE)
                opcode, ack_block = struct.unpack("!HH", response)

                if opcode != ACK or ack_block != block_number:
                    print("Unexpected ACK received. Upload aborted.")
                    break

            except socket.timeout:
                print("Timeout occurred. Upload aborted.")
                break

            if len(data) < 512:  # 마지막 데이터일 경우 업로드 완료
                print("Upload complete.")
                break


def receive_file(s, filename, server_address): # 서버에서 파일을 다운로드합니다.

    with open(filename, 'wb') as f:
        block_number = 0
        while True:
            try:
                # 데이터 패킷 대기
                response, _ = s.recvfrom(BUFFER_SIZE)
                opcode, received_block, data = parse_data_packet(response)

                if opcode != DATA or received_block != block_number + 1:
                    print("Unexpected data packet. Download aborted.")
                    break

                # 수신한 데이터 파일에 쓰기
                f.write(data)
                block_number = received_block

                # ACK 패킷 생성 및 전송
                ack_packet = create_ack(block_number)
                s.sendto(ack_packet, server_address)

                if len(data) < 512:  # 마지막 데이터일 경우 다운로드 완료
                    print("Download complete.")
                    break

            except socket.timeout:
                print("Timeout occurred. Download aborted.")
                break


def main(): #   사용자로부터 입력을 받아 TFTP 서버와 통신합니다.
   
    host = input("TFTP server IP 입력하세요: ").strip()
    port = input("TFTP server port 입력하세요: ").strip()
    port = int(port) if port else 69

    operation = input("[get|put] get 또는 put을 입력하세요: ").strip().lower()
    filename = input("filename 입력하세요: ").strip()

    # 서버 주소 및 UDP 소켓 생성
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
