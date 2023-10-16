import pygame
from config import *

img_sub = "./img/submarino.png"
img_des = "./img/destructor.png"
img_pat = "./img/patrulla.png"

class Barco:
    def __init__(self, size, img, pos):
        self.size = size
        self.estado = True
        self.girado = False #True -> Vertical, False -> Horizontal
        self.posIni = pos
        self.pos = pos
        self.coord = (-1,-1)
        self.arrastrando = False
        self.img = pygame.image.load(img).convert_alpha()
        self.partesRestantes = size

        self.surface = pygame.Surface((TILESIZE*size, TILESIZE))
        self.surface.fill((0,0,255))
        self.surface.set_alpha(0)
        self.rect = self.surface.get_rect()
        self.rect.x, self.rect.y = pos


    def girar(self, board):
        self.girado = not self.girado
        if board.moverBarco(self):
            self.surface = pygame.transform.rotate(self.surface, 90)
            self.img = pygame.transform.rotate(self.img, 90)
            self.rect = self.surface.get_rect()
            self.rect.x, self.rect.y = self.pos
        else:
            self.girado = not self.girado
            board.moverBarco(self)
    
    def recibirAtaque(self, board):
        if self.partesRestantes > 0:
            self.partesRestantes -= 1

        if self.partesRestantes == 0:
            self.hundir(board)

    def hundir(self, board):
        self.estado = False
        board.barcosRestantes()

class Submarino(Barco):
    def __init__(self, pos):
        super().__init__(3, img_sub, pos)

class Destructor(Barco):
    def __init__(self, pos):
        super().__init__(2, img_des, pos)

class Patrulla(Barco):
    def __init__(self, pos):
        super().__init__(1, img_pat, pos)