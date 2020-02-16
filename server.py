import ssl
import socket
import threading
import json
import sys

##### configuration:
PATH_FILES = {                  # "path" : "file"
    "/" : "index.html",

}

HTTP_PORT = 80
URL = "0.0.0.0"
MAX_CONNECTIONS = 32
ENCODING = "utf-8"
ENCRYPTED = True
#if encryption is turned on:
CERTIFICATE_CHAIN_FILE = ''             # .cert or .pem file
CERTIFICATE_KEY_FILE = ''               # .pem file
HTTPS_PORT = 443
REDIRECT_HTTP = True



##### execution code

def main():
    if ENCRYPTED:
        thread = threading.Thread(target=https_listener
        thread.daemon = True
        thread.start()
    http_listener()



def http_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((URL, HTTP_PORT))
    s.listen(MAX_CONNECTIONS)
    while True:
        thread = threading.Thread(target=handle_http_request,name="thread",args=(s.accept()))
        thread.daemon = True
        thread.start()


def encryption_working():       # returns wether or not all settings for encryption were set correctly
    if not ENCRYPTED:
        return False
    if CERTIFICATE_KEY_FILE == "":
        raise Exception("You need to set the privkey value to the location of your private key!")
        return False
    if(CERTIFICATE_CHAIN_FILE == ""):
        raise Exception("You need to set the certchain value to the location of your certificate!")
        return False
    return True


def https_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((URL, HTTPS_PORT))
    s.listen(MAX_CONNECTIONS)
    if encryption_working():
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(CERTIFICATE_CHAIN_FILE, CERTIFICATE_KEY_FILE)
        secureSocket = context.wrap_socket(s, server_side=True)
        while True:
            try:
                thread = threading.Thread(target=handle_https_request,name="thread",args=(secureSocket.accept()))
                thread.daemon = True
                thread.start()
            except:
                print("HTTP Request over HTTPS")



def handle_http_request(clientsocket, address):
    requestString = ""
    try:
        requestString = clientsocket.recv(4096).decode("utf-8")
    except:
        print("Received encrypted request over HTTP!")      # HTTPS Request over HTTP
        clientsocket.send(b'HTTP/1.1 400 Bad_Request\n')
        print("HTTPS Request over HTTP")
        return

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
            try:
                with open(PATH_FILES[path]) as file:
                    response = file.read()
            except:
                send404(clientsocket)                           # File not found
                print("File \'" + PATH_FILES[path] + "\' not found")
                return
        else:
            send404(clientsocket)                               # Path not set
            print("Path \'" + path + "\' not set")
            return

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
        try:
            with open(PATH_FILES[path]) as file:
                response = file.read()
        except:
            send404(clientsocket)                               # File not found
            print("File \'" + PATH_FILES[path] + "\' not found")
            return
    else:
        send404(clientsocket)                                   # Path not set
        print("Path \'" + path + "\' not set")
        return

    clientsocket.send(b'HTTP/1.1 200 OK\n')
    clientsocket.send(b'Content-Type: text/html\n')
    clientsocket.send(b'\n')
    clientsocket.sendall(bytes(response, ENCODING))
    clientsocket.close()



def htmlRequestToDict(request_string):          # makes requests from webbrowsers easier to work with
    rowSeperated = request_string.split("\n")
    row1Data = rowSeperated[0].split(" ")
    requestDict = {"Type":row1Data[0], "Path":row1Data[1]}
    for i in range(1, len(rowSeperated)):
        if(len(rowSeperated[i])>1):             # prevent bugs caused by empty rows at end message
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


def send404(client):                            # sends 404 Error to client if something went wrong
    client.send(b'HTTP/1.1 404 Not Found\n')
    client.send(b'Content-Type: text/html\n')
    client.send(b'\n')
    client.sendall(b'404 Not Found')
    client.close()


if __name__ == "__main__":
    main()
