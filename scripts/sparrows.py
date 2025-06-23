import pygame
import random
import math
from scripts.animation import Animation

# Defines spawn, movemement, and animation behavior for individual sparrows
class Sparrow:
    def __init__(self, animation, screen_size, scroll=(0, 0), speed_range=(0.2, 0.8)):
        # Copy animation so each bird has its own instance
        self.animation = animation.copy()  
        self.screen_width, self.screen_height = screen_size
        self.depth = random.uniform(0.5, 1.0)
        self.speed_range = speed_range
        self.respawn(scroll)

    # Handles bird respawn locations and randomizes bird attributes for each respawned bird
    def respawn(self, scroll=(0, 0)):
        self.depth = random.uniform(0.5, 1.0)
        target_y = random.uniform(self.screen_height * 0.1, self.screen_height * 0.45)
        self.y = target_y + scroll[1] * self.depth * 0.21
        self.base_y = self.y
        self.speed = random.uniform(*self.speed_range)
        self.direction = random.choice([-1, 1])
        self.flip = self.direction == -1

        # Places birds just off screen depending on
        respawn_margin = 20  
        # Left side (bird facing right)    
        if self.direction == 1:
            self.x = scroll[0] * self.depth - respawn_margin / (1 - self.depth)
        # Else right side      
        else:
            self.x = scroll[0] * self.depth + self.screen_width + respawn_margin / (1 - self.depth)

        # Set random movement attributes for the sparrow
        self.bob_amplitude = random.uniform(0.6, 1.6)
        self.bob_speed = random.uniform(0.0008, 0.0015)
        self.bob_phase = random.uniform(0, math.tau)
        self.glide_interval = random.randint(120, 300)
        # Reset base variables
        self.glide_timer = 0           
        self.flapping = True
        self.dead = False

    # Defines sparrow movement and animation control
    def update(self, scroll=(0, 0)):
        self.x += self.speed * self.direction
        self.glide_timer += 1

        # Toggle between flapping and gliding
        if self.glide_timer >= self.glide_interval:
            self.flapping = not self.flapping  
            self.glide_timer = 0
            self.glide_interval = random.randint(120, 300)  # Reset interval
        # While flapping, bob vertically and cycle through animations
        if self.flapping:
            time = pygame.time.get_ticks()
            self.y = self.base_y + math.sin(time * self.bob_speed + self.bob_phase) * self.bob_amplitude
            self.animation.update()             
        # Else glide with no vertical movement and hold glide frame
        else:
            self.animation.set_frame(0)
            self.animation.timer = 0
            # Makes gliding half the time as flapping
            self.glide_timer += 1

        # Bigger margin for despawning, better consistency when player is rapidly moving
        despawn_margin = 60          
        parallax_x = self.x - scroll[0] * self.depth

        # Kill the bird if out of bounds of current screen and despawn_margin buffer
        if (self.direction == 1 and parallax_x > self.screen_width + despawn_margin) or \
        (self.direction == -1 and parallax_x < -despawn_margin):
            self.dead = True

    # Displays birds on screen with potential hitbugs, works with and without parallax (start menu)
    def render(self, surface, game=None, offset=None):
        img = self.animation.img()  
        if self.flip:
            img = pygame.transform.flip(img, True, False) 

        x, y = self.x, self.y
        # Apply parallax effect based on depth        
        if offset:
            x -= offset[0] * self.depth
            y -= offset[1] * self.depth * .21
        surface.blit(img, (int(x), int(y)))  

        # Debug red circle for bird spawn points
        if game and getattr(game, "debug_hitboxes", False):
            pygame.draw.circle(surface, (255, 0, 0), (int(x), int(y)), 4)

# Handles multiple bird instances
class Sparrows:
    def __init__(self, game):
        self.game = game
        self.enabled = False  
        self.bird_type = None
        self.birds = []  
        self.spawn_timer = 0

    # Called in load_level, can load different bird types based on stage
    def configure(self, theme_data):
        self.bird_type = theme_data.get("bird")  
        self.enabled = bool(self.bird_type) 
        self.birds.clear()  
        self.spawn_timer = 0 

    # Handles bird spawning and updates individual birds
    def update(self):
        # Skip if not configured
        if not self.enabled or not self.bird_type:
            return  

        self.spawn_timer += 1
        # Get animation frames
        if self.spawn_timer >= random.randint(60, 240) and len(self.birds) < 6 and random.random() < 0.15:
            frames = self.game.assets.get(self.bird_type)  
            if frames:
                # Create new bird with random animation duration
                animation = Animation(frames, img_dur=random.randint(6, 10), loop=True)
                bird = Sparrow(animation, self.game.display.get_size(), self.game.scroll)
                self.birds.append(bird)  
            # Reset spawn timer after a new bird is made
            self.spawn_timer = 0  
        # Remove dead birds
        for bird in self.birds[:]:  
            bird.update(self.game.scroll)
            if bird.dead:
                self.birds.remove(bird) 

    # Handles calling render for all sparrows
    def render(self, surface, offset = (0,0)):
        for bird in self.birds:
            # Render each bird with current game scroll offset
            bird.render(surface, game=self.game, offset=offset)
