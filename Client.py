import socket

connexion_avec_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexion_avec_serveur.connect(('localhost', 12800))

while 1:

    msg_send = input("Type the command: \n")
    msg_send = msg_send.encode()
    connexion_avec_serveur.send(msg_send)
