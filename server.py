import ssl
import socket
import threading
import json
import sys

##### configuration:
PATH_FILES = {                  # "path" : "file"
    "/data" : "index.html",

}

HTTP_PORT = 80
URL = "0.0.0.0"
MAX_CONNECTIONS = 32
ENCODING = "utf-8"
ENCRYPTED = True
#if encryption is turned on:
CERTIFICATE_CHAIN_FILE = ''         # .cert or .pem file
CERTIFICATE_KEY_FILE = ''           # .pem file
HTTPS_PORT = 443
REDIRECT_HTTP = True

# ISSUES:
# 1. HTTPS redirects off => Crash
# 2. Invalid Certificate => Crash




##### execution code

def main():
    thread = threading.Thread(target=http_listener)
    thread.daemon = True
    thread.start()
    https_listener()



def http_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((URL, HTTP_PORT))
    s.listen(MAX_CONNECTIONS)
    while True:
        thread = threading.Thread(target=handle_http_request,name="thread",args=(s.accept()))
        thread.daemon = True
        thread.start()



def https_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((URL, HTTPS_PORT))
    s.listen(MAX_CONNECTIONS)
    if ENCRYPTED:
        if CERTIFICATE_KEY_FILE == "":
            raise Exception("You need to set the privkey value to the location of your private key!")
        if(CERTIFICATE_CHAIN_FILE == ""):
            raise Exception("You need to set the certchain value to the location of your certificate!")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)#
        context.load_cert_chain(CERTIFICATE_CHAIN_FILE, CERTIFICATE_KEY_FILE)
        secureSocket = context.wrap_socket(s, server_side=True)
        while True:
            thread = threading.Thread(target=handle_https_request,name="thread",args=(secureSocket.accept()))
            thread.daemon = True
            thread.start()
    else:
        raise Exception("Encryption is not turned on")



def handle_http_request(clientsocket, address):
    requestString = clientsocket.recv(4096).decode("utf-8")
    print(requestString)
    request = htmlRequestToDict(requestString)
    if REDIRECT_HTTP:
        redirect = "https://" + request["Host"].strip() + request["Path"].strip()
        clientsocket.send(b'HTTP/1.1 301 Moved Permanently\n')
        clientsocket.send(bytes('Location: ' + redirect + '\n', ENCODING))
        clientsocket.close()
    else:
        path = request["Path"]
        response = ""

        if path in PATH_FILES:
            with open(PATH_FILES[path]) as file:
                response = file.read()
        else:
            response = "<h1>404 Page not found</h1>"
        clientsocket.send(b'HTTP/1.1 200 OK\n')
        clientsocket.send(b'Content-Type: text/html\n')
        clientsocket.send(b'\n')
        clientsocket.sendall(bytes(response, ENCODING))
        clientsocket.close()


def handle_https_request(clientsocket, address):
    requestString = clientsocket.recv(4096).decode("utf-8")
    request = htmlRequestToDict(requestString)
    path = request["Path"]
    response = ""

    if path in PATH_FILES:
        with open(PATH_FILES[path]) as file:
            response = file.read()
    else:
        response = "<h1>404 Page not found</h1>"
    clientsocket.send(b'HTTP/1.1 200 OK\n')
    clientsocket.send(b'Content-Type: text/html\n')
    clientsocket.send(b'\n')
    clientsocket.sendall(bytes(response, ENCODING))
    clientsocket.close()



def htmlRequestToDict(request_string):      # makes requests from webbrowsers easier to work with
    rowSeperated = request_string.split("\n")
    row1Data = rowSeperated[0].split(" ")
    requestDict = {"Type":row1Data[0], "Path":row1Data[1]}
    for i in range(1, len(rowSeperated)):
        if(len(rowSeperated[i])>1):         # prevent bugs caused by empty rows at end message
            key = ""
            value = ""
            j = 0
            while rowSeperated[i][j] != ":":
                key += rowSeperated[i][j]
                j+=1
            j+=1    #skip ":"
            while j < len(rowSeperated[i]):
                value += rowSeperated[i][j]
                j+=1
            requestDict[key] = value
    return requestDict


if __name__ == "__main__":
    main()
