### Main File (player.py)

import time
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from logic import initialize, start, run, getLenght

# Flags for enabling/disabling features
ENABLE_GRID = True
ENABLE_CAMERA_FOLLOW = True
PAUSED = True  # Start paused at the first frame

# Camera controls
camera_offset = [0.0, 2.0, -30]  # Start above looking down
camera_rotation = [0.0, 40]  # Looking at (0,0,0)
camera_speed = 1.0
zoom_speed = 1.0
zoom_level = 0

# Sample index control
current_index = 0


# Initialize Pygame and OpenGL
def init_3d():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 0.1, 100.0)  # Move camera further back
    glMatrixMode(GL_MODELVIEW)


init_3d()
# Initialize logic
initialize()
start()


def handle_input():
    global ENABLE_CAMERA_FOLLOW, PAUSED, camera_offset, camera_rotation, zoom_level, current_index
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                PAUSED = not PAUSED
            elif event.key == pygame.K_c:
                ENABLE_CAMERA_FOLLOW = not ENABLE_CAMERA_FOLLOW
            elif event.key == pygame.K_UP:
                camera_offset[1] -= camera_speed
            elif event.key == pygame.K_DOWN:
                camera_offset[1] += camera_speed
            elif event.key == pygame.K_LEFT:
                camera_offset[0] -= camera_speed
            elif event.key == pygame.K_RIGHT:
                camera_offset[0] += camera_speed
            elif event.key == pygame.K_a:
                camera_rotation[0] -= 2.0  # Rotate left
            elif event.key == pygame.K_d:
                camera_rotation[0] += 2.0  # Rotate right
            elif event.key == pygame.K_w:
                camera_rotation[1] -= 2.0  # Rotate up
            elif event.key == pygame.K_s:
                camera_rotation[1] += 2.0  # Rotate down
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                move_camera_relative(zoom_speed)
            elif event.key == pygame.K_MINUS:
                move_camera_relative(-zoom_speed)
            elif event.key == pygame.K_COMMA:
                current_index = max(0, current_index - 1)  # Go back
            elif event.key == pygame.K_PERIOD:
                current_index = min(getLenght() - 1, current_index + 1)  # Go forward

def move_camera_relative(distance):
    global camera_offset, camera_rotation
    yaw_rad = np.radians(camera_rotation[0])
    pitch_rad = np.radians(camera_rotation[1])
    
    forward = np.array([
        np.cos(pitch_rad) * np.sin(yaw_rad),
        np.sin(pitch_rad),
        np.cos(pitch_rad) * np.cos(yaw_rad)
    ])
    
    camera_offset += forward * distance


def draw_text(text, x, y):
    glWindowPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def draw_grid():
    if not ENABLE_GRID:
        return
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_LINES)
    for i in range(-10, 11):
        glVertex3f(i, 0, -10)
        glVertex3f(i, 0, 10)
        glVertex3f(-10, 0, i)
        glVertex3f(10, 0, i)
    glEnd()


def animate_3d():
    global PAUSED, current_index
    
    maxindex = getLenght()
    while True:
        handle_input()

        if current_index >= maxindex:
            current_index = 0  # Restart animation and pause at first frame
            pos_x, pos_y, pos_z = 0.0, 0.0, 0.0
            vel_x, vel_y, vel_z = 0.0, 0.0, 0.0
            yaw, pitch, roll = 0.0, 0.0, 0.0
            acc_x, acc_y, acc_z = 0.0, 0.0, 0.0
            PAUSED = True
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        glTranslatef(*camera_offset)
        glRotatef(camera_rotation[1], 1, 0, 0)
        glRotatef(camera_rotation[0], 0, 1, 0)
        glTranslatef(0, 0, zoom_level)
    
        draw_grid()
        draw_text(f"Sample {current_index+1} / {maxindex}", 10, 10)
        draw_text(f"Camera Position: {camera_offset}, Rotation: {camera_rotation}, Zoom {zoom_level}", 10, 30)
        
        run(current_index, PAUSED)  # Run logic

        pygame.display.flip()
        if not PAUSED:
            
            current_index += 1
        time.sleep(0.05)

animate_3d()


