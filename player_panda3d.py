import time
import numpy as np
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectSlider, DirectFrame, DirectLabel, DGG
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *
import MotionVisualizer
from UDPHandler import UDPHandler

class MotionVisualizerApp(ShowBase):
    def __init__(self):
        # Initialize ShowBase
        ShowBase.__init__(self)
        
        # Flags for enabling/disabling features
        self.ENABLE_GRID = True
        self.ENABLE_CAMERA_FOLLOW = True
        self.PAUSED = True  # Start paused at the first frame
        
        # Camera controls
        self.camera_offset = [0.0, 2.0, -30.0]  # Start above looking down
        self.camera_rotation = [0.0, 40.0]  # Looking at (0,0,0)
        self.camera_speed = 1.0
        self.zoom_speed = 1.0
        self.zoom_level = 0
        self.deltaTime = 0.01
        
        # Sample index control
        self.current_index = 0
        self.motion_visualizers = []
        self.last_index = 0
        
        # UDP handler
        self.udpHandler = UDPHandler()
        
        # Set up Panda3D window
        self.win.setClearColor(Vec4(0.1, 0.1, 0.1, 1))
        
        # Disable default camera controls
        self.disableMouse()
        
        # Position camera initially
        self.update_camera()
        
        # Set up keyboard inputs
        self.setup_inputs()
        
        # Initialize visualizers and UI
        self.init_visualizers()
        self.init_ui()
        
        self.load_fbx_model("AlpineSkiBootA1Mat_right.fbx")

        # Set up update task
        self.taskMgr.add(self.update, "UpdateTask")
        
        # Create a grid
        if self.ENABLE_GRID:
            self.create_grid()
    
    def load_fbx_model(self, model_path):
        try:
            self.model = self.loader.loadModel(model_path)
            if not self.model:
                print(f"Failed to load FBX: {model_path}")
                return
            
            self.model.setScale(0.001)  # Adjust size
            self.model.setPos(0, 10, 0)  # Move it in front of the camera
            self.model.reparentTo(self.render)  # Attach to scene
            
            print(f"Successfully loaded FBX: {model_path}")
            
            # Make sure the camera looks at it
            self.camera.lookAt(self.model)
            
            # Setup lighting
            self.setup_lighting()

        except Exception as e:
            print(f"Error loading FBX: {e}")

    def setup_lighting(self):
        light = DirectionalLight('light')
        light.setColor((1, 1, 1, 1))
        light_np = self.render.attachNewNode(light)
        light_np.setHpr(-45, -45, 0)
        self.render.setLight(light_np)

    def setup_inputs(self):
        """Set up keyboard controls"""
        self.accept("escape", self.exit_app)
        self.accept("space", self.toggle_pause)
        self.accept("c", self.toggle_camera_follow)
        self.accept("arrow_up", self.camera_move, [0, 1, 0, self.camera_speed])
        self.accept("arrow_down", self.camera_move, [0, -1, 0, self.camera_speed])
        self.accept("arrow_left", self.camera_move, [-1, 0, 0, self.camera_speed])
        self.accept("arrow_right", self.camera_move, [1, 0, 0, self.camera_speed])
        self.accept("a", self.camera_rotate, [-2.0, 0])
        self.accept("d", self.camera_rotate, [2.0, 0])
        self.accept("w", self.camera_rotate, [0, -2.0])
        self.accept("s", self.camera_rotate, [0, 2.0])
        self.accept("+", self.zoom_camera, [self.zoom_speed])
        self.accept("=", self.zoom_camera, [self.zoom_speed])
        self.accept("-", self.zoom_camera, [-self.zoom_speed])
        self.accept(",", self.step_frame, [-1])
        self.accept(".", self.step_frame, [1])
    
    def init_visualizers(self):
        """Initialize motion visualizers"""
        left = "data/Skimulator/Set3/Left/"
        right = "data/Skimulator/Set3/Right/"
        self.motion_visualizers.append(MotionVisualizer.MotionVisualizer(left, True, self.udpHandler, self.deltaTime))
        self.motion_visualizers.append(MotionVisualizer.MotionVisualizer(right, False, self.udpHandler, self.deltaTime))
        
        # Get the maximum length of data
        for motion_visualizer in self.motion_visualizers:
            self.last_index = max(self.last_index, motion_visualizer.get_length())
        
        # Synchronize time in visualizers
        self.sync_times()
        
        # Initialize logic for each visualizer
        for motion_visualizer in self.motion_visualizers:
            motion_visualizer.initialize()
            motion_visualizer.start()
            
            # Add a new NodePath to render for each visualizer
            motion_visualizer.node_path = self.render.attachNewNode(f"visualizer-{id(motion_visualizer)}")
    
    def sync_times(self):
        """Synchronize the start times of the motion visualizers"""
        if len(self.motion_visualizers) >= 2:
            startTime1 = self.motion_visualizers[0].time[0]
            startTime2 = self.motion_visualizers[1].time[0]
            
            index = 0
            if startTime1 > startTime2:
                while startTime2 < startTime1:
                    index += 1
                    startTime2 = self.motion_visualizers[1].time[index]
                self.motion_visualizers[0].set_start_index(index)
                print("startTime2 < startTime1 : Index: ", index)
            elif startTime2 > startTime1:
                while startTime1 < startTime2:
                    index += 1
                    startTime1 = self.motion_visualizers[0].time[index]
                self.motion_visualizers[1].set_start_index(index)
                print("startTime2 > startTime1 : Index: ", index)
    
    def init_ui(self):
        """Initialize the UI elements"""
        # Create frame info text
        self.frame_text = OnscreenText(
            text=f"Frame: {self.current_index+1} / {self.last_index}",
            pos=(-0.95, 0.9),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        # Create camera info text
        self.camera_text = OnscreenText(
            text=f"Camera: {self.camera_offset}, Rot: {self.camera_rotation}",
            pos=(-0.95, 0.85),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        # Create frame slider
        self.slider = Slider(
            self,
            range=(0, self.last_index - 1),
            value=0,
            position=(0, 0, -0.85),
            size=(1.8, 0.05),
            command=self.slider_changed
        )
    
    def create_grid(self):
        """Create a reference grid on the ground"""
        # Create vertex format with position and color
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData('grid', format, Geom.UHStatic)
        
        # Create writers for vertex and color
        vertex = GeomVertexWriter(vdata, 'vertex')
        color = GeomVertexWriter(vdata, 'color')
        
        # Create line segments
        lines = GeomLines(Geom.UHStatic)
        
        grid_color = (0.5, 0.5, 0.5, 1.0)
        grid_size = 10
        grid_step = 1
        
        # Add vertices and colors
        vertex_index = 0
        
        # Create grid lines
        for i in range(-grid_size, grid_size + 1, grid_step):
            # X-axis lines
            vertex.addData3f(i, 0, -grid_size)
            vertex.addData3f(i, 0, grid_size)
            color.addData4f(*grid_color)
            color.addData4f(*grid_color)
            
            # Z-axis lines
            vertex.addData3f(-grid_size, 0, i)
            vertex.addData3f(grid_size, 0, i)
            color.addData4f(*grid_color)
            color.addData4f(*grid_color)
            
            # Add lines
            lines.addVertices(vertex_index, vertex_index + 1)
            lines.addVertices(vertex_index + 2, vertex_index + 3)
            vertex_index += 4
        
        # Create the Geom and add primitives
        geom = Geom(vdata)
        geom.addPrimitive(lines)
        
        # Create GeomNode and add the Geom
        node = GeomNode('grid')
        node.addGeom(geom)
        
        # Create NodePath and attach to render
        grid_np = self.render.attachNewNode(node)
        # Apply line thickness
        grid_np.setRenderModeThickness(2)
    
    def update_camera(self):
        """Update camera position and orientation"""
        # Reset camera position and orientation
        self.camera.setPos(0, 0, 0)
        self.camera.setHpr(0, 0, 0)
        
        # Apply camera transformations in the correct order
        self.camera.setPos(
            self.camera_offset[0],
            -self.camera_offset[2],  # Panda3D uses different coordinate system
            self.camera_offset[1]
        )
        
        # Rotate the camera (pitch, then yaw)
        self.camera.setHpr(self.camera_rotation[0], -self.camera_rotation[1], 0)
        
        # Apply zoom (move camera forward/backward)
        self.camera.setY(self.camera.getY() + self.zoom_level)
    
    def camera_move(self, x, y, z, speed):
        """Move camera by the given offset"""
        self.camera_offset[0] += x * speed
        self.camera_offset[1] += y * speed
        self.camera_offset[2] += z * speed
        self.update_camera()
    
    def camera_rotate(self, yaw, pitch):
        """Rotate camera by the given angles"""
        self.camera_rotation[0] += yaw
        self.camera_rotation[1] += pitch
        self.update_camera()
    
    def zoom_camera(self, amount):
        """Zoom camera in/out"""
        self.zoom_level += amount
        self.update_camera()
    
    def toggle_pause(self):
        """Toggle animation pause state"""
        self.PAUSED = not self.PAUSED
    
    def toggle_camera_follow(self):
        """Toggle camera follow mode"""
        self.ENABLE_CAMERA_FOLLOW = not self.ENABLE_CAMERA_FOLLOW
    
    def exit_app(self):
        """Exit the application cleanly"""
        self.userExit()
    
    def step_frame(self, direction):
        """Step forward or backward one frame"""
        new_index = self.current_index + direction
        if 0 <= new_index < self.last_index:
            self.current_index = new_index
            self.slider.set_value(self.current_index)
    
    def slider_changed(self):
        """Handle slider value changes"""
        self.current_index = int(self.slider.get_value())
    
    def update(self, task):
        """Main update loop"""
        # Update frame counter and UI elements
        self.frame_text.setText(f"Frame: {self.current_index+1} / {self.last_index}")
        self.camera_text.setText(f"Camera: {self.camera_offset}, Rot: {self.camera_rotation}")
        
        # Update motion visualizers
        for motion_visualizer in self.motion_visualizers:
            motion_visualizer.run(self.current_index, self.PAUSED)
        
        for motion_visualizer in self.motion_visualizers:
            motion_visualizer.afterRun(self.current_index, self.PAUSED)
        
        # Advance to next frame if not paused
        if not self.PAUSED:
            self.current_index += 1
            if self.current_index >= self.last_index:
                self.current_index = 0
                for motion_visualizer in self.motion_visualizers:
                    motion_visualizer.reset_state()
                self.PAUSED = True
            
            # Update slider position without triggering callbacks
            self.slider.set_value(self.current_index, from_update=True)
        
        # Sleep to maintain frame rate
        time.sleep(self.deltaTime)
        
        return task.cont


class Slider:
    def __init__(self, app, range=(0, 100), value=0, position=(0, 0, 0), size=(1, 0.05), command=None):
        """
        Create a slider UI element in Panda3D
        
        Args:
            app: The Panda3D application instance
            range: Tuple of (min, max) values
            value: Initial value
            position: Position in 3D space (x, y, z)
            size: Size as (width, height)
            command: Callback function when value changes
        """
        self.app = app
        self.min_value, self.max_value = range
        self._value = value
        self.command = command
        self._updating = False
        
        # Create slider frame
        self.frame = DirectFrame(
            frameSize=(position[0]-size[0]/2, position[0]+size[0]/2, 
                       position[2]-size[1]/2, position[2]+size[1]/2),
            frameColor=(0.2, 0.2, 0.2, 0.8),
            pos=(position[0], position[1], position[2])
        )
        
        # Create the slider
        self.slider = DirectSlider(
            range=(self.min_value, self.max_value),
            value=self._value,
            pageSize=1,
            frameSize=(-size[0]/2, size[0]/2, -size[1]/2, size[1]/2),
            frameColor=(0.4, 0.4, 0.4, 0.8),
            thumb_frameColor=(0.6, 0.6, 0.8, 1.0),
            thumb_relief=DGG.FLAT,
            command=self._on_value_changed,
            parent=self.frame
        )
    
    def _on_value_changed(self):
        """Internal callback when slider value changes"""
        if not self._updating:
            self._value = self.slider['value']
            if self.command:
                self.command()
    
    def get_value(self):
        """Get the current slider value"""
        return self._value
    
    def set_value(self, value, from_update=False):
        """Set the slider value"""
        value = max(self.min_value, min(self.max_value, value))
        self._value = value
        
        # Avoid recursive callbacks when setting from update
        self._updating = from_update
        self.slider['value'] = value
        self._updating = False


# Start the application
if __name__ == "__main__":
    app = MotionVisualizerApp()
    app.run()
