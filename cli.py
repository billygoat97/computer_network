import socket
import sys
import threading
from threading import Thread

class serverThread(Thread):
    def __init__(self, socket, ip, port):
        Thread.__init__(self)
        self.socket = socket
        self.ip = ip
        self.port = port
    def run(self):
        lock = threading.Lock()
        lock.acquire()
        try:
            while True:
                send_messege = input("[You] ")
                self.socket.send(send_messege.encode())
            lock.release()
        except KeyboardInterrupt:
            self.socket.send("TERMINATED".encode())
            self.socket.close()
            print("\nexit")
            sys.exit

class serverReadThread(Thread):
    def __init__(self, socket, ip, port):
        Thread.__init__(self)
        self.socket = socket
        self.ip = ip
        self.port = port
    def run(self):
        lock = threading.Lock()
        lock.acquire()
        try:
            while True:
                received = (self.socket.recv(BUFFERSIZE))
                print(received.decode())
            lock.release()
        
        except KeyboardInterrupt:
            self.socket.send("TERMINATED".encode())
            self.socket.close()
            print("\nexit")
            sys.exit

BUFFERSIZE = 1024
TCP_IP = sys.argv[1]
TCP_PORT_NUM = sys.argv[2]



try:
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((TCP_IP,int(TCP_PORT_NUM)))
    count = (tcp_sock.recv(BUFFERSIZE))
    if(int(count)>1):
        print("Connected to the chat server ("+count.decode()+" users online)")
    else:
        print("Connected to the chat server ("+count.decode()+" user online)")
    ST = serverThread(tcp_sock,TCP_IP,int(TCP_PORT_NUM))
    SRT=serverReadThread(tcp_sock,TCP_IP,int(TCP_PORT_NUM))
    ST.start()
    SRT.start()
    


except KeyboardInterrupt:
    tcp_sock.send("TERMINATED".encode())
    tcp_sock.close()
    print("\nexit")
    sys.exit

