import pandas as pd
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import socket
import json
from UDPHandler import UDPHandler

class MotionVisualizer:
    def __init__(self, accel_path, gyro_path, isLeftLeg, udpHandler, dt=0.01, rotation_scale=1.2, acc_scale=1.0):
        self.dt = dt  # Time step remains unchanged
        self.rotation_scale = rotation_scale  # Scale factor for yaw, pitch, and roll updates
        self.acc_scale = acc_scale            # Scale factor for accelerometer updates
        self.load_data(accel_path, gyro_path)
        self.reset_state()
        self.isLeftLeg = isLeftLeg
        # Create a UDP handler instance
        self.udp_handler = udpHandler
        self.start_index = 0

    def set_start_index(self, index):
        self.start_index = index

    def initialize(self):
        self.reset_state()
        pass

    def start(self):
        pass

    def load_data(self, accel_path, gyro_path):
        df_accel = pd.read_csv(accel_path)
        df_gyro = pd.read_csv(gyro_path)
        
        self.time = df_accel["time"].values
        self.length = len(df_accel)

        # Calculate and print the dt between the two initial samples (if available)
        if len(self.time) > 1:
            computed_dt = self.time[1] - self.time[0]
            print("Computed dt between initial samples:", computed_dt)

        self.accelerometer_x = df_accel["x"].values
        self.accelerometer_y = df_accel["y"].values
        self.accelerometer_z = df_accel["z"].values

        self.gyro_x = df_gyro["x"].values
        self.gyro_y = df_gyro["y"].values
        self.gyro_z = df_gyro["z"].values

    def get_length(self):
        return len(self.accelerometer_x)

    def reset_state(self):
        self.pos_x, self.pos_y, self.pos_z = 0.0, 0.0, 0.0
        self.vel_x, self.vel_y, self.vel_z = 0.0, 0.0, 0.0
        self.yaw, self.pitch, self.roll = 0.0, 0.0, 0.0
        self.acc_x, self.acc_y, self.acc_z = 0.0, 0.0, 0.0

    def run(self, index, pause):
        curr_index = self.start_index + index
        if not pause and curr_index < len(self.accelerometer_x):
            # Scale accelerometer data
            self.acc_x = self.accelerometer_x[curr_index] * self.acc_scale
            self.acc_y = self.accelerometer_y[curr_index] * self.acc_scale
            self.acc_z = self.accelerometer_z[curr_index] * self.acc_scale

            # Update velocities with scaled acceleration
            self.vel_x += self.acc_x * self.dt
            self.vel_y += self.acc_y * self.dt
            self.vel_z += self.acc_z * self.dt

            # Update positions
            self.pos_x += self.vel_x * self.dt
            self.pos_y += self.vel_y * self.dt
            self.pos_z += self.vel_z * self.dt

            # Convert gyroscope data from radians to degrees (1 radian = 180/π degrees)
            rad_to_deg = 180.0 / 3.14159265358979
            gyro_x_deg = self.gyro_x[curr_index] * rad_to_deg
            gyro_y_deg = self.gyro_y[curr_index] * rad_to_deg
            gyro_z_deg = self.gyro_z[curr_index] * rad_to_deg
            
            # Update angles with converted gyroscope data (now in degrees/second)
            self.yaw   += gyro_z_deg * self.dt * self.rotation_scale
            self.pitch += gyro_y_deg * self.dt * self.rotation_scale
            self.roll  += gyro_x_deg * self.dt * self.rotation_scale

            # Normalize angles to be within [-180, 180]
            self.yaw   = ((self.yaw + 180) % 360) - 180
            self.pitch = ((self.pitch + 180) % 360) - 180
            self.roll  = ((self.roll + 180) % 360) - 180

        self.draw_cone_with_line()
        self.udp_handler.setLegData(self.isLeftLeg, self.yaw, self.pitch, self.roll, self.acc_x, self.acc_y, self.acc_z)


    def afterRun(self, index, pause):
        if self.isLeftLeg:
            self.udp_handler.sendLegData()

    def draw_cone_with_line(self):
        glPushMatrix()
        glTranslatef(self.pos_x, self.pos_y, self.pos_z)
        glRotatef(self.yaw, 0, 1, 0)
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.roll, 0, 0, 1)

        glColor3f(0.0, 1.0, 0.0)
        glutSolidCone(0.2, 0.5, 20, 20)

        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1)
        glEnd()

        glPopMatrix()