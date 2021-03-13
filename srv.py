import socket
import sys
import threading
from threading import Thread

class clientThread(threading.Thread):
    def __init__(self, socket, ip, port):
        Thread.__init__(self)
        self.socket = socket
        self.ip = ip
        self.port = port

    def run(self):
        flag = True
        while flag:
            getInput = self.socket.recv(1024)
            if(getInput.decode() == "TERMINATED"):
                if self.socket in thread_list:
                    thread_list.remove(self.socket)
                global count 
                count = count - 1
                if count >1:
                    print("< The user "+ str(self.ip)+":"+str(self.port)+ " left ("+str(count)+" users online)")
                else:
                    print("< The user "+ str(self.ip)+":"+str(self.port)+ " left ("+str(count)+" user online)")
                self.socket.close()
                flag =False
            else:
                for clients in thread_list:
                    if clients != self.socket:
                        sendInput = ("["+str(self.ip)+":"+str(self.port)+"]" + getInput.decode()).encode()
                        clients.send(sendInput)
                if flag == True:
                    print("["+str(self.ip)+":"+str(self.port)+"]", getInput.decode())
    


TCP_IP = sys.argv[1]
TCP_PORT_NUM = sys.argv[2]
count = 0
thread_list = []
print("Chat Server started in port " + TCP_PORT_NUM)

try:
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    tcp_sock.bind((TCP_IP, int(TCP_PORT_NUM)))
    while True:
        tcp_sock.listen(5)
        (conn, (ip,port)) = tcp_sock.accept() 

        count = count + 1
        conn.send(str(count).encode())
        newthread = clientThread(conn, ip, port)
        newthread.start()
        if count >1:
            print("> The user "+ str(ip)+":"+str(port)+ " entered ("+str(count)+" users online)")
        else:
            print("> The user "+ str(ip)+":"+str(port)+ " entered ("+str(count)+" user online)")
        thread_list.append(conn)
        for clients in thread_list:
            if clients != conn:
                if count >1:
                    enter_input = "> The user "+ str(ip)+":"+str(port)+ " entered ("+str(count)+" users online)"
                else:
                    enter_input = "> The user "+ str(ip)+":"+str(port)+ " entered ("+str(count)+" user online)"
                clients.send(enter_input.encode())
except KeyboardInterrupt:
    tcp_sock.close()
    print("\nexit")
    sys.exit