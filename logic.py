### Logic File (logic.py)

import pandas as pd
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Load CSV files
def initialize():
    global accelerometer_x, accelerometer_y, accelerometer_z, gyro_x, gyro_y, gyro_z, pos_x, pos_y, pos_z, vel_x, vel_y, vel_z, yaw, pitch, roll, dt
    base_path = "./"
    df_accel = pd.read_csv(base_path + "Accelerometer.csv")
    df_gyro = pd.read_csv(base_path + "Gyroscope.csv")
    
    accelerometer_x = df_accel["x"].values  # X-axis acceleration
    accelerometer_y = df_accel["y"].values  # Y-axis acceleration
    accelerometer_z = df_accel["z"].values  # Z-axis acceleration

    gyro_x = df_gyro["x"].values  # Roll rate
    gyro_y = df_gyro["y"].values  # Pitch rate
    gyro_z = df_gyro["z"].values  # Yaw rate

    dt = 0.05  # Time step

def getLenght():
    return len(accelerometer_x)

# Reset initial state
def start():
    global pos_x, pos_y, pos_z, vel_x, vel_y, vel_z, yaw, pitch, roll
    pos_x, pos_y, pos_z = 0.0, 0.0, 0.0
    vel_x, vel_y, vel_z = 0.0, 0.0, 0.0
    yaw, pitch, roll = 0.0, 0.0, 0.0

# Compute motion and draw the cone
def run(index, pause):
    global pos_x, pos_y, pos_z, vel_x, vel_y, vel_z, yaw, pitch, roll
    # if index >= len(accelerometer_x):
    #     return
    if (not pause and index < len(accelerometer_x)):
        acc_x = accelerometer_x[index]
        acc_y = accelerometer_y[index]
        acc_z = accelerometer_z[index]
        
        vel_x += acc_x * dt
        vel_y += acc_y * dt
        vel_z += acc_z * dt
        
        pos_x += vel_x * dt
        pos_y += vel_y * dt
        pos_z += vel_z * dt
        
        yaw += gyro_z[index] * dt
        pitch += gyro_y[index] * dt
        roll += gyro_x[index] * dt
    
    draw_cone_with_line(pos_x, pos_y, pos_z, yaw, pitch, roll)

# Draw cone and orientation line
def draw_cone_with_line(x, y, z, yaw, pitch, roll):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(yaw, 0, 1, 0)
    glRotatef(pitch, 1, 0, 0)
    glRotatef(roll, 0, 0, 1)
    
    glColor3f(0.0, 1.0, 0.0)
    glutSolidCone(0.2, 0.5, 20, 20)
    
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 1)
    glEnd()
    
    glPopMatrix()