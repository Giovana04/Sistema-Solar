from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

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
    