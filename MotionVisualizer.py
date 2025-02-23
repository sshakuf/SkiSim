import pandas as pd
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import socket
import json

class MotionVisualizer:
    def __init__(self, accel_path, gyro_path, isLeftLeg):
        self.dt = 0.05  # Time step
        self.load_data(accel_path, gyro_path)
        self.reset_state()
        self.isLeftLeg = isLeftLeg
        # Create a UDP handler instance
        self.udp_handler = UDPHandler()

    def initialize(self):
        self.reset_state()
        pass

    def start(self):
        pass

    def load_data(self, accel_path, gyro_path):
        df_accel = pd.read_csv(accel_path)
        df_gyro = pd.read_csv(gyro_path)

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
        if not pause and index < len(self.accelerometer_x):
            self.acc_x = self.accelerometer_x[index]
            self.acc_y = self.accelerometer_y[index]
            self.acc_z = self.accelerometer_z[index]

            self.vel_x += self.acc_x * self.dt
            self.vel_y += self.acc_y * self.dt
            self.vel_z += self.acc_z * self.dt

            self.pos_x += self.vel_x * self.dt
            self.pos_y += self.vel_y * self.dt
            self.pos_z += self.vel_z * self.dt

            self.yaw += self.gyro_z[index] * self.dt
            self.pitch += self.gyro_y[index] * self.dt
            self.roll += self.gyro_x[index] * self.dt

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

    


# UDP Handler Class
class UDPHandler:
    """Handles UDP communication for motion data."""
    
    def __init__(self, ip="127.0.0.1", port=5005):
        self.UDP_IP = ip
        self.UDP_PORT = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self. motion_data = {
            "legs": {
                "left": {
                    "pitch": 0, "yaw": 0, "roll": 0,
                    "accX": 0, "accY": 0, "accZ": 0
                },
                "right": {
                    "pitch": 0, "yaw": 0, "roll": 0,
                    "accX": 0, "accY": 0, "accZ": 0
                }
            }
        }

    def send_data(self, data):
        """Send JSON data via UDP."""
        json_data = json.dumps(data)
        self.sock.sendto(json_data.encode(), (self.UDP_IP, self.UDP_PORT))
    
    def update_connection(self, ip, port):
        """Update UDP IP and port settings."""
        self.UDP_IP = ip
        self.UDP_PORT = int(port)

    def sendLegData(self):
        self.send_data(self.motion_data)


    def setLegData(isLeft, self, yaw, pitch, roll, accX, accY, accZ):
        # update motion_data
        if isLeft:
            leg = "left"
        else:
            leg = "right"

        self.motion_data["legs"][leg]["pitch"] = pitch
        self.motion_data["legs"][leg]["yaw"] = yaw
        self.motion_data["legs"][leg]["roll"] = roll    
        self.motion_data["legs"][leg]["accX"] = accX
        self.motion_data["legs"][leg]["accY"] = accY
        self.motion_data["legs"][leg]["accZ"] = accZ

