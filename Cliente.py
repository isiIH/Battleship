import json
import socket
import sys
import threading
from main_screen import Game

from config import *

class Cliente:
    def __init__(self, nombre):
        self.nombre = nombre
        self.localIP = None
        self.localPort = None
        self.bufferSize = 1024
        self.client = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.client.settimeout(1)
        self.game = Game(self)

    def conectarAServidor(self, ip, port):
        self.localIP = ip
        self.localPort = port
        self.enviarAServidor({'action': 'c', 'bot' : 0, 'ships' : {}, 'position': []})

    def enviarAServidor(self, dct):
        print(dct)
        self.client.sendto(bytes(json.dumps(dct), 'utf-8'), (self.localIP, self.localPort))

    def listen(self):
        while True:
            while True:
                try:
                    content = json.loads(self.client.recvfrom(
                        self.bufferSize)[0].decode("utf-8"))
                    break

                except socket.timeout: 
                    if not self.game.run:
                        self.client.close()
                        sys.exit(0)
                
                except ConnectionResetError:
                    self.game.msg = "Server not responding"
                    self.game.setState(0)

            print("Received: {}".format(content))

            match content['action']:
                case 'c':
                    if content['status']:
                        self.game.setState(1)
                        
                case 'b':
                    if content['status']:
                        self.game.setState(2)
                        self.game.wait = False
                        self.game.reset_timer()
                        self.game.turno = content.get('first',None)
                        if content.get('name',None) is not None:
                            self.game.enemy = content['name']
                    else:
                        self.game.mode = None

                case 's':
                    if content['status']:
                        self.game.reset_timer()
                        self.game.board2.actualizarTablero(content['effective'])
                        if not content['effective']:
                            if self.game.turno is not None:
                                self.game.turno = not self.game.turno

                        left = content.get('left',None)
                        if left is not None:
                            self.game.show = True
                            self.game.board2.nBarcos = left

                case 'a':
                    self.game.reset_timer()
                    self.game.board1.realizarAtaque(content['position'], content['status'])
                    if not content['status']:
                        if self.game.turno is not None:
                            self.game.turno = not self.game.turno

                case 'l':
                    self.game.setState(3)
                    if content['win']:
                        self.game.winMessage = "GAME OVER. YOU WIN"
                    else:
                        if self.game.enemy == "Campo enemigo":
                            self.game.winMessage = "GAME OVER. ENEMY WINS"
                        else:
                            self.game.winMessage = f"GAME OVER. {self.game.enemy} WINS"

                case 'd':
                    self.game.clearWindow(1)
                    
    def run(self):
        listener = threading.Thread(target=self.listen)
        listener.start()
        self.game()
        listener.join()

if __name__ == '__main__':
    client = Cliente("Mankris")
    client.run()