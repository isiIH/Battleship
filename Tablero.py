from Barco import *
from config import *

# 0 = Celda vacía
# 1 = Barco colocado
# 2 = Impacto
# 3 = Fallo

class Tablero:
    def __init__(self, ntiles, boardPos):
        self.tiles = [[0 for _ in range(ntiles)] for _ in range(ntiles)]
        self.barcos = []
        self.boardPos = boardPos
        self.nBarcos = NUMBARCOS
        self.posAttack = None
    
    def colocarBarco(self, barco : Barco, coordenadas):
        (x,y) = coordenadas
        if(x > NUMTILES-1 or x < 0 or y > NUMTILES-1 or y < 0):
            return False
        #Si el barco está en posición vertical
        if(barco.girado):
            #Verifica que esté dentro de los límites
            if(x+barco.size > NUMTILES):
                return False
            #Verifica que no haya otros barcos alrededor de la casilla
            for i in range(max(0,x-1),min(NUMTILES,x+barco.size+1)):
                for j in range(max(0,y-1),min(NUMTILES,y+2)):
                    if(self.tiles[i][j]):
                        return False
            #Posiciona el barco
            for i in range(x,x+barco.size):
                self.tiles[i][y] = 1
        #Si el barco está en posición horizontal
        else:
            #Verifica que esté dentro de los límites
            if(y+barco.size > NUMTILES):
                return False
            #Verifica que no haya otros barcos alrededor de la casilla
            for i in range(max(0,x-1),min(NUMTILES,x+2)):
                for j in range(max(0,y-1),min(NUMTILES,y+barco.size+1)):
                    if(self.tiles[i][j]):
                        return False
            #Posiciona el barco
            for i in range(y,y+barco.size):
                self.tiles[x][i] = 1

        #Exito
        barco.coord = (x,y)
        barco.rect.x, barco.rect.y = barco.pos = (y*TILESIZE+self.boardPos[0], x*TILESIZE+self.boardPos[1])
        return True
    
    def eliminarBarco(self, barco : Barco):
        row,col = barco.coord
        if(row > NUMTILES-1 or row < 0 or col > NUMTILES-1 or col < 0):
            return
        if(barco.girado):
            for i in range(row,row+barco.size):
                self.tiles[i][col] = 0
        else:
            for i in range(col,col+barco.size):
                self.tiles[row][i] = 0
    
    def moverBarco(self, barco : Barco):
        b_x, b_y = self.boardPos
        barco.rect.x = (barco.rect.x // TILESIZE )* TILESIZE + 20
        barco.rect.y = (barco.rect.y// TILESIZE) * TILESIZE + 10
        row = (barco.rect.y-b_y) // TILESIZE
        col = (barco.rect.x-b_x) // TILESIZE
        
        if not self.colocarBarco(barco, (row,col)):
            barco.rect.x, barco.rect.y = barco.pos
            row = (barco.rect.y-b_y) // TILESIZE
            col = (barco.rect.x-b_x) // TILESIZE
            self.colocarBarco(barco, (row,col))
            return False
        barco.pos = (barco.rect.x, barco.rect.y)
        return True
    
    def actualizarTablero(self, effective):
        row, col = self.posAttack
        if effective:
            self.tiles[row][col] = 2  #Impacto
        else:
            self.tiles[row][col] = 3  #Fallo

    def realizarAtaque(self, position, effective):
        row, col = position
        if effective:
            self.tiles[row][col] = 2  #Impacto
            #Recibir ataque
            for barco in self.barcos:
                for s in range(barco.size):
                    if(barco.girado):
                        if barco.coord[0]+s == row and barco.coord[1] == col:
                            barco.recibirAtaque(self)
                    else:
                        if barco.coord[0] == row and barco.coord[1]+s == col:
                            barco.recibirAtaque(self)
                    
        else:
            self.tiles[row][col] = 3  #Fallo
    
    def barcosRestantes(self):
        self.nBarcos -= 1