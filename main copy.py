import sys
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

LARGURA_JANELA = 1200
ALTURA_JANELA = 800

texturas = {}
# arquivo_textura, raio, distancia_do_sol, velocidade em torno do sol
PLANETAS = [
    ("mercurio.jpg", 1, 2.0, 4),
    ("venus.jpg",   3, 3.0, 1.5),
    ("terra.jpg",   7,  4.5, 1),
    ("marte.jpg",   1, 6.0, 0.5),
]

INDICE_TERRA = 2
INDICE_SATURNO = 5

RAIO_SCALE = 0.16     # raios dos planetas
DIST_SCALE = 3.0      # multiplica as distâncias

# estado da animação (tem que ser assim pra dar pra dar pra mudar no decorrer do codigo)
velocidade_tempo = 0.2
angulos = [0.0 for _ in range(len(PLANETAS))]
angulo_lua = 0.0
pausado = False

def carregar_textura(arquivo):
    img = Image.open(arquivo)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img_data = img.convert("RGBA").tobytes()
    largura, altura = img.size
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, largura, altura, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    return tex_id

def inicializar_texturas():
    global texturas
    arquivos = [p[0] for p in PLANETAS]
    arquivos += ["sol.jpg", "lua.png", "anelSaturno.png"]
    for f in arquivos:
        if f in texturas:
            continue
        texturas[f] = carregar_textura(f)
    print("texturas carregadas:", list(texturas.items()))

def posicionar_luz_no_sistema():
    # a posição da luz é definida em coordenadas do mundo
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    pos_luz = [0.0, 0.0, 0.0, 1]  # posição x, y, z, w (luz)
    glLightfv(GL_LIGHT0, GL_POSITION, pos_luz)
    glEnable(GL_LIGHTING) 
    glEnable(GL_LIGHT0) 

    glPopMatrix()

def desenhar_esfera_texturizada(tex_id, raio, horizontal=32, vertical=32):
    glEnable(GL_TEXTURE_2D) # Faz o que eu tinha falado antes de fixar a textura no planeta
    glBindTexture(GL_TEXTURE_2D, tex_id)
    quad = gluNewQuadric()
    gluQuadricTexture(quad, GL_TRUE)
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, raio, horizontal, vertical)
    glDisable(GL_TEXTURE_2D)

# MOUSE
angulo_x = 20.0
angulo_y = 0.0
zoom = -90.0
mouse_x = 0
mouse_y = 0
botao_mouse_pressionado = False

def inicializar_camera():
    global angulo_x, angulo_y, zoom
    angulo_x = 20.0
    angulo_y = 40.0
    zoom = -60.0

def aplicar_camera():
    glTranslatef(0.0, 0.0, zoom)
    glRotatef(angulo_x, 1.0, 0.0, 0.0)
    glRotatef(angulo_y, 0.0, 1.0, 0.0)

def evento_mouse(botao, estado, x, y):
    global botao_mouse_pressionado, mouse_x, mouse_y, zoom
    if botao == GLUT_LEFT_BUTTON:
        if estado == GLUT_DOWN:
            botao_mouse_pressionado = True
            mouse_x = x
            mouse_y = y
        else:
            botao_mouse_pressionado = False
    # scroll 3 cima, 4 baixo
    if botao == 3:
        zoom += 3.0
        glutPostRedisplay() # faz a tela redesenhar
    elif botao == 4:
        zoom -= 3.0
        glutPostRedisplay()

def evento_mouse_movimento(x, y):
    global mouse_x, mouse_y, angulo_x, angulo_y, botao_mouse_pressionado
    if botao_mouse_pressionado:
        dx = x - mouse_x
        dy = y - mouse_y
        angulo_y += dx * 0.2 # sensibilide, pega o dx para angulo_y porque gira em torno do eixo y
        angulo_x += dy * 0.2
        # limita ângulos pra não virar tudo de ponta cabeça
        if angulo_x > 89: angulo_x = 89
        if angulo_x < -89: angulo_x = -89
        mouse_x = x
        mouse_y = y
        glutPostRedisplay()

# ---------- Renderização ----------
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    #reset e aplica câmera
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    aplicar_camera()

    posicionar_luz_no_sistema()

    # sol desenhado sem iluminação pq a luz sai dele (teoricamente)
    glPushMatrix()
    glDisable(GL_LIGHTING)
    if texturas.get('sol.jpg', 0):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texturas['sol.jpg']) 
        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE)
        gluSphere(quad, 3.8, 32, 32)  # sol maior que planetas
        gluDeleteQuadric(quad)
        glDisable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    glPopMatrix()

    # desenha planetas usando escala definida (distância e raio adequados)
    for i, p in enumerate(PLANETAS): 
        arquivo, raio_raw, dist_raw, velocidade, = p 
        raio = raio_raw * RAIO_SCALE
        dist = dist_raw * DIST_SCALE

        glPushMatrix()
        # rotaciona em torno do Sol
        glRotatef(angulos[i], 0.0, 1.0, 0.0)
        # mas fica na distancia definida la em cima
        glTranslatef(dist, 0.0, 0.0)

        # rotação do planeta no próprio eixo
        glRotatef(30, 0.0, 1.0, 0.0)

        if i == INDICE_TERRA:
            desenhar_esfera_texturizada(texturas.get('terra.jpg', 0), raio)
            # lua orbitando
            glPushMatrix()
            glRotatef(angulo_lua, 0.0, 1.0, 0.0)
            glTranslatef((1 + raio_raw) * RAIO_SCALE + raio, 0.0, 0.0) # distancia da terra é 1 + r terra
            desenhar_esfera_texturizada(texturas.get('lua.png', 0), 0.27 * RAIO_SCALE)
            glPopMatrix()

        else:
            desenhar_esfera_texturizada(texturas.get(arquivo, 0), raio)

        glPopMatrix()

    glutSwapBuffers()

def idle():
    global angulos, angulo_lua
    if not pausado:
        for i, p in enumerate(PLANETAS):
            velocidade = p[3] 
            angulos[i] = (angulos[i] + velocidade * velocidade_tempo) % 360.0 # pega o angulo atual e adiciona a velocidade
        angulo_lua = (angulo_lua + 5.0 * velocidade_tempo) % 360.0 # a lua é vel fixa
        glutPostRedisplay()

# ---------- Teclado ----------
def teclado(tecla, x, y):
    global pausado, velocidade_tempo
    k = tecla.decode('utf-8') if isinstance(tecla, bytes) else tecla
    if k == '\x1b':  # ESC
        sys.exit(0)
    elif k == 'r':
        resetar()
    elif k == '+':
        velocidade_tempo *= 1.5
    elif k == '-':
        velocidade_tempo /= 1.5
    elif k == 'p':
        pausado = not pausado

def resetar():
    global angulos, angulo_lua, velocidade_tempo, pausado
    angulos = [0.0 for _ in range(len(PLANETAS))]
    angulo_lua = 0.0
    velocidade_tempo = 1.0
    pausado = False

def reshape(largura, altura):
    if altura == 0:
        altura = 1
    glViewport(0, 0, largura, altura)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(largura)/float(altura), 0.1, 2000.0)
    glMatrixMode(GL_MODELVIEW)

def init_gl():
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_NORMALIZE)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(LARGURA_JANELA, ALTURA_JANELA)
    glutCreateWindow(b"Sistema Solar")

    init_gl()
    inicializar_texturas()
    inicializar_camera()
    # funções de evento
    glutDisplayFunc(display) 
    glutIdleFunc(idle)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)

    glutMouseFunc(evento_mouse)
    glutMotionFunc(evento_mouse_movimento)

    glutMainLoop()

if __name__ == '__main__':
    main()
