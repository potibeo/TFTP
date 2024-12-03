import socket
import sys
import time


def send_request(server_address, mode, filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    if mode == 'get':
        request_packet = f'\x00\x01{filename}\x00octet\x00'.encode()
    elif mode == 'put':
        request_packet = f'\x00\x02{filename}\x00octet\x00'.encode()
    else:
        print("모드가 잘못되었습니다.")
        return

    sock.settimeout(5)

    try:
        sock.sendto(request_packet, server_address)
        print("서버에 요청 패킷 전송됨")

        while True:
            data, _ = sock.recvfrom(516)
            print("서버로부터 데이터 수신:", data)


    except socket.timeout:
        print("서버 응답 없음. 타임아웃 발생.")
    finally:
        sock.close()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("사용법: mytftp <host_address> <get|put> <filename>")
        sys.exit(1)

    host = sys.argv[1]
    mode = sys.argv[2]
    filename = sys.argv[3]

    send_request((host, 69), mode, filename)
