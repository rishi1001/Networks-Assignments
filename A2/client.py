import socket
import threading
import re

sendSocket = socket.socket()                    # 2 sockets 1 sending and 1 reciveing
recvSocket = socket.socket()
host = input('ENTER IP:')
port = 1262

print('Waiting for connection..')
try:                                            
    sendSocket.connect((host, port))
    recvSocket.connect((host,port))
except socket.error as e:                            # CONNECTION REFUSED (SERVER IS NOT SETUP)
    print(str(e))        
    exit()



def send_thread():     
    while True:
        msg = input()
        checkUser = re.compile(r"@([A-Za-z0-9]+)")
        list_msg = msg.split()
        if (not list_msg) or (not re.fullmatch(checkUser,list_msg[0])):       # FORMAT CHECKING ON CLIENT SIDE BEFORE SENDING THE MESSAGE
            print('Incorrect Username or Format')
            continue        
        getUser = "@([a-zA-Z0-9]+)"
        user_toSend = re.findall(getUser,msg)[0]
        start_index_msg = len(user_toSend)+2
        msg_toSend = msg[start_index_msg:]
        content_length = len(msg_toSend)
        msg_toServer = "SEND {}\nContent-length: {}\n\n{}".format(user_toSend,content_length,msg_toSend)
        sendSocket.sendall(str.encode(msg_toServer))
        Response = sendSocket.recv(1024).decode('utf-8')
        regex_send = 'SEND'
        if re.match(regex_send,Response)==None or re.match(regex_send,Response).span()[0]!=0: # ERROR MESSAGE FROM SERVER
            error_102 = '102'
            if error_102 in Response:
                print('MESSAGE NOT SENT DUE TO 102')
                continue
            else:
                sendSocket.close()                                      
                print('DISCONNECTED')
                return
        else:
            print('MESSAGE SENT TO {}'.format(user_toSend))
        
    sendSocket.close()

def recv_thread():
    while True:
        try:
            Response = recvSocket.recv(1024).decode('utf-8')      
            regex_forward = 'FORWARD'
            line1 = Response.split('\n')[0]
            line2 = Response.split('\n')[1]
            if re.match(regex_forward,Response)==None or re.match(regex_forward,Response).span()[0]!=0:  # MESSAGE FORMAT NOT MATCHED
                raise
            sender_username = line1.split()[1]
            regex_length = 'Content-length:'
            if re.match(regex_length,line2)==None or re.match(regex_length,line2).span()[0]!=0:   # MESSAGE FORMAT NOT MATCHED
                raise
            content_length = int(line2.split()[1])
            message = Response.split('\n')[3]
            if len(message)!=content_length:
                raise
            print('MESSAGE FROM {} : {}'.format(sender_username,message))
            msg_toSend = 'RECEIVED {}\n\n'.format(sender_username)
            recvSocket.sendall(str.encode(msg_toSend))
        except:                                                                             # ERROR 103
            error = "ERROR 103 Header incomplete\n\n"
            recvSocket.sendall(str.encode(error))     
            recvSocket.close()                        
            print('DISCONNECTED FROM SERVER DUE TO 103')
            return
          
    recvSocket.close()

print('CONNECTED TO SERVER')



def register():                                                         # REGISTRATION

    username = input('USERNAME :')
    msg_toServer = "REGISTER TOSEND {} \n\n".format(username)
    sendSocket.sendall(str.encode(msg_toServer))
    Response = sendSocket.recv(1024).decode('utf-8')
    regex_send = 'REGISTERED TOSEND'
    if re.match(regex_send,Response)==None or re.match(regex_send,Response).span()[0]!=0:
        print('ERROR RECEIVED DISCONNECTING')        
        return False
    msg_toServer = "REGISTER TORECV {} \n\n".format(username)
    recvSocket.sendall(str.encode(msg_toServer))
    Response = recvSocket.recv(1024).decode('utf-8')
    regex_recv = 'REGISTERED TORECV'
    if re.match(regex_recv,Response)==None or re.match(regex_recv,Response).span()[0]!=0:
        print('ERROR RECEIVED DISCONNECTING') 
        return False
    return True
    
if register():                                                      # IF REGISTRATION IS SUCCESSFUL

    t1 = threading.Thread(target=send_thread)
    t2 = threading.Thread(target=recv_thread)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


