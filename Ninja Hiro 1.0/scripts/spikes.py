import pygame
import math
import random
from scripts.spark import Spark
from scripts.particle import Particle

# Handles spikes as harmful tiles, with trigger based damage and collision
class Spike:
    def __init__(self, game, tile):
        self.game = game
        self.cooldown = 0
        self.x = tile['pos'][0]
        self.y = tile['pos'][1] 
        self.variant = tile.get('variant', 0)
        self.image = game.assets['spikes'][self.variant]

        # Check above and below to determine a given spike orientation, gaurds against spikes that are a full tile size
        above = game.tilemap.solid_check((self.x + 8, self.y - 4))
        below = game.tilemap.solid_check((self.x + 8, self.y + 18))
        if above:
            self.type = 'ceiling'
        elif below:
            self.type = 'floor'
        else:
            self.type = 'floor'  # Default to floor 

        # Define hitbox depending on tile type, ceiling or floor
        if self.type == 'floor':
            # Shifts the hitbox down 10 blocks, allows small clearance
            self.hitbox = pygame.Rect(self.x, self.y + 10, 16, 6)
        else:
            # Must slide to pass through a ceiling type 
            self.hitbox = pygame.Rect(self.x, self.y, 16, 6)

    # Handles player collision with spikes, invulnerability and collision
    def update(self):
        if self.game.dead:
            return
        player = self.game.player

        # Check for player and spike collision
        if self.hitbox.colliderect(player.rect()):
            # Collision is ignored if player is currently invulnerable to the spike
            if self.type == 'floor' or (self.type == 'ceiling' and not player.sliding):
                if player.smoke_active_timer > 0:
                    return
                # If still in grace period after breaking a shield, ignore spike
                if player.spike_grace_timer > 0:
                    return
                # First removes a player's shield
                if player.has_sushi_shield:
                    player.has_sushi_shield = False
                    self.game.sfx.get('sushi_shield_shatter', self.game.sfx['hit']).play()
                # Else kill the player
                else:
                    if not self.game.dead:
                        player.die()
                # Start global grace period for spikes
                player.spike_grace_timer = 60  # 1 second

    # Displays spikes
    def render(self, surf, offset=(0, 0)):
        # Flip variant 0 if ceiling spike, leave variant 1 untouched, as it is already upside down
        if self.type == 'ceiling':
            image = self.image if self.variant == 1 else pygame.transform.flip(self.image, False, True)
        else:
            image = self.image
        surf.blit(image, (self.x - offset[0], self.y - offset[1]))
