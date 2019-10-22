import socket
import threading
import time

# Here we have the global variables
# The clients consists of the list of thread objects clients
# The logs consists of all the messages send through the server, it is used to redraw when someone new connects
Clients = []
Logs = {}

# -------------------------------SERVER ----------------------------------------
# This is the Server Thread, it is responsible for listening to connexions
# It opens new connections as it is a thread constantly listening at the port for new requests
class Server(threading.Thread):

    ID = 1

    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port

        #Initialize network
        self.network = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.network.bind((self.host, self.port))
        self.network.listen(10)
        print("The Server Listens at {}".format(port))

    # Here we have the main listener
    # As somebody connects we send a small hello as confirmation
    # Also we give him an unique ID that will be able to differentiate them from other users
    # We send the server logs so the new user can redraw at the same state in the board
    # We send the list of connected users to construct the permission system
    def run(self):
        while True:
            connexion, infos_connexion = self.network.accept()
            print("Sucess at " + str(infos_connexion))
            Hello = 'HLO'.encode()
            connexion.send(Hello)

            time.sleep(0.1)

            #Send all ID's so user cannot repeat any id's
            msg = b" "
            for client in Clients:
                msg = msg + b" " + client.clientID.encode()
            connexion.sendall(msg)

            time.sleep(0.1)

            #Receive the choosen ID from user
            NewUserId = connexion.recv(1024).decode()

            for log in Logs:
                connexion.send(Logs[log])

            a = Client(connexion,NewUserId)

            a.load_users()
            Clients.append(a)
            Server.ID = Server.ID + 1
            a.start()


# -----------------------------------CLIENTS -------------------------------------
# This is the client thread, it is responsible for dealing with the messages from all different clients
# There is one thread for every connected client, this allows us to deal with them all at the same time
class Client(threading.Thread):

    MessageID = 0

    def __init__(self, connexion,clientID):
        threading.Thread.__init__(self)
        self.connexion = connexion
        self.clientID = clientID

    def load_users(self):
        for client in Clients:
            msg = 'A' + ' ' + str(client.clientID) + ' ' + 'f'
            self.connexion.send(msg.encode())
            msg = 'A' + ' ' + str(self.clientID) + ' ' + 'f'
            client.connexion.send(msg.encode())




    def run(self):
        while True:
            try:
                #Here we start by reading the messages
                #Split according to the protocol
                msg = self.connexion.recv(1024)
                decodedMSG = msg.decode()
                splitMSG = decodedMSG.split()

                if( "LO" in splitMSG):
                    self.echoes_act_load(msg)

                #Z is used to indicate message deletion so let's echo with a different function
                #Deletion messages are treated differently from normal messages
                #We don't keep track of them, and they must erase their log from the server
                #So we call a different function to deal with them
                if (splitMSG[0] == 'Z'):
                    self.echoes_delete(msg)
                    continue

                # Here we have the erase all message type
                # For the erase all function the message is completely constructed in the client
                # So differently from all the messages we just echo it all here!
                # That's why there is no addition of the end message character f
                # Also since it is a delete message, we don't give it a message id m
                # This was done due to a maximum message length, this allows us to divide the message in chunks
                if (splitMSG[0] == 'E'):
                    for s in splitMSG:
                        try:
                            Logs.pop(s)
                        except KeyError:
                            pass
                    for client in Clients:
                        client.connexion.sendall(msg)
                    continue

                if(splitMSG[0] == 'DR'):
                    self.update_position_in_logs(msg)
                    self.echoes_move(msg)
                    continue

                self.echoesAct3(msg)

            #We pass the Connection Reset Error since the pinger will deal with it more effectivelly
            except ConnectionResetError:
                pass
            except ConnectionAbortedError:
                pass



    #Here we echo messages to all members of the network
    #Keep a dictonary of the messages to send it to new users
    #Update the message number for every message send
    def echoesAct3(self, msg):
        msg = msg.decode()
        splitMSG = msg.split()
        msg = msg + " " + "m" + str(Client.MessageID) + " " + "f"
        msg = msg.encode()
        # We do not want to log some types of messages. For instance like permission messages
        if splitMSG[0] not in ["P"]:
            Logs["m" + str(Client.MessageID)] = msg
        Client.MessageID = Client.MessageID + 1
        for client in Clients:
            client.connexion.sendall(msg)


    #Here we echo delete messages
    #We need to remove them from the message log
    #And finally echoe the message to all members of the server
    def echoes_delete(self, msg):
        msg = msg.decode()
        msg = msg + " " + "f"
        splitMsg = msg.split()
        try:
            Logs.pop(splitMsg[1])
        except KeyError:
            pass

        msg = msg.encode()
        for client in Clients:
            client.connexion.sendall(msg)

    # Since the load messages were arriving to fast, they would all arrive with no separation
    # The f and LO were introduced to separate the streams of messages!
    # Once they have been properly separated into original messages we just call the original send function on them
    # And echoe them to the server
    def echoes_act_load(self, msg):
        msg = msg.decode()
        split_message_stream = msg.split("f")

        for message in split_message_stream:
            msg = message.split()

            try:
                if( msg[0] == "LO" ):
                    msg = msg[1:]
                    msg = " ".join(msg)
                    msg = msg.encode()
                    self.echoesAct3(msg)
            except IndexError:
                pass


    # Here we echoe a move message!
    # We should not keep a counter for those types of message
    # Also we do not add them to the Log
    def echoes_move(self, msg):
        msg = msg + b" f"
        for client in Clients:
            client.connexion.sendall(msg)


    #Here we update the position of a draged object in the server
    def update_position_in_logs(self,msg):
        msg = msg.decode()
        splitMsg = msg.split()

        #We retrieve the original message
        OriginalMessage = Logs[splitMsg[1]]
        OriginalMessage = OriginalMessage.decode()
        OriginalMessage = OriginalMessage.split()

        #Them add to the coordinates according to the drag!
        #The position of the coordinates of each message is different for different types of message
        #This requires us to alternate the coordinates differently according to the type
        if( OriginalMessage[0] in ['L', 'C', 'O', 'R', 'S', 'D']):
            OriginalMessage[1] = str(int(OriginalMessage[1]) + int(splitMsg[2]))
            OriginalMessage[3] = str(int(OriginalMessage[3]) + int(splitMsg[2]))
            OriginalMessage[2] = str(int(OriginalMessage[2]) + int(splitMsg[3]))
            OriginalMessage[4] = str(int(OriginalMessage[4]) + int(splitMsg[3]))
            OriginalMessage = " ".join(OriginalMessage)

            #Rewrite the log
            Logs[splitMsg[1]] = OriginalMessage.encode()
        elif(   OriginalMessage[0] in ['T'] ):
            OriginalMessage[2] = str(int(OriginalMessage[2]) + int(splitMsg[2]))
            OriginalMessage[3] = str(int(OriginalMessage[3]) + int(splitMsg[3]))
            OriginalMessage = " ".join(OriginalMessage)

            # Rewrite the log
            Logs[splitMsg[1]] = OriginalMessage.encode()

# --------------------------------PINGER------------------------------------------------------------
# This is the pinger Thread, it is used to check how many users are currently connected
# It sends messages to all users, if it receives a disconnection error it does the following
# Sends a removal message to alert all users of the disconnection
# Removes client from list of clients to avoid sending messages to it again
# Also it sends the permission to delete the disconnected user stuff from the board!
class Pinger(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def announce_remove_user(self, disconnectedClient):
        for client in Clients:
            msg = 'RE' + ' ' + str( disconnectedClient.clientID) + ' ' + 'f'
            client.connexion.sendall(msg.encode())

    def run(self):
        while True:
            time.sleep(0.1)
            for client in Clients:
                try:
                    msg = "$".encode()
                    client.connexion.send(msg)
                except ConnectionResetError:
                    Clients.remove(client)
                    self.announce_remove_user(client)
                except ConnectionAbortedError:
                    Clients.remove(client)
                    self.announce_remove_user(client)


if __name__ == "__main__":

    host = ''
    port = 5000
    server = Server(host,port)
    server.start()
    Pinger().start()


