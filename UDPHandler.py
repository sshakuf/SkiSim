import pandas as pd
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import socket
import json
import UDPHandler


# UDP Handler Class
class UDPHandler:
    """Handles UDP communication for motion data."""
    
    def __init__(self, ip="127.0.0.1", port=5005):
        self.UDP_IP = ip
        self.UDP_PORT = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.motion_data = {
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


    def setLegData(self, isLeft, yaw, pitch, roll, accX, accY, accZ):
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

