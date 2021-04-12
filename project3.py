import socket
import sys
import threading
from threading import Thread
import os
import time

MAX_DATA_RECV = 1000000
count = 0
flag = 0
def byte2str(B):
    S = "".join([chr(b) for b in B])
    return S

def read_data(sock):
    
    data = sock.recv(MAX_DATA_RECV)
    data_size = int()
    data_decode = byte2str(data)
    data_line = [line.strip() for line in data_decode.split('\n')]
    for line in data_line:
        if line.find("Content-Length: ") == 0:
            data_size = int(line[line.find(' ') + 1:])

    while len(data) < data_size:
        data += sock.recv(MAX_DATA_RECV)

    return data

class Proxy:
    def __init__(self, server, thread_id, cli_socket, cli_host, cli_port):
        self.server = server #main it is connected to 
        self.thread_id = thread_id
        self.cli_socket = cli_socket
        self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cli_host = cli_host
        self.cli_port = cli_port
        self.srv_host = str()
        self.srv_port = 80
        self.cli_prx_data = bytes()
        self.prx_cli_data = bytes()
        self.request = str()
        self.sendrequest = str()
        self.user_agent = str()
        self.status_code = str()
        self.content_type = str()
        self.content_length = str()
        self.last_length = str()
        self.url_filter = False
        self.image_filter = False
        self.imsi_image_filter = 'X'
        self.imsi_url_filter = 'X'
    

    def terminate(self):

        global flag
        flag = 1

        self.server.lock.acquire()
        global count
        count += 1
        print("--------------------------------------")
        print(str(count)+ " [Conn:  "+str(self.thread_id)+"/   "+str(len(self.server.thread_list))+"]")
        print("[ "+self.imsi_url_filter+" ] URL filter | [ " + self.imsi_image_filter + " ] Image filter")
        print()
        print("[CLI connected to "+str(self.cli_host)+":"+str(self.cli_port)+"]")
        print("[CLI ==> PRX --- SRV]")
        print(" > " + self.sendrequest)
        print(" > " + self.user_agent)
        print("[SRV connected to "+str(self.srv_host)+":"+str(self.srv_port)+"]")
        print("[CLI --- PRX ==> SRV]")
        print(" > " + self.sendrequest + "\n" + " > " + self.user_agent)
        print("[CLI -- PRX <== SRV]") # for interface issues
        print(" > " + self.status_code)
        print(" > " + self.content_type +" "+ self.content_length)
        print("[CLI <== PRX --- SRV]")
        print(" > " + self.status_code)
        print(" > " + self.content_type+" "+self.last_length)
        print("[CLI TERMINATED]")
        print("[SRV TERMINATED]")
        self.cli_socket.close()
        self.srv_socket.close()

        
        self.server.thread_list.remove(self.thread_id)
        self.server.lock.release()


    def proxy_send_server(self):
        if(self.url_filter == True): # redirection
            self.srv_socket.connect((self.server.redirect, self.srv_port))
            data_decode = byte2str(self.cli_prx_data) # decoding
            data_line = [line.strip() for line in data_decode.split('\n')]
            for i, line in enumerate(data_line): #change http and host into reidirect
                if line.find("Host: ") == 0:
                    data_line[i] = data_line[i].split(' ')
                    data_line[i][1] = self.server.redirect
                    data_line[i] = ' '.join(data_line[i])
                elif "HTTP" in line:
                    data_line[i] = data_line[i].split(' ')

                    data_line[i][1] = data_line[i][1].replace(self.srv_host, self.server.redirect)
                    data_line[i] = ' '.join(data_line[i])
                    request_line = data_line[i]

            data_decode = "\r\n".join(data_line) # http header ends with \r\n
            self.cli_prx_data = data_decode.encode() # encode in order to save into bytes
            self.srv_host = self.server.redirect
            self.sendrequest = "GET " + self.server.redirect # request alter
        else: # if not redirect
            self.srv_socket.connect((self.srv_host, self.srv_port))
            data_decode = byte2str(self.cli_prx_data)
            data_line = [line.strip() for line in data_decode.split('\n')]
            data_decode = "\r\n".join(data_line)
            self.cli_prx_data = data_decode.encode()
        # print("[SRV connected to "+str(self.srv_host)+":"+str(self.srv_port)+"]")
        # print("[CLI --- PRX ==> SRV]")
        # print(" > " + self.request + "\n" + " > " + self.user_agent)
        
        self.srv_socket.sendall(self.cli_prx_data) # send to target socket whether it is redirected or not
        
        data = read_data(self.srv_socket) # receive data from target

        imsi_data =byte2str(data) # decoding
        line = imsi_data.split('\n') # split into line
        
        if "HTTP" in line[0]: # get request
            index = line[0].find("HTTP")
            self.request = line[0][:index]
        for l in line:
            l = l.strip()
        index = line[0].find(' ')
        self.status_code = line[0][index + 1:] #fetch whcih status code
        self.content_type = str()
        self.content_length = str()
        for l in line:
            if l.find("Content-Type: ") == 0: # can show if it is image, text etc...
                imsi_index = l.find(' ')
                self.content_type = l[imsi_index + 1:].strip()
            if l.find("Content-Length: ") == 0:
                imsi_index = l.find(' ')
                self.content_length= l[imsi_index + 1:].strip() + "bytes" # what contents, and bytes
                self.last_length = self.content_length
                
        
        # print("[CLI -- PRX <== SRV]") # for interface issues
        # print(" > " + self.status_code)
        # print(" > " + self.content_type +" "+ self.content_length)

        if("image" in self.content_type and self.server.image_tf == True): # if there is image and filtering on
            imsi_data =byte2str(self.prx_cli_data) # decoding
            data_line = [line.strip() for line in data_decode.split('\n')]
            for i, line in enumerate(data_line):
                if "Content-Type" in line:
                    line[i+1:] = ""
            data_decode = "\r\n".join(data_line)
            self.prx_cli_data = data_decode.encode()
            self.last_length = "0bytes"
        else:
            self.prx_cli_data = data
        
        #print(byte2str(data))

    def client_send_proxy(self):

        data = read_data(self.cli_socket) # get data from client
        self.cli_prx_data = data # in bytes

        imsi_data = byte2str(data) #decoding..
        cd = byte2str(data)
        line = imsi_data.split('\n') 
        self.sendrequest = line[0]
        for l in line:
            l = l.strip() # not nessary erase

        #if "HTTP" not in self.request :
        #    self.terminate()
        #    return

        if "HTTP" in line[0]:
            index = line[0].find("HTTP")
            self.sendrequest = line[0][:index]

        for i in line:
            if "Referer:" in i:  
                ii = i.split(" ")   
                if "?image_on" in ii[1] :
                    self.image_filter = False
                    self.server.image_tf = False
                    self.imsi_image_filter = 'X'
                    break
                elif "?image_off" in ii[1] :
                    self.image_filter = True 
                    self.server.image_tf = True
                    self.imsi_image_filter = 'O'
                    break
            
        # else:
        #     self.image_filter = False
        #     self.server.image_tf = False
        #     self.imsi_image_filter = 'X'

        if self.server.original in line[0]:
            self.imsi_url_filter = 'O'
            self.url_filter = True
        else:
            self.imsi_url_filter = 'X'
            self.url_filter = False
        
        #print("[ "+self.imsi_url_filter+" ] URL filter | [ " + self.imsi_image_filter + " ] Image filter")
        for l in line:
            l = l.strip()
            if l.find("Host: ") == 0:
                index = l.find(' ')
                imsi_srv_host = l[index + 1:]
                if ":" in imsi_srv_host:
                    imsi_srv_host = imsi_srv_host.split(":")
                    self.srv_host = imsi_srv_host[0]
                    self.srv_port = int(imsi_srv_host[1])
                else:
                    self.srv_host = imsi_srv_host
            elif l.find("User-Agent: ") == 0:
                l.split()
                index = l.find(' ')
                self.user_agent = l[index + 1:]
            
        # print("[CLI connected to "+str(self.cli_host)+":"+str(self.cli_port)+"]")
        # print("[CLI ==> PRX --- SRV]")
        # print(" > " + self.request)
        # print(" > " + self.user_agent)
        


        self.srv_port = int(self.srv_port)

        self.proxy_send_server()
        
        # print("[CLI <== PRX --- SRV]")
        # print(" > " + self.status_code)
        # print(" > " + self.content_type+" "+self.content_length)



        self.cli_socket.sendall(self.prx_cli_data)
        self.terminate()




class Server:
    def __init__(self, port):
        self.port = port # get port number
        self.lock = threading.Lock() # to prevent interrupting thread
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create of socket
        self.original = "" # original that should be changed
        self.redirect = "" # revised url
        self.thread_list = []
        self.image_tf = False
    def run(self, original = None, redirect = None): # start
        
            self.redirect = redirect
            self.original = original
            print("Starting proxy server on port: "+ str(self.port)) 
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1) # in case of reusal
            self.socket.bind(("",self.port)) #bind with local port
            self.socket.listen() #wait 
            start = time.time()
            while(True):
                try:
                    conn, (cli_ip,cli_port) = self.socket.accept() # accept new socket (each thread)

                    self.lock.acquire()
                    #global count # count how many times 
                    #count += 1
                    thread_id = 1
                    while(thread_id in self.thread_list): # thread creation
                        thread_id += 1
                    self.thread_list.append(thread_id)
                    # print("--------------------------------------")
                    # print(str(count)+ " [Conn:  "+str(thread_id)+"/   "+str(len(self.thread_list))+"]")
                    self.lock.release()

                    proxy = Proxy(self, thread_id, conn, cli_ip, cli_port) # make proxy server
                    new = threading.Thread(target = proxy.client_send_proxy) # make start with client send proxy
                    new.daemon = True 
                    new.start() # start
                    global flag
                    #while flag == 0:
                    #    b = time.time()
                    #flag = 0
                except KeyboardInterrupt: # for exceptions
                    # a = sys.getsizeof('main')
                    # print("==============================")
                    # print(str(count) +":" +str(a))
                    # print("==============================")
                    self.socket.close()
                    print("exit")
                    sys.exit(1)


############################### so far so good ############################
if __name__ == '__main__':
    port = int(sys.argv[1])  # get port from input -> 1 input only
    proxy_server = Server(port) # create server by using class Server
    proxy_server.run("yonsei", "www.linuxhowtos.org") # redirection -> anything that has yonsei inside will turn into this link
