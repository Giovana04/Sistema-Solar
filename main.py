from tkinter import Image
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import support

# variáveis globais 



def load_texture_with_pillow(texture_path):
        image = Image.open(texture_path)
        image_data = image.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM).tobytes()
        width, height = image.size
        image.close()
        return image_data, width, height


def drawSphereWithTexture(texture_id, x,y,z, raio, r):
    glRotatef(r, 0.1, 5, 0)
    glTranslatef(x,y,z)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    sphere = gluNewQuadric()
    gluQuadricTexture(sphere, GL_TRUE) 
    gluQuadricNormals(sphere, GLU_SMOOTH)
    # os 32 são o quão detalhada vai ser a esfera! Quanto menor for, mais quadrado ela vai ser, 
    # mas caso for grande demais, vai ser meio pesado.
    gluSphere(sphere, raio, 32, 32)

    gluDeleteQuadric(sphere)

def addTexture(path):
    image_data, w, h = support.load_texture_with_pillow(path)
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    return texture_id
def update(r):
    # atualiza o array da rotação de cada planeta! E verifica se não ultrapassou em 360 graus, o maximo
    for i in range(len(r)):
      
        r[i] += 10
        if (r[i] > 360.0):
            r[i] -= 360.0
    return r
def drawDisk(inner, outer, slices, loops, x,y,z):
    glTranslatef(x,y,z)
    glRotatef(70, 6, 5, 0)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, addTexture("anelSaturno.png"))
    quad =  gluNewQuadric()
    gluQuadricTexture(quad, GL_TRUE) 
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluDisk(quad, inner, outer, slices, loops)
def drawFunc(rotacaoPlanetas):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
  
    glPushMatrix()
    # primeiro paramentro: o quão distante o planeta está do centro! O segundo é a altura comparada ao centro, e o outro é a distancia ao centro
    # o quarto muda o tamanho da esfera! E o ultimo é a rotação! Na logica atual, ambos planetas tão com a mesma rotação, mas dá pra alterar depois pra eles terem rotação mais realista
    support.drawSphereWithTexture(addTexture("netuno.png"), 0.8,0 ,0, 0.05, rotacaoPlanetas[1])
    glPopMatrix()
  
    glPushMatrix()
    support.drawSphereWithTexture(addTexture("urano.png"), 0.6,0 ,0, 0.05, rotacaoPlanetas[0])
    glPopMatrix()
  
    glPushMatrix()
    support.drawSphereWithTexture(addTexture("saturno.png"), 0.2 ,0 ,0, 0.1, 0)
    glPopMatrix()
  
    glPushMatrix()
    support.drawSphereWithTexture(addTexture("jupiter.png"), -0.3 ,0 ,0, 0.2, 0)
    glPopMatrix()
  
    glPushMatrix()
    drawDisk(0.15,0.25,20,10, 0.2,0,0)
    glPopMatrix()
  
    glutSwapBuffers()
    rotacaoPlanetas = update(rotacaoPlanetas)
  
def init():
 
    glClearColor(0.0,0.0,0.0,1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glDepthFunc(GL_LEQUAL)
    glShadeModel(GL_SMOOTH)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST) 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glPushMatrix()
  
def main():
   # cada pos do array simboliza um planeta, entao teria mais posicoes quando tiver todos! 
   # Só deixei 2 pq nesse momento, saturno e jupiter tao no lugar do sol basicamente 
    rotacaoPlanetas = [0,0]
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(400, 400)
  
    glutCreateWindow(b"first")
    init()
    glutDisplayFunc(lambda : drawFunc(rotacaoPlanetas))
    glutIdleFunc(lambda : drawFunc(rotacaoPlanetas))
    glutMainLoop()
main()