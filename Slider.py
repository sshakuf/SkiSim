import pygame

class Slider:
    def __init__(self, x, y, width, height, min_value, max_value, initial_value=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.dragging = False
        self.slider_color = (100, 100, 100)
        self.handle_color = (200, 200, 200)
        self.handle_width = 10
        
    def draw(self, surface):
        # Draw slider background
        pygame.draw.rect(surface, self.slider_color, (self.x, self.y, self.width, self.height))
        
        # Calculate handle position
        handle_pos = self.get_handle_position()
        
        # Draw handle
        pygame.draw.rect(surface, self.handle_color, 
                         (handle_pos - self.handle_width//2, self.y - 5, 
                          self.handle_width, self.height + 10))
    
    def get_handle_position(self):
        # Convert current value to pixel position
        if self.max_value == self.min_value:  # Avoid division by zero
            return self.x
        normalized_value = (self.value - self.min_value) / (self.max_value - self.min_value)
        return int(self.x + normalized_value * self.width)
    
    def handle_event(self, event):
        # Handle mouse down
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            handle_pos = self.get_handle_position()
            
            # Check if click is on or near the handle or anywhere on the slider
            if self.y <= mouse_pos[1] <= self.y + self.height and self.x <= mouse_pos[0] <= self.x + self.width:
                self.dragging = True
                # Update value immediately based on click position
                normalized_pos = (mouse_pos[0] - self.x) / self.width
                self.value = self.min_value + normalized_pos * (self.max_value - self.min_value)
                return True
                
        # Handle mouse up
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            
        # Handle mouse motion while dragging
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_pos = pygame.mouse.get_pos()
            # Calculate new value based on mouse position
            normalized_pos = max(0, min(1, (mouse_pos[0] - self.x) / self.width))
            self.value = self.min_value + normalized_pos * (self.max_value - self.min_value)
            return True  # Indicate that value has changed
            
        return False  # Indicate no change
    
    def set_value(self, value):
        self.value = max(self.min_value, min(self.max_value, value))