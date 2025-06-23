import pygame
import random
from scripts.particle import Particle

# Handles crumble blocks, which shake once stepped on before falling
class CrumbleBlock:
    def __init__(self, game, tile, image, crumble_time=40, fall_time=60, gravity=0.6):
        self.game = game
        self.image = image
        self.crumble_time = crumble_time
        self.fall_time = fall_time
        self.gravity = gravity

        self.pos = [tile['pos'][0], tile['pos'][1]]
        self.rect = pygame.Rect(self.pos[0], self.pos[1], image.get_width(), image.get_height())

        self.state = "solid"
        self.timer = 0
        self.velocity_y = 0

    # Tracks player colision and state timers 
    def update(self):
        # Skip updates on dead blocks or when not on a level
        if self.game.dead or self.state == "gone":
            return

        player_rect = self.game.player.rect()

        if self.state == "solid":
            self.rect.topleft = self.pos

            # Trigger crumble only if player's feet actually align with top of block
            standing_on = player_rect.bottom == self.rect.top
            horizontally_overlapping = (
                player_rect.right > self.rect.left and
                player_rect.left < self.rect.right
            )
            # Start block crumble sequence
            if standing_on and horizontally_overlapping:
                self.state = "crumbling"
                self.timer = 0\
                # Currently the same sfx as a slide
                (self.game.sfx.get('crumble_start') or self.game.sfx['slide']).play()

        # Go from crumble state to falling state after timer completion
        elif self.state == "crumbling":
            self.timer += 1
            if self.timer >= self.crumble_time:
                self.state = "falling"
                self.timer = 0
                self.velocity_y = 0

        # Start the block's fall logic
        elif self.state == "falling":
            self.velocity_y += self.gravity
            self.pos[1] += self.velocity_y
            self.rect.y = int(self.pos[1])

            self.timer += 1
            if self.timer >= self.fall_time:
                self.state = "gone"

    # Only renders blocks in the appropriate state, addiong a slight shake  to crumble blocks
    def render(self, surf, offset=(0, 0)):
        if self.state != "gone":
            shake_offset = 0
            if self.state == "crumbling":
                shake_offset = random.randint(-1, 1)
            surf.blit(self.image, (self.rect.x - offset[0], self.rect.y + shake_offset - offset[1]))
        
    # Returns true when the block is in a walkable state
    def is_solid(self):
        return self.state in ("solid", "crumbling")
