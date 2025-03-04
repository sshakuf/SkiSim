import time
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import MotionVisualizer
from UDPHandler import UDPHandler
from Slider import Slider  # Import the Slider class from separate file

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
deltaTime = 0.01
# Sample index control
current_index = 0

motion_visualizers = []
last_index = 0

udpHandler = UDPHandler()

# Global variables for UI
slider = None
display_size = (800, 600)
slider_height = 20
slider_y_offset = 50  # Distance from bottom of screen
ui_surface = None
font = None

def syncTimes(motion_visualizers):
    # we need to to adjust the start position of the raw files to the same time
    startTime = 0
    #for motion_visualizer in motion_visualizers:
    if len(motion_visualizers) >= 2:
        startTime1 = motion_visualizers[0].time[0]
        startTime2 = motion_visualizers[1].time[0]
        
        index = 0
        if startTime1 > startTime2:
            while startTime2 < startTime1:
                index += 1
                startTime2 = motion_visualizers[1].time[index]
            motion_visualizers[0].set_start_index(index)
            print ("startTime2 < startTime1 : Index: ", index)
        elif startTime2 > startTime1:
            while startTime1 < startTime2:
                index += 1
                startTime1 = motion_visualizers[0].time[index]
            motion_visualizers[1].set_start_index(index)
            print ("startTime2 > startTime1 : Index: ", index)

# Initialize Pygame and OpenGL
def init_3d():
    global motion_visualizers, last_index, udpHandler, deltaTime, slider, display_size, ui_surface, font

    # Initialize visualizers
    left = "data/Skimulator/Set1/Left_2025-03-02_15-06-29/"
    right = "data/Skimulator/Set1/Right_2025-03-02_15-07-11/"
    motion_visualizers.append(MotionVisualizer.MotionVisualizer(left + "Accelerometer.csv", left + "Gyroscope.csv", True, udpHandler, deltaTime))
    motion_visualizers.append(MotionVisualizer.MotionVisualizer(right + "Accelerometer.csv", right + "Gyroscope.csv", False, udpHandler, deltaTime))

    # Get the maximum length of data
    for motion_visualizer in motion_visualizers:
        last_index = max(last_index, motion_visualizer.get_length())
    
    # Synchronize time in visualizers
    syncTimes(motion_visualizers)

    # Initialize Pygame
    pygame.init()
    display_size = (800, 600)
    pygame.display.set_mode(display_size, pygame.DOUBLEBUF | pygame.OPENGL)
    
    # Initialize UI components
    ui_surface = pygame.Surface(display_size, pygame.SRCALPHA)
    font = pygame.font.Font(None, 24)  # Default font
    
    # Create slider after we know the last_index
    slider = Slider(50, display_size[1] - slider_y_offset, display_size[0] - 100, slider_height, 0, last_index - 1, 0)
    
    # Initialize OpenGL
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display_size[0] / display_size[1]), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)


# Initialize everything
init_3d()

# Initialize logic for each visualizer
for motion_visualizer in motion_visualizers:
    motion_visualizer.initialize()
    motion_visualizer.start()


def handle_input():
    global ENABLE_CAMERA_FOLLOW, PAUSED, camera_offset, camera_rotation, zoom_level, current_index, slider
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
            
        # Handle slider events first
        if slider.handle_event(event):
            # If slider value changed, update current_index
            current_index = int(slider.value)
            # Continue processing other events
            
        if event.type == pygame.KEYDOWN:
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
                slider.set_value(current_index)
            elif event.key == pygame.K_PERIOD:
                current_index = min(last_index - 1, current_index + 1)  # Go forward
                slider.set_value(current_index)

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

def draw_ui():
    global slider, display_size, ui_surface, font
    
    # Save current OpenGL state
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    # Use bottom-left as origin (0,0) to match Pygame coordinate system
    glOrtho(0, display_size[0], 0, display_size[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth test temporarily
    glDisable(GL_DEPTH_TEST)
    
    # Clear the surface
    ui_surface.fill((0, 0, 0, 0))  # Transparent
    
    # First render the text at the bottom
    text = font.render(f"Frame: {current_index+1} / {last_index}", True, (255, 255, 255))
    
    # Render text first (will appear below slider)
    text_y = slider_y_offset + 10  # This will position text below the slider
    # ui_surface.blit(text, (display_size[0]//2 - text.get_width()//2, 
    #                        display_size[1] - text_y))
    
    # Calculate slider position (move it up to avoid covering text)
    adjusted_slider_y = slider_y_offset + 40  # Move slider up to avoid covering text
    
    # Update slider position
    slider.y = display_size[1] - adjusted_slider_y
    
    # Adjust slider drawing for OpenGL coordinates (Y is flipped in OpenGL)
    flipped_y = display_size[1] - slider.y - slider.height
    
    # Store original slider position
    original_y = slider.y
    
    # Temporarily modify slider position for drawing
    slider.y = flipped_y
    
    # Draw slider on the surface
    slider.draw(ui_surface)
    
    # Restore original slider position for mouse interaction
    slider.y = original_y
    
    # Convert pygame surface to OpenGL with vertical flip
    # Use subsurface=False to prevent vertical flipping of the texture
    data = pygame.image.tostring(ui_surface, "RGBA", False)
    
    # Create a texture
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, display_size[0], display_size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    
    # Enable texturing and blending
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1, 1, 1, 1)  # Set color to white (texture color will show)
    
    # Draw the texture as a screen-aligned quad
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(0, 0)
    glTexCoord2f(1, 0); glVertex2f(display_size[0], 0)
    glTexCoord2f(1, 1); glVertex2f(display_size[0], display_size[1])
    glTexCoord2f(0, 1); glVertex2f(0, display_size[1])
    glEnd()
    
    # Clean up
    glDeleteTextures(1, [texture_id])
    
    # Restore OpenGL state
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glPopAttrib()


def animate_3d():
    global PAUSED, current_index, last_index, motion_visualizers, camera_offset, camera_rotation, zoom_level, deltaTime, slider
    
    while True:
        handle_input()

        if current_index >= last_index:
            current_index = 0  # Restart animation and pause at first frame
            slider.set_value(0)
            
            for motion_visualizer in motion_visualizers:
                motion_visualizer.reset_state()
            PAUSED = True
        
        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up 3D scene
        glLoadIdentity()
        glTranslatef(*camera_offset)
        glRotatef(camera_rotation[1], 1, 0, 0)
        glRotatef(camera_rotation[0], 0, 1, 0)
        glTranslatef(0, 0, zoom_level)
    
        # Draw 3D elements
        draw_grid()
        
        # Draw 3D visualization
        for motion_visualizer in motion_visualizers:
            motion_visualizer.run(current_index, PAUSED)
        
        for motion_visualizer in motion_visualizers:
            motion_visualizer.afterRun(current_index, PAUSED)
            
        # Add OpenGL text in 3D space
        draw_text(f"Sample {current_index+1} / {last_index}", 10, 10)
        draw_text(f"Camera: {camera_offset}, Rot: {camera_rotation}", 10, 30)
        
        # Draw 2D UI elements on top
        draw_ui()
        
        # Update display
        pygame.display.flip()
        
        # Update animation index
        if not PAUSED:
            current_index += 1
            slider.set_value(current_index)
            
        time.sleep(deltaTime)


# Start animation loop
animate_3d()