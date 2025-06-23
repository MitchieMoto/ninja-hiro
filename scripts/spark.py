import math
import pygame

# Individual sparks, they run until they have no speed
class Spark:
    def __init__(self, pos, angle, speed):
        # Cartesian Coordinates
        self.pos = list(pos)
        # Polar coordinates for velocity
        self.angle = angle
        self.speed = speed
    
    # Tracks the angle and decrements the spark speed
    def update(self):
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed
        
        # Slow down spark speed
        self.speed = max(0, self.speed - 0.1)
        return not self.speed
    
    # Renders the spark as long as it is moving
    def render(self, surf, offset=(0, 0)):
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1]),
        ]
        pygame.draw.polygon(surf, (255, 255, 255), render_points)