import socket
from _thread import *
import re

ServerSocket = socket.socket()                  # by default TCP
host = '127.0.0.1'                              
port = 1262
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))
    exit()                                      # STOP the server if BIND is not possible

print('SERVER STARTED')
ServerSocket.listen(5)

users = {}                                          # CONTAINS RECV SOCKETS
users_send = {}                                     # CONTAINS SEND SOCKETS
def threaded_client(connection):                    # FUNCTION FOR ALL SOCKETS FROM CLIENT
    type = -1
    try:                                                    # REGISTRATION 
        data = connection.recv(2048)
        msg = data.decode('utf-8')
        regex_recv = 'REGISTER TORECV'
        regex_send = 'REGISTER TOSEND'
        if re.match(regex_recv,msg)!=None and re.match(regex_recv,msg).span()[0]==0:  # REGEX MATCH FOR TORECV REQUEST
            type = 0                       
            username = msg.split()[2]
            regex_username = re.compile(r"[A-Za-z0-9]+")
            if not re.fullmatch(regex_username,username):           # ERROR 100
                error = "ERROR 100 Malformed username\n\n"
                connection.sendall(str.encode(error))    
                connection.close()
                print('CLIENT DISCONNECTED DUE TO 100')
                return
            users[username]=connection
            reply = 'REGISTERED TORECV {}'.format(username)
            connection.sendall(str.encode(reply))        
           
        elif re.match(regex_send,msg)!=None and re.match(regex_send,msg).span()[0]==0:  # REGEX MATCH FOR TOSEND REQUEST
            type = 1
            username = msg.split()[2]
            regex_username = re.compile(r"[A-Za-z0-9]+")
            if not re.fullmatch(regex_username,username):       # ERROR 100
                error = "ERROR 100 Malformed username\n\n"
                connection.sendall(str.encode(error))     
                connection.close()
                print('CLIENT DISCONNECTED DUE TO 100')
                return
            users_send[username]=connection                    
            reply = 'REGISTERED TOSEND {}'.format(username)
            connection.sendall(str.encode(reply))
        else :
            raise
    except:
        error = "ERROR 101 No user registered\n\n"             # ERROR 101
        connection.sendall(str.encode(error))    
        connection.close()  
        print('CLIENT DISCONNECTED DUE TO 101')
        return
        
        

    if type==1:                                                 # SEND SOCKET ELSE THREAD WILL BE CLOSED
        while True:
            try:
                data = connection.recv(2048)
                if username not in users:                       # REGISTERED FOR TOSEND BUT NOT FOR TORECV
                    error = "ERROR 101 No user registered\n\n"
                    connection.sendall(str.encode(error))    
                    connection.close()  
                    print('CLIENT DISCONNECTED DUE TO 101')
                    return
                msg = data.decode('utf-8')
                regex_send = 'SEND'
                line1 = msg.split('\n')[0]
                line2 = msg.split('\n')[1]
                if re.match(regex_send,msg)==None or re.match(regex_send,msg).span()[0]!=0: # REGEX MATCH FOR SEND REQUEST
                    raise
                user_toSend = line1.split()[1]        
                regex_length = 'Content-length:'
                if re.match(regex_length,line2)!=None and re.match(regex_length,line2).span()[0]==0:   # REGEX MATCH FOR HEADER
                    content_length = int(line2.split()[1])
                    msg_toSend = msg.split('\n')[3]   
                    if len(msg_toSend)!=content_length:                                             # CONTENT LENGTH NOT MATCHING
                        raise
                else:
                    raise
                msg_toRecv = "FORWARD {}\nContent-length: {}\n\n{}".format(username,content_length,msg_toSend)
                if user_toSend in users:                                                            
                    recv_connection = users[user_toSend]
                    recv_connection.sendall(str.encode(msg_toRecv))
                    msg_fromRecv = recv_connection.recv(2048).decode('utf-8')
                    regex_recv = 'RECEIVED'
                    if re.match(regex_recv,msg_fromRecv)==None or re.match(regex_recv,msg_fromRecv).span()[0]!=0: # ERROR RECEVIED FROM RECV SOCKET
                        error = "ERROR 102 Unable to send\n\n"
                        connection.sendall(str.encode(error))     
                        recv_connection.close()
                        users_send[user_toSend].close()
                        del users[user_toSend]
                        del users_send[user_toSend]
                        print('{} DISCONNECTED DUE TO 103'.format(user_toSend))
                        continue
                    print('MESSAGE SENT FROM {} TO {}'.format(username,user_toSend))
                    reply = 'SEND'
                    connection.sendall(str.encode(reply))
                    
                elif user_toSend=='ALL':                                    # BROADCAST
                    has_Sent = True
                    for recv_user,recv_connection in users.items():             # STOP AND WAIT 
                        if recv_user!=username:
                            recv_connection.sendall(str.encode(msg_toRecv))
                            msg_fromRecv = recv_connection.recv(2048).decode('utf-8')
                            regex_recv = 'RECEIVED'
                            if re.match(regex_recv,msg_fromRecv)==None or re.match(regex_recv,msg_fromRecv).span()[0]!=0: 
                                error = "ERROR 102 Unable to send\n\n"
                                connection.sendall(str.encode(error)) 
                                recv_connection.close()
                                users_send[user_toSend].close()
                                del users[user_toSend]
                                del users_send[user_toSend]
                                print('{} DISCONNECTED DUE TO 103'.format(user_toSend))
                                has_Sent=False
                                break
                    if has_Sent==True:
                        print('MESSAGE SENT FROM {} TO {}'.format(username,user_toSend))
                        reply = 'SEND'
                        connection.sendall(str.encode(reply))
                else:                                                               # USER NOT FOUND
                    error = "ERROR 102 Unable to send\n\n"
                    connection.sendall(str.encode(error))  
                    print("MESSAGE NOT SENT DUE TO 102")   
                    continue
            except:
                try:
                    error = "ERROR 103 Header incomplete\n\n"
                    connection.sendall(str.encode(error))     
                    connection.close()
                    users[username].close()
                    del users[username]
                    del users_send[username]
                    print('{} DISCONNECTED DUE TO 103'.format(username))
                    return
                except:
                    return
            

while True:
    Client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))    
    start_new_thread(threaded_client, (Client, ))   
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))


ServerSocket.close()

