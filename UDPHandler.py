import socket
import json
import time

class UDPHandler:
    def __init__(self, ip="127.0.0.1", port=5005):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.left_leg_data = None
        self.right_leg_data = None
    
    def setLegData(self, isLeftLeg, yaw, pitch, roll, acc_x, acc_y, acc_z, 
                  gravity_x, gravity_y, gravity_z):
        """
        Set leg data including orientation, acceleration, and gravity
        
        Parameters:
        -----------
        isLeftLeg : bool
            True if data is for left leg, False for right leg
        yaw, pitch, roll : float
            Orientation angles in degrees
        acc_x, acc_y, acc_z : float
            Acceleration values
        gravity_x, gravity_y, gravity_z : float
            Gravity vector components (mandatory)
        """
        # Create a data dictionary with all values
        leg_data = {
            "yaw": float(yaw),
            "pitch": float(pitch),
            "roll": float(roll),
            "acc": {
                "x": float(acc_x),
                "y": float(acc_y),
                "z": float(acc_z)
            },
            "gravity": {
                "x": float(gravity_x),
                "y": float(gravity_y),
                "z": float(gravity_z)
            }
        }
        
        # Store data for the appropriate leg
        if isLeftLeg:
            self.left_leg_data = leg_data
        else:
            self.right_leg_data = leg_data
    
    def sendLegData(self):
        """
        Send both legs' data over UDP as a combined JSON message
        with the structure: { "legs": { "left": {...}, "right": {...} } }
        """
        if self.left_leg_data is None and self.right_leg_data is None:
            return
            
        # Create the legs data structure
        legs_data = {}
        
        # Add leg data if available
        if self.left_leg_data is not None:
            legs_data["left"] = self.left_leg_data
            
        if self.right_leg_data is not None:
            legs_data["right"] = self.right_leg_data
            
        # Create the final combined data structure
        combined_data = {
            "legs": legs_data
        }
            
        # Convert to JSON and send
        json_data = json.dumps(combined_data)
        try:
            self.socket.sendto(json_data.encode(), (self.ip, self.port))
            # Print the data being sent (can be commented out in production)
            # print(f"Sending: {json_data}")
        except Exception as e:
            print(f"Error sending UDP data: {e}")