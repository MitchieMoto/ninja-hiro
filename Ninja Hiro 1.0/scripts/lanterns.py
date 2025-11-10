import pygame
import random
import math

# Defines lanterns according to their size, with parallax and glow
class Lanterns:
    def __init__(self, images, screen_size, count=12):
        self.images = images
        self.screen_width, self.screen_height = screen_size
        self.depths = [0.8, 0.6, 0.3]  # the smaller lanterns are "closer"
        self.lanterns = [self._create_lantern() for _ in range(count)]

    # Returns lantern dicts according to a random size and its given depth
    def _create_lantern(self):
        size_index = random.randint(0, 2)
        img = self.images[size_index]
        x = random.uniform(-self.screen_width, self.screen_width) 
        # Spawn only on the top half of the screen 
        y = random.randint(0, self.screen_height // 2)

        return {
            "img": img,
            "pos": [x, y],
            "depth": self.depths[size_index],
            "size_index": size_index,
            "bob_phase": random.uniform(0, math.tau)
        }

    # Natural gentle bobbing effect on lanterns
    def update(self):
        current_time = pygame.time.get_ticks()
        for lantern in self.lanterns:
            lantern["pos"][1] += math.sin(current_time / 1500 + lantern["bob_phase"]) * 0.1

    # Draws the lanterns and a bloom effect
    def render(self, surface, offset=(0, 0)):
        for lantern in self.lanterns:
            img = lantern["img"]

            # Wrap the lanterns horizontally and vertically
            render_pos = (
                lantern["pos"][0] - offset[0] * lantern["depth"],
                lantern["pos"][1] - offset[1] * lantern["depth"] * 0.21 # Keeps the clouds "higher" away 
            )
            x = render_pos[0] % (surface.get_width() + img.get_width()) - img.get_width()
            y = render_pos[1] % (surface.get_height() + img.get_height()) - img.get_height()

            # Draw a double layered bloom effect 2 and 6 pixels away from the lanterns
            for blur in [1,3]:
                bloom = pygame.transform.smoothscale(
                    img,
                    (
                        img.get_width() + blur * 2,
                        img.get_height() + blur * 2
                    )
                )
                surface.blit(bloom, (x - blur, y - blur), special_flags=pygame.BLEND_ADD)
            # Draws the actual lanterns
            surface.blit(img, (x, y))
