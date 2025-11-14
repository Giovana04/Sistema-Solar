import sys
import math
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

LARGURA_JANELA = 1200
ALTURA_JANELA = 800

INDICE_TERRA = 2
INDICE_SATURNO = 5

texturas = {}
# arquivo_textura, raio (unscaled), distancia_do_sol (unscaled), velocidade angular, inclinação
PLANETAS = [
    ("mercurio.jpg", 0.38, 2.0, 4.15, 0.0), # 1
    ("venus.jpg",    0.95, 3.0, 1.62, 0.0), # 2
    ("terra.jpg",    1.0,  4.5, 1.0,  0.0), # 3
    ("marte.jpg",    0.53, 6.0, 0.53, 0.0), # 4
    ("jupiter.png",  11.2, 8.5, 0.08, 0.0), # 5
    ("saturno.png",  9.45, 11.0,0.03, 0.0), # 6
    ("urano.png",    4.0,  13.5,0.011,0.0), # 7
    ("netuno.png",   3.88, 16.0,0.006,0.0)  # 8
]

RAIO_SCALE = 0.16 # escala de raio dos planetas
DIST_SCALE = 3.0 # escala de distância dos planetas

# estado da animação (tem que ser assim pra dar pra dar pra mudar no decorrer do codigo)
velocidade_tempo = 2.0
angulos = [0.0 for _ in range(len(PLANETAS))] # ângulos atuais dos planetas
angulo_lua = 0.0
pausado = False

# ---------- Câmera (mouse e foco) ----------
angulo_x = 20.0
angulo_y = 0.0
zoom = -60.0
mouse_x = 0
mouse_y = 0
botao_mouse_pressionado = False
planeta_foco = -1 # -1 = Sol (origem), 0 = Mercurio, 1 = Venus...

def inicializar_camera():
    global angulo_x, angulo_y, zoom, planeta_foco
    angulo_x = 20.0
    angulo_y = 40.0
    zoom = -60.0
    planeta_foco = -1 # Foco no sol

def aplicar_camera():
    # 1. Aplica zoom e rotação (mouse)
    # 2. gira o mundo para que o planeta focado fique no centro da rotação.
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # 1. Calcula o PONTO DE FOCO (tx, ty, tz)
    tx, ty, tz = 0.0, 0.0, 0.0
    if planeta_foco >= 0 and planeta_foco < len(PLANETAS):
        p = PLANETAS[planeta_foco]
        dist = p[2] * DIST_SCALE
        rad = math.radians(angulos[planeta_foco])
        
        # Esta matemática deve ser IDÊNTICA à transformação
        # usada para desenhar o planeta
        tx = dist * math.cos(rad)
        tz = -dist * math.sin(rad) # glRotatef/glTranslatef resulta em -sin

    # 2. Aplica transformações de câmera (mouse)
    glTranslatef(0.0, 0.0, zoom)
    glRotatef(angulo_x, 1.0, 0.0, 0.0)
    glRotatef(angulo_y, 0.0, 1.0, 0.0)
    
    # 3. Translada o MUNDO INTEIRO
    # O oposto do ponto de foco. Isso move o mundo
    # para que o ponto (tx, ty, tz) fique em (0,0,0) ANTES
    # das rotações de câmera.
    glTranslatef(-tx, -ty, -tz)


def evento_mouse(botao, estado, x, y):
    global botao_mouse_pressionado, mouse_x, mouse_y, zoom
    if botao == GLUT_LEFT_BUTTON:
        if estado == GLUT_DOWN:
            botao_mouse_pressionado = True
            mouse_x = x
            mouse_y = y
        else:
            botao_mouse_pressionado = False
    if botao == 3: # scroll up
        zoom += 3.0
        if zoom > -5.0: zoom = -5.0 # Limite de zoom in
        glutPostRedisplay()
    elif botao == 4: # scroll down
        zoom -= 3.0
        if zoom < -500.0: zoom = -500.0 # Limite de zoom out
        glutPostRedisplay()

def evento_mouse_movimento(x, y):
    global mouse_x, mouse_y, angulo_x, angulo_y, botao_mouse_pressionado
    if botao_mouse_pressionado:
        dx = x - mouse_x
        dy = y - mouse_y
        angulo_y += dx * 0.3
        angulo_x += dy * 0.3
        if angulo_x > 89.0: angulo_x = 89.0
        if angulo_x < -89.0: angulo_x = -89.0
        mouse_x = x
        mouse_y = y
        glutPostRedisplay()

# ---------- Texturas ----------
def carregar_textura(arquivo):
    try:
        img = Image.open(arquivo)
    except Exception as e:
        print(f"Erro ao abrir textura {arquivo}: {e}")
        return 0
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
    arquivos += ["sol.jpg", "lua.png", "anelSaturno.png", "estrelas.png"]
    for f in arquivos:
        if f in texturas: continue
        texturas[f] = carregar_textura(f)
    print("Texturas carregadas (0 = falha):", list(texturas.items()))

# ---------- Luz ----------
def posicionar_luz_no_sistema():
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    pos_luz = [0.0, 0.0, 0.0, 1.0]  # Luz no centro do sistema (Sol)
    glLightfv(GL_LIGHT0, GL_POSITION, pos_luz)
    glPopMatrix()

def configurar_luz():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

# ---------- Desenho ----------
def desenhar_esfera_texturizada(tex_id, raio, slices=48, stacks=24):
    if tex_id is None or tex_id == 0:
        quad = gluNewQuadric()
        gluSphere(quad, raio, slices, stacks)
        gluDeleteQuadric(quad)
        return
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    quad = gluNewQuadric()
    gluQuadricTexture(quad, GL_TRUE)
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, raio, slices, stacks)
    gluDeleteQuadric(quad)
    glDisable(GL_TEXTURE_2D)

def desenhar_anel(tex_id, raio_interno, raio_externo, fatias=200):
    if tex_id is None or tex_id == 0:
        return
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Desabilita luz para o anel ficar sempre visível (opcional)
    glPushAttrib(GL_ENABLE_BIT)
    glDisable(GL_LIGHTING)
    
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(fatias + 1):
        theta = (2.0 * math.pi * i) / fatias
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        u = i / float(fatias)
        glTexCoord2f(u, 1.0)
        glVertex3f(raio_externo * cos_t, 0.0, raio_externo * sin_t)
        glTexCoord2f(u, 0.0)
        glVertex3f(raio_interno * cos_t, 0.0, raio_interno * sin_t)
    glEnd()
    
    glPopAttrib()
    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)

def desenhar_orbitas():
    # NOVIDADE: Desenha as linhas de órbita
    glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT) # Salva estado da luz e cor
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glColor3f(0.6, 0.6, 0.6) # Cor cinza para as órbitas

    for p in PLANETAS:
        dist = p[2] * DIST_SCALE
        glBegin(GL_LINE_LOOP)
        segmentos = 100
        for i in range(segmentos):
            theta = 2.0 * math.pi * float(i) / float(segmentos)
            x = dist * math.cos(theta)
            # A matemática DEVE ser idêntica à da câmera e do planeta
            z = -dist * math.sin(theta) 
            glVertex3f(x, 0.0, z)
        glEnd()
    glPopAttrib() # Restaura estado


# ---------- Renderização ----------
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # MODELMODE: reset e aplica câmera (que agora sabe sobre o foco)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    aplicar_camera()

    # Luz
    posicionar_luz_no_sistema()
    configurar_luz()

    # Fundo de estrelas
    if texturas.get("estrelas.png", 0):
        glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST) # Desenha por trás de tudo
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity() # Desenha relativo à tela, não ao mundo
        
        # O ideal é um skybox, mas um quad grande funciona
        glTranslatef(0.0, 0.0, -450.0) # BEM longe
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texturas["estrelas.png"])
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex3f(-800, -600, 0)
        glTexCoord2f(1,0); glVertex3f(800, -600, 0)
        glTexCoord2f(1,1); glVertex3f(800, 600, 0)
        glTexCoord2f(0,1); glVertex3f(-800, 600, 0)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        
        glPopMatrix()
        glPopAttrib() # Restaura iluminação e depth test


    # *** NOVIDADE ***: Desenha as órbitas
    desenhar_orbitas()

    # Sol (sem iluminação, emissivo)
    glPushMatrix()
    glDisable(GL_LIGHTING)
    desenhar_esfera_texturizada(texturas.get('sol.jpg', 0), 3.8, 48, 24)
    glEnable(GL_LIGHTING)
    glPopMatrix()

    # Planetas (com iluminação)
    for i, p in enumerate(PLANETAS):
        arquivo, raio_raw, dist_raw, velocidade, inclinacao = p
        raio = raio_raw * RAIO_SCALE
        dist = dist_raw * DIST_SCALE

        glPushMatrix()
        
        # 1. Rotaciona a órbita
        # A matemática aqui (glRotate -> glTranslate) deve bater
        # com a da câmera e das linhas de órbita.
        glRotatef(angulos[i], 0.0, 1.0, 0.0)
        # 2. Move para a distância
        glTranslatef(dist, 0.0, 0.0)

        # Rotação do planeta (visual)
        glRotatef(30, 0.0, 1.0, 0.0)

        if i == INDICE_TERRA:
            desenhar_esfera_texturizada(texturas.get('terra.jpg', 0), raio)
            # lua
            glPushMatrix()
            glRotatef(angulo_lua, 0.0, 1.0, 0.0)
            glTranslatef((0.8 + raio_raw) * RAIO_SCALE + raio, 0.0, 0.0)
            desenhar_esfera_texturizada(texturas.get('lua.png', 0), 0.27 * RAIO_SCALE)
            glPopMatrix()

        elif i == INDICE_SATURNO:
            desenhar_esfera_texturizada(texturas.get('saturno.png', 0), raio)
            glPushMatrix()
            glRotatef(20, 1.0, 0.0, 0.0)
            desenhar_anel(texturas.get('anelSaturno.png', 0), raio * 1.25, raio * 2.7)
            glPopMatrix()

        else:
            desenhar_esfera_texturizada(texturas.get(arquivo, 0), raio)

        glPopMatrix()

    glutSwapBuffers()

# ---------- Animação ----------
def idle():
    global angulos, angulo_lua
    if not pausado:
        for i, p in enumerate(PLANETAS):
            velocidade = p[3]
            angulos[i] = (angulos[i] + velocidade * velocidade_tempo) % 360.0
        angulo_lua = (angulo_lua + 5.0 * velocidade_tempo) % 360.0
        glutPostRedisplay()

# ---------- Teclado ----------
def teclado(tecla, x, y):
    global pausado, velocidade_tempo, planeta_foco
    k = tecla.decode('utf-8') if isinstance(tecla, bytes) else tecla
    
    if k == '\x1b':  # ESC
        sys.exit(0)
    elif k == 'r':
        resetar()
    elif k == '+':
        velocidade_tempo *= 1.25
    elif k == '-':
        velocidade_tempo /= 1.25
    elif k == 'p':
        pausado = not pausado

    # *** NOVIDADE: Controle de Foco ***
    if '0' <= k <= '8':
        idx = int(k)
        if idx == 0:
            planeta_foco = -1 # Foco no Sol (Origem)
            print("Foco: Sol (Origem)")
        elif (idx-1) < len(PLANETAS):
            planeta_foco = idx - 1
            print(f"Foco: {PLANETAS[planeta_foco][0]}")
        glutPostRedisplay()


def resetar():
    global angulos, angulo_lua, velocidade_tempo, pausado, planeta_foco
    angulos = [0.0 for _ in range(len(PLANETAS))]
    angulo_lua = 0.0
    velocidade_tempo = 1.0
    pausado = False
    planeta_foco = -1 # Reseta o foco
    inicializar_camera() # Reseta o zoom/ângulos
    glutPostRedisplay()

def reshape(largura, altura):
    if altura == 0: altura = 1
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
    glEnable(GL_CULL_FACE) # Opcional: melhora performance
    glCullFace(GL_BACK)

# ---------- Main ----------
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(LARGURA_JANELA, ALTURA_JANELA)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Sistema Solar - Foco e Orbitas")

    init_gl()
    inicializar_texturas()
    inicializar_camera() # Agora também reseta o foco

    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(teclado)
    glutMouseFunc(evento_mouse)
    glutMotionFunc(evento_mouse_movimento)

    print("Controles:")
    print("  Mouse + Botão Esquerdo: Rotacionar camera")
    print("  Scroll: Zoom")
    print("  Teclas 0-8: Mudar foco (0=Sol, 1=Mercurio...)")
    print("  P: Pausar/Continuar")
    print("  +, -: Acelerar/Desacelerar tempo")
    print("  R: Resetar")
    print("  ESC: Sair")

    glutMainLoop()

if __name__ == '__main__':
    main()