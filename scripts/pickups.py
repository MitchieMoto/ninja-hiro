import pygame
import math

# Handles all pickups
class pickup:
    def __init__(self, game, pos, pickup_type, image):
        self.game = game
        self.base_pos = list(pos)
        self.type = pickup_type
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.timer = 0

    # Bobs the pickups and tracks for player collision, applying the appropriate effect
    def update(self):
        # Handles a slight bob effect for pickup items
        self.timer += 1
        bob_offset = math.sin(self.timer * 0.05) * 2
        self.rect.centery = self.base_pos[1] + bob_offset
        
        # Defines all player pickup interactions and plays appropriate sfx
        if self.rect.colliderect(self.game.player.rect()):
            if self.type == 'ramen':
                self.game.player.dash_cooldown_multiplier = 0.5
                self.game.player.ramen_timer = 15 * 60
                if 'pickup_spicy_ramen' in self.game.sfx:
                    self.game.sfx['pickup_spicy_ramen'].play()
            elif self.type == 'sushi':
                self.game.player.has_sushi_shield = True
                if 'pickup_sushi_shield' in self.game.sfx:
                    self.game.sfx['pickup_sushi_shield'].play()
            elif self.type == 'spirit_blessing':
                self.game.player.has_spirit_blessing = True
                self.game.sfx['pickup_spirit_blessing'].play()
            return True
        return False

    # Displays the pickups with the bobbing
    def render(self, surf, offset):
        surf.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))
