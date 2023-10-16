import pygame
from random import randint
from config import *
from Tablero import Tablero
from Barco import *

pygame.init()
clock = pygame.time.Clock() 

#ESTADO
# 0 -> Desconectado
# 1 -> Preparación: Jugador coloca sus barcos y elige single o multiplayer
# 2 -> Jugando partida
# 3 -> Finalización de la partida

class Game:
    def __init__(self, client):
        self.win = pygame.display.set_mode((WINDOWWIDTH,WINDOWHEIGHT))
        pygame.display.set_caption("Battleship")

        #Imagenes
        self.img_impacto = pygame.image.load("./img/impacto.png").convert_alpha()
        self.img_apuntar = pygame.image.load("./img/apuntar.png").convert_alpha()
        self.img_agua = pygame.image.load("./img/agua.png").convert_alpha()

        #Botones
        self.connect = pygame.Rect(WINDOWWIDTH//2+BOARDSIZE//2-30,WINDOWHEIGHT//2+80,185,40)

        self.single_button = pygame.Rect(WINDOWWIDTH//2+BOARDSIZE//2, WINDOWHEIGHT//2,120,40)
        self.multi_button = pygame.Rect(WINDOWWIDTH//2+BOARDSIZE//2, WINDOWHEIGHT//2+50,120,40)
        self.disc_button = pygame.Rect(WINDOWWIDTH//2+BOARDSIZE//2-2, WINDOWHEIGHT//2+100,125,40)

        self.volver_button = pygame.Rect(BOARDSIZE+30,WINDOWHEIGHT-50,135,40)
        self.salir_button = pygame.Rect(WINDOWWIDTH//2+BOARDSIZE//2+20, WINDOWHEIGHT//2+50,70,40)

        self.reset_button = pygame.Rect(BOARDSIZE + 150,30,80,40)
        self.random_button = pygame.Rect(BOARDSIZE + 150,80,100,40)

        #input
        self.input_ip = pygame.Rect(WINDOWWIDTH//2+BOARDSIZE//2-30,WINDOWHEIGHT//2,185,30) 
        self.active_ip = False
        self.text_ip = IP
        self.color_ip = WHITE

        self.input_port = pygame.Rect(WINDOWWIDTH//2+BOARDSIZE//2-30,WINDOWHEIGHT//2+40,185,30) 
        self.active_port = False
        self.text_port = f"{PORT}"
        self.color_port = WHITE

        #Client
        self.client = client
        self.turno = None
        self.countdown_timer = None
        self.wait = False

        #Enemy
        self.enemy = "Campo Enemigo"
        self.show = False

        #Bot
        self.mode = None

        #Board
        self.board1 = Tablero(NUMTILES, (20,40))
        self.board2 = Tablero(NUMTILES, (WINDOWWIDTH - BOARDSIZE - 20, 40))

        #Estado
        self.estado = 0 #Desconectado del servidor

        #Mensajes
        self.winMessage = ""
        self.msg = ""

        self.run = False


    def barcosAleatorios(self, board):
        for barco in board.barcos:
            board.eliminarBarco(barco)
            exito = board.colocarBarco(barco, (randint(0,NUMTILES-1), randint(0,NUMTILES-1)))
            while not exito:
                exito = board.colocarBarco(barco, (randint(0,NUMTILES-1), randint(0,NUMTILES-1)))
            girar = randint(0,1)
            if girar:
                board.eliminarBarco(barco)
                barco.girar(board)

    def colocarBarcos(self, board):
        # for i in range(1,15):
        #     if(i < 4):
        #         board.barcos.append(Submarino((BOARDSIZE+50, i*30)))
        #     elif i < 9:
        #         board.barcos.append(Destructor((BOARDSIZE+50, i*30)))
        #     else:
        #         board.barcos.append(Patrulla((BOARDSIZE+50, i*30)))

        board.barcos.append(Submarino((BOARDSIZE+50, 30)))
        board.barcos.append(Destructor((BOARDSIZE+50, 60)))
        board.barcos.append(Patrulla((BOARDSIZE+50, 90)))

    def __call__(self):

        self.colocarBarcos(self.board1)
        self.colocarBarcos(self.board2)

        self.run = True
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False             
                    self.client.enviarAServidor({'action': 'd', 'bot' : 0, 'ships' : {}, 'position': []})

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.estado == 0:
                        if self.connect.collidepoint(event.pos):
                                if self.text_port == "" or int(self.text_port)<0 or int(self.text_port)>65535 or len(self.text_ip.split('.')) != 4 or self.text_ip[-1] == ".":
                                    self.msg = "Wrong ip or port"
                                else:
                                    self.client.conectarAServidor(self.text_ip, int(self.text_port))

                        if self.input_ip.collidepoint(event.pos): 
                            self.active_ip = True
                        else: 
                            self.active_ip = False

                        if self.input_port.collidepoint(event.pos): 
                            self.active_port = True
                        else: 
                            self.active_port = False

                    if self.estado == 1:
                        if self.mode == None:
                            #Mover y girar barcos
                            for barco in self.board1.barcos:
                                if barco.rect.collidepoint(event.pos):
                                    offset_x, offset_y = barco.rect.x - event.pos[0], barco.rect.y - event.pos[1]

                                    if event.button == 3:
                                        self.board1.eliminarBarco(barco)
                                        barco.girar(self.board1)
                                    else:
                                        barco.arrastrando = True

                            #BOTON PARA RESETEAR BARCOS
                            if self.reset_button.collidepoint(event.pos):
                                self.clearWindow(1)

                            #BOTON PARA RANDOMIZAR
                            if self.random_button.collidepoint(event.pos):
                                self.barcosAleatorios(self.board1)

                            #BOTON PARA JUGAR
                            if self.single_button.collidepoint(event.pos):
                                self.setMode(1)
                            elif self.multi_button.collidepoint(event.pos):
                                self.setMode(0)
                                self.wait = True

                        else:
                            if self.wait and self.salir_button.collidepoint(event.pos):
                                self.client.enviarAServidor({'action': 'd', 'bot' : 0, 'ships' : {}, 'position': []})
                                self.wait = False

                        if self.disc_button.collidepoint(event.pos):
                            self.clearWindow(0)

                    if self.estado == 2:
                        #Recibir ataque
                        for barco in self.board2.barcos:
                            if barco.rect.collidepoint(event.pos):
                                barco.recibirAtaque(self.board2, event.pos)

                    if self.estado > 0:
                        #BOTON PARA VOLVER A JUGAR
                        if self.volver_button.collidepoint(event.pos):
                            self.client.enviarAServidor({'action': 'd', 'bot' : 0, 'ships' : {}, 'position': []})

                #Arrastrar un barco
                if event.type == pygame.MOUSEBUTTONUP:
                    if self.estado == 1:
                        for barco in self.board1.barcos:
                            if barco.arrastrando:
                                barco.arrastrando = False
                                self.board1.eliminarBarco(barco)
                                self.board1.moverBarco(barco)

                if self.estado == 0 and event.type == pygame.KEYDOWN: 
                    key = event.key
                    if self.active_ip:
                        if (48 <= key <= 57 and (int(self.text_ip.split('.')[-1]+event.unicode) < 256 and not self.text_ip.split('.')[-1].startswith('0') if len(self.text_ip) > 0 and self.text_ip[-1] != '.' else 1)) or (key == 46 and len(self.text_ip.split('.')) < 4 and self.text_ip != '' and self.text_ip[-1] != '.'): # 1-10 o '.'
                            self.text_ip += event.unicode
                        elif key == pygame.K_BACKSPACE:
                            self.text_ip = self.text_ip[:-1]
                    if self.active_port:
                        if 48 <= key <= 57 and len(self.text_port) < 6: # 1-10 o '.'
                            self.text_port += event.unicode
                        elif key == pygame.K_BACKSPACE:
                            self.text_port = self.text_port[:-1]

                #ATAQUES
                if self.estado == 2 and event.type == pygame.MOUSEBUTTONDOWN: #Jugando
                    self.atacar()
            #MOVER BARCO CON MOUSE
            if self.mode == None and self.estado == 1:
                x, y = pygame.mouse.get_pos()
                for barco in self.board1.barcos:
                    if barco.arrastrando:
                        barco.rect.x = x + offset_x
                        barco.rect.y = y + offset_y

            self.draw_win()

            pygame.display.update()
            clock.tick(60)

    def draw_win(self):
        self.win.fill(FONDO)

        if(self.show and self.estado > 1):
            self.text(24, f"Barcos restantes: {self.board1.nBarcos}", (BOARDSIZE // 2 - 70,BOARDSIZE+50))
            self.text(24, f"Barcos restantes: {self.board2.nBarcos}", (WINDOWWIDTH - BOARDSIZE // 2 - 70,BOARDSIZE+50))
        
        #Barcos
        for barco in self.board1.barcos:
            self.win.blit(barco.img, (barco.rect.x, barco.rect.y))
        for barco in self.board2.barcos:
            if not barco.estado:
                self.win.blit(barco.img, (barco.rect.x, barco.rect.y))

        #Tablero
        self.text(36, self.client.nombre, (20,10))

        turn_a = self.turno
        if self.turno is not None:
            turn_b = not self.turno
        else:
            turn_b = self.turno
        
        self.draw_board(self.board1, turn_b)
        if self.estado > 1:
            self.text(36, self.enemy, (WINDOWWIDTH - BOARDSIZE - 20,10))
            self.draw_board(self.board2, turn_a)

        #Botones
        if self.estado == 1:
            if self.mode == None:
                self.createButton('Reset', self.reset_button, RED)
                self.createButton('Random', self.random_button, GREEN)
                self.text(24, "Seleccione el modo de juego:", (WINDOWWIDTH//2+BOARDSIZE//2-50,WINDOWHEIGHT//2-30))
                self.createButton('SinglePlayer', self.single_button, BLUE, 24)
                self.createButton('MultiPlayer', self.multi_button, BLUE, 24)
                self.createButton('Desconectar', self.disc_button, RED, 24)
            elif self.wait:
                self.text(24, "Waiting for players...", (WINDOWWIDTH//2+BOARDSIZE//2-20,WINDOWHEIGHT//2-30), RED2)
                self.createButton('Salir', self.salir_button, RED, 24)

        #Servidor
        if self.estado == 0:
            self.text(24, "IP:", (WINDOWWIDTH//2+BOARDSIZE//2-60,WINDOWHEIGHT//2+10), BLACK)
            self.color_ip = WHITE2 if self.active_ip else WHITE
            self.text(24, "PORT:", (WINDOWWIDTH//2+BOARDSIZE//2-88,WINDOWHEIGHT//2+50), BLACK)
            self.color_port = WHITE2 if self.active_port else WHITE
            self.createButton(self.text_ip, self.input_ip, self.color_ip, 24, BLACK)
            self.createButton(self.text_port, self.input_port, self.color_port, 24, BLACK)
            self.createButton('Conectar al servidor', self.connect, BLUE, 24)
            self.text(24, self.msg, (WINDOWWIDTH//2+BOARDSIZE//2-25,WINDOWHEIGHT//2+130), RED2)

        #Timer
        if self.estado == 2:
            current_time = pygame.time.get_ticks()
            remaining_time = max(0, (self.countdown_timer - current_time) // 1000)
            self.text(36, str(remaining_time), (WINDOWWIDTH//2-10, 40), BLACK)

        if self.estado == 3:
            self.showText(self.winMessage)
        if self.estado > 1:
            self.createButton('Salir del juego', self.volver_button, BLUE, 24)


    def draw_board(self, board : Tablero, turno):
        win_x, win_y = board.boardPos
        for row in range(NUMTILES):
            for col in range(NUMTILES):
                #PLAYER
                rect = pygame.Rect(win_x + col * TILESIZE, win_y + row * TILESIZE, TILESIZE, TILESIZE)
                
                # if board.tiles[row][col] == 1:
                #     pygame.draw.rect(self.win, RED, rect)
                if board.tiles[row][col] == 2: #Impacto
                    # pygame.draw.rect(win, RED, rect)
                    self.win.blit(self.img_impacto, (rect.x, rect.y))
                elif board.tiles[row][col] == 3: #Fallo
                    # pygame.draw.rect(win, BLUE, rect)
                    self.win.blit(self.img_agua, (rect.x, rect.y))

                # Comprobar si el mouse está sobre la casilla actual
                x, y = pygame.mouse.get_pos()
                if rect.collidepoint(x, y):
                    self.win.blit(self.img_apuntar, (rect.x, rect.y))

                border_color = BLUE

                # Dibujar el borde de la casilla
                pygame.draw.rect(self.win, border_color, rect, 2)

        if turno is not None:
            if turno:
                border_color = RED
            rect = pygame.Rect(win_x, win_y, BOARDSIZE, BOARDSIZE)
            pygame.draw.rect(self.win, border_color, rect, 3)

    def atacar(self):
        #JUGADOR
        win_x, win_y = self.board2.boardPos
        x, y = pygame.mouse.get_pos()
        row = (y-win_y) // TILESIZE
        col = (x-win_x) // TILESIZE

        if(row > NUMTILES-1 or row < 0 or col > NUMTILES-1 or col < 0):
            return
        
        self.board2.posAttack = (row,col)
    
        self.client.enviarAServidor({'action': 's', 'bot' : self.mode, 'ships' : {}, 'position': [row,col]})

    def showText(self, message):
        font = pygame.font.Font('freesansbold.ttf', 32)
        text = font.render(message, True, BLACK, BLUE)
        textRect = text.get_rect()
        textRect.center = (WINDOWWIDTH // 2, WINDOWHEIGHT // 2)
        self.win.blit(text, textRect)

    def createButton(self, text, button, color, fs=24, tc=WHITE):
        font = pygame.font.SysFont('Roboto',fs,bold=False)
        surf = font.render(text,True,tc)
        pygame.draw.rect(self.win, color, button)
        self.win.blit(surf,(button.x+15, button.y+12))

    def text(self, fweight, texto, pos, color=BLACK):
        font = pygame.font.SysFont('Roboto',fweight,bold=False)
        text = font.render(texto, True, color)
        textRect = text.get_rect()
        textRect.x, textRect.y = pos
        self.win.blit(text,textRect)

    def setState(self, estado):
        self.estado = estado

    def clearWindow(self, estado):
        self.msg = ""
        self.mode = None
        self.turno = None
        self.board1 = Tablero(NUMTILES, (20,40))
        self.board2 = Tablero(NUMTILES, (WINDOWWIDTH - BOARDSIZE - 20, 40))

        self.colocarBarcos(self.board1)
        self.colocarBarcos(self.board2)
        self.estado = estado

    def setMode(self, mode):
        jugar = True
        for barco in self.board1.barcos:
            if barco.coord == (-1,-1):
                jugar = False
        if jugar:
            self.mode = mode
            girado = lambda x: 0 if x else 1

            json = {'action': 'b', 'bot' : self.mode, 'ships' : {
                'p':[self.board1.barcos[2].coord[0],self.board1.barcos[2].coord[1],girado(self.board1.barcos[2].girado)],
                'd':[self.board1.barcos[1].coord[0],self.board1.barcos[1].coord[1],girado(self.board1.barcos[1].girado)],
                's':[self.board1.barcos[0].coord[0],self.board1.barcos[0].coord[1],girado(self.board1.barcos[0].girado)]
                }, 'position': [], 'name':self.client.nombre}
            
            self.client.enviarAServidor(json)

    def reset_timer(self):
        self.countdown_timer = pygame.time.get_ticks() + (TIMER+1) * 1000