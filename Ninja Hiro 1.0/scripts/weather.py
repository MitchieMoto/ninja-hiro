import pygame
import random
import math
from scripts.config import COLOR_CODES

RAIN_COLORS = [
    COLOR_CODES["Ai"],
    COLOR_CODES["Kon"],
    COLOR_CODES["Tetsuonando"],
    COLOR_CODES["Kachi"],
    COLOR_CODES["Gunjo"],
]

# A moving and vanishing line simulating a rain drop
class RainDrop:
    def __init__(self, player_pos, spawn_radius):
        self.spawn_radius = spawn_radius
        self.reset(player_pos)  

    # Simulates rain by centering the "raindrops" around the player
    def reset(self, player_pos):
        # Set a random depth, angle and radius for parallax and spawn distribution
        self.depth = random.uniform(0.6, 1.2)
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, self.spawn_radius)

        # Position raindrop around the player
        self.x = player_pos[0] + math.cos(angle) * radius
        self.y = player_pos[1] + math.sin(angle) * radius

        # Speed, line length, wind slant, blue color
        self.speed = random.uniform(4, 9) * self.depth
        self.length = random.randint(4, 10)
        self.angle = random.uniform(-0.25, -0.1)  
        self.color = random.choice(RAIN_COLORS)
    
    # Move the raindrop diagonally based on speed and angle
    def update(self):
        self.x += self.angle * self.speed
        self.y += self.speed

# Handles moving and rendering the raindrops as they fall around the player
class RainSystem:
    def __init__(self, player_ref, drop_count=300, spawn_radius=300):
        self.player_ref = player_ref  
        self.drop_count = drop_count 
        self.spawn_radius = spawn_radius  
        self.drops = []  
        self.initialized = False

    # Initialize raindrops based on the player's starting position
    def initialize(self, player_pos):
        self.drops = [RainDrop(player_pos, self.spawn_radius) for _ in range(self.drop_count)]

    # Move the drop start points and reset them when too far away
    def update(self):
        # First-time initialization tied to the player's current position
        if not self.initialized and self.player_ref:
            self.drops = [RainDrop(self.player_ref.rect().center, self.spawn_radius) for _ in range(self.drop_count)]
            self.initialized = True

        # Move the drops
        for drop in self.drops:
            drop.update()  

            # Check if drop is too far from the player, if so, respawn it
            dx = drop.x - self.player_ref.rect().center[0]
            dy = drop.y - self.player_ref.rect().center[1]
            if dx**2 + dy**2 > self.spawn_radius**2:
                drop.reset(self.player_ref.rect().center)

    # Renders each raindrop across the screen from each rain drops moving start position
    def render(self, surface, offset=None):
        if offset is None:
            offset = (0, 0)
        # Draws all raindrop lines
        for drop in self.drops:
            # Calculate screen position adjusted by camera offset    
            start_x = drop.x - offset[0]
            start_y = drop.y - offset[1]

            # Compute line end point
            end_x = start_x + drop.angle * drop.length
            end_y = start_y + drop.length

            # Draw the raindrop as a short slanted line
            pygame.draw.line(surface, drop.color, (start_x, start_y), (end_x, end_y), 1)
