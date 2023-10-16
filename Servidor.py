import json
import random
import time
import socket
import threading

import numpy as np

from queue import Queue

from config import *

class Ship:
    def __init__(self, _type, board, side=None, coord=[]):
        self.active = True
        self.side = side # vertical: 0 | horizontal: 1
        self._type = _type
        self.left = self.exc = 1 if self._type == 'p' else (2 if self._type == 'd' else 3)
        self.state = True
        self.coords = []
        if coord != []:
            for k in range(self.exc):
                if self.side: 
                    self.coords.append([coord[0], coord[1]+k])
                else:
                    self.coords.append([coord[0]+k, coord[1]])
            board.positions += self.coords
        else:
            self.random_coords(board)
    
    def random_coords(self, board):
        self.coords = []
        ret = False
        while not ret:
            ret = True
            self.side = np.random.random() < .5
            if self.side:
                x, y = random.randint(0, NUMTILES-1), random.randint(0, NUMTILES-self.exc)
            else:
                x, y = random.randint(0, NUMTILES-self.exc), random.randint(0, NUMTILES-1)
            for i in range(-1, 2):
                for j in range(-1, 2):
                    for k in range(self.exc):
                        if self.side:
                            ret &= not ([x+i, y+j+k] in board.positions)
                        else:
                            ret &= not ([x+i+k, y+j] in board.positions)
                        if not ret:
                            break
        for k in range(self.exc):
            if self.side: 
                self.coords.append([x, y+k])
            else:
                self.coords.append([x+k, y])
        board.positions += self.coords

    def takeDamage(self):
        if self.left > 0:
            self.left -= 1

        if self.left == 0:
            self.sink()

    def sink(self):
        self.state = False

class Board:
    def __init__(self):
        self.nt = NUMTILES
        self.board = np.zeros((self.nt, self.nt), dtype=int)
        self.barcos = []
        self.positions = []
        self.left = NUMBARCOS

class Game:
    def __init__(self, mode):
        self.player_a = None
        self.player_b = None
        self.mode = mode
        self.nt = NUMTILES

        self.board_a = Board()
        self.attck_a = np.zeros((self.nt, self.nt), dtype=int)
        self.left_a = 0
        self.name_a = ""

        self.board_b = Board()
        self.attck_b = np.zeros((self.nt, self.nt), dtype=int)
        self.left_b = 0
        self.name_b = ""

        self.turno = True
    

    def join_player(self, ships, pid, name):
        left = 0
        if self.player_a is None:
            self.player_a = pid
            board_x = self.board_a
            if name != None:
                self.name_a = name
        else:
            self.player_b = pid
            board_x = self.board_b
            if name != None:
                self.name_b = name

        for t, (x, y, s) in ships.items():
            ship = Ship(t, board_x, s, [x,y])
            board_x.barcos.append(ship)
            for k in range(ship.exc):
                if not s:
                    board_x.board[x+k, y] = 1
                else:
                    board_x.board[x, y+k] = 1
                left += 1

        if pid == self.player_a:
            self.left_a = left
        else:
            self.left_b = left

        if self.mode == 'ia':
            self.board_b.barcos = [Ship('p', self.board_b), Ship('d', self.board_b), Ship('s', self.board_b)]
            for barco in self.board_b.barcos:
                for x, y in barco.coords:
                    self.board_b.board[x, y] = 1
                    self.left_b += 1         

    def attack_coords(self, pid, coords):
        i, j = coords

        if pid == self.player_a and not self.turno:
            return False, None
        elif pid == self.player_b and self.turno:
            return False, None

        if(i > NUMTILES-1 or i < 0 or j > NUMTILES-1 or j < 0):
            return False, None

        if pid == self.player_a:
            board_x = self.board_b.board
            attck_x = self.attck_b
        else:
            board_x = self.board_a.board
            attck_x = self.attck_a

        if attck_x[i, j]:
            return False, None
        
        attck_x[i, j] = 1

        if board_x[i, j]:
            if pid == self.player_a:
                self.left_b -= 1
                for ship in self.board_b.barcos:
                    for coord in ship.coords:
                        if coord == [i,j]:
                            ship.takeDamage()
                            if not ship.state:
                                self.board_b.left -= 1
            else:
                self.left_a -= 1
                for ship in self.board_a.barcos:
                    for coord in ship.coords:
                        if coord == [i,j]:
                            ship.takeDamage()
                            if not ship.state:
                                self.board_a.left -= 1

            return True, True
        else:
            self.turno = not self.turno
        
        return True, False


    def random_ia_attack(self):
        while True:
            i, j = random.randint(0, self.nt-1), random.randint(0, self.nt-1)
            if not self.attck_a[i, j]:
                self.attck_a[i, j] = 1
                if self.board_a.board[i, j]:
                    self.left_a -= 1
                return [i, j], self.board_a.board[i, j]


    @classmethod
    def check_build(cls, ships):
        pos = []
        for t, (x, y, s) in ships.items():
            exc = 1 if t == 'p' else (2 if t == 'd' else 3)
            for k in range(exc):
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if (not s) and ([x+k+i, y+j] in pos):
                            return False
                        elif s and [x+i, y+k+j] in pos:
                            return False
            for k in range(exc):
                if not s:
                    pos.append([x+k, y])
                else:
                    pos.append([x, y+k])

        return True

class Server:
    ip = IP
    local_port = PORT
    buffer_size = 1024

    udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_server_socket.bind((ip, local_port))
    udp_server_socket.settimeout(1)

    print("Server up and listening...")

    CLIENT_TIMEOUT = TIMER

    def __init__(self):
        self.tasks = Queue()
        self.running = True
        self.games = {}
        self.pending_games = {}
        self.clients = {}


    def try_send(self, pid, dct):
        try:
            self.udp_server_socket.sendto(bytes(json.dumps(dct), 'utf-8'), pid)
            return True
        
        except:
            if pid in self.clients:
                self.clients.pop(pid)
            return False
        
    
    def join_player(self, pid, mode, ships, name):
        if not Game.check_build(ships):
            self.try_send(pid, {'action': 'b', 'status': 0})
            return

        self.clients[pid] = time.time()
        
        if mode: # un jugador
            game = Game('ia')
            game.join_player(ships, pid, name)
            self.games[pid] = game
            self.try_send(pid, {'action': 'b', 'status': 1, 'first': 1})

        else: # multiplayer
            if len(self.pending_games) == 0:
                game = Game('mp')
                game.join_player(ships, pid, name)
                self.games[pid] = game
                self.pending_games |= {pid: game}
            else:
                game = self.pending_games.pop(random.choice(list(self.pending_games.keys())))
                game.join_player(ships, pid, name)
                self.games[pid] = game
                self.try_send(game.player_a, {'action': 'b', 'status': 1, 'first': 1, 'name': game.name_b})
                self.clients[game.player_a] = time.time()
                self.try_send(game.player_b, {'action': 'b', 'status': 1, 'first': 0, 'name': game.name_a})
                self.clients[game.player_b] = time.time()
        
    def attack_pos(self, pid, coords):
        game = self.games.get(pid, None)
        if game is None:
            self.try_send(pid, {'action': 'd'})
            return
        status, effective = game.attack_coords(pid, coords)
        if status:
            if pid == game.player_a:
                left = game.board_b.left
            elif pid == game.player_b:
                left = game.board_a.left
            self.try_send(pid, {'action': 's', 'status': 1, 'effective': effective, 'left':left})
            if not effective:
                if game.turno:
                    self.clients[game.player_a] = time.time()
                elif game.mode == 'mp':
                    self.clients[game.player_b] = time.time()
            else:
                self.clients[pid] = time.time()
        else:
            self.try_send(pid, {'action': 's', 'status': 0})
            return
        if game.mode == 'ia':
            time.sleep(0.5)
            if game.left_b == 0:
                self.try_send(pid, {'action': 'l', 'win': 1})
                # self.games.pop(pid)
                return
            while not game.turno:
                ia_attack_pos, effect_ia = game.random_ia_attack()
                self.try_send(pid, {'action': 'a', 'status': int(effect_ia), 'position': ia_attack_pos})
                if game.left_a == 0:
                    self.try_send(pid, {'action': 'l', 'win': 0})
                    # self.games.pop(pid)
                if not int(effect_ia):
                    game.turno = not game.turno

        elif game.mode == 'mp':
            if pid == game.player_a:
                self.try_send(game.player_b, {'action': 'a', 'status': effective, 'position': coords})
            elif pid == game.player_b:
                self.try_send(game.player_a, {'action': 'a', 'status': effective, 'position': coords})
            # chequea termino
            if game.left_a == 0:
                self.try_send(game.player_a, {'action': 'l', 'win': 0})
                self.try_send(game.player_b, {'action': 'l', 'win': 1})
                self.games.pop(game.player_a)
                self.games.pop(game.player_b)
            elif game.left_b == 0:
                self.try_send(game.player_a, {'action': 'l', 'win': 1})
                self.try_send(game.player_b, {'action': 'l', 'win': 0})
                self.games.pop(game.player_a)
                self.games.pop(game.player_b)


    def disconnect_player(self, pid):
        game = self.games.get(pid, None)
        if game is None:
            self.try_send(pid, {'action': 'd'})
            return
        if self.pending_games.get(pid, None) is not None:
            self.pending_games.pop(pid)
        if game.mode == 'ia':
            game.board_b.positions = []
            self.try_send(pid, {'action': 'd'})
            self.games.pop(pid)
        elif game.mode == 'mp':
            if game.player_a is not None:
                self.try_send(game.player_a, {'action': 'd'})
                self.games.pop(game.player_a)
            if game.player_b is not None:
                self.try_send(game.player_b, {'action': 'd'})
                self.games.pop(game.player_b)


    def run(self):
        listener = threading.Thread(target=self.listen)
        monitor = threading.Thread(target=self.monitor)

        listener.start()
        monitor.start()
        try:
            self.run_tasks()
        finally:
            self.running = False
        listener.join()
        monitor.join()

    def run_tasks(self):
        while True:
            while True:
                try:
                    task = self.tasks.get(True, 1)
                    break
                except KeyboardInterrupt:
                    raise Exception('Shutdown')
                except:
                    pass

            task[0](*task[1])


    def monitor(self):
        while self.running:
            for game in list(self.games.values()):
                for player in (game.player_a, game.player_b):
                    if (player is None) or (player in self.pending_games):
                        continue
                    if (player == game.player_a and not game.turno) or \
                            (player == game.player_b and game.turno):
                        continue
                    if time.time() - self.clients[player] > self.CLIENT_TIMEOUT:
                        self.tasks.put([self.disconnect_player, (player,)])

            time.sleep(0.5)


    def listen(self):
        while self.running:
            # escucha con timeout, si recibe algo corta bucle
            while self.running:
                try:
                    content, address = self.udp_server_socket.recvfrom(self.buffer_size)
                    content = json.loads(content.decode("utf-8"))
                    break

                except socket.timeout: 
                    pass

            print(f"{address}: {content}")

            self.clients[address] = time.time()

            match content['action']:
                case 'c':
                    self.tasks.put([self.try_send, (address, {'action': 'c', 'status': 1})])

                case 'b':
                    self.tasks.put([self.join_player, (address, content['bot'], content['ships'], content.get('name',None))])

                case 's':
                    self.tasks.put([self.attack_pos, (address, content['position'])])

                case 'd':
                    self.tasks.put([self.disconnect_player, (address,)])


if __name__ == '__main__':
    server = Server()
    server.run()
