import socket
import select
from threading import Thread

hote = ''
port = 12800

connexion_principale = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexion_principale.bind((hote, port))
connexion_principale.listen(5)
print("The Server Listens at {}".format(port))

serveur_lance = True
clients_connectes = []
while serveur_lance:
    # On va vérifier que de nouveaux clients ne demandent pas à se connecter
    # Pour cela, on écoute la connexion_principale en lecture
    # On attend maximum 50ms
    connexions_demandees, wlist, xlist = select.select([connexion_principale],
                                                       [], [], 0.05)
    for connexion in connexions_demandees:
        connexion_avec_client, infos_connexion = connexion.accept()
        print(infos_connexion)
        # On ajoute le socket connecté à la liste des clients
        clients_connectes.append(connexion_avec_client)

    clients_a_lire = []
    try:
        clients_a_lire, wlist, xlist = select.select(clients_connectes,
                                                     [], [], 0.05)
    except select.error:
        pass
    else:
        # On parcourt la liste des clients à lire
        for client in clients_a_lire:
            # Client est de type socket
            msg_recu = client.recv(1024)
            # Peut planter si le message contient des caractères spéciaux
            msg_recu = msg_recu.decode()
            print("Received message from " + str(clients_connectes.index(client)) + " : " + msg_recu)
            if msg_recu == "fin":
                serveur_lance = False



print("Fermeture des connexions")
for client in clients_connectes:
    client.close()

connexion_principale.close()

