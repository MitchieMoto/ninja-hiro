import random

# A cloud which follows player movement and slowly drifts right
class Cloud:
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth
    
    # Slow innate right movement
    def update(self):
        self.pos[0] += self.speed
        
    # Follows the players movements with parallax horizontal wrapping 
    def render(self, surf, offset=(0, 0)):
        render_pos = (
            self.pos[0] - offset[0] * self.depth,
            self.pos[1] - offset[1] * self.depth * 0.21 # Keeps the clouds "higher" away 
        ) 
        # Wraps the clouds horizontally, reusing them, no vertical wrapping
        render_x = render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width()
        render_y = render_pos[1] 
        surf.blit(self.img, (render_x, render_y))

# Manages multiple cloud instances
class Clouds:
    def __init__(self, cloud_images, screen_height, count=8):
        self.clouds = []
        max_cloud_height = max(img.get_height() for img in cloud_images)

        # Append all clouds with randomized attributes given the count 
        for i in range(count):
            x = random.random() * 99999
            y = random.uniform(0, max(0, screen_height / 8 - max_cloud_height))
            img = random.choice(cloud_images)
            speed = random.random() * 0.05 + 0.05
            depth = random.random() * 0.6 + 0.2
            self.clouds.append(Cloud((x, y), img, speed, depth))

        # Sort clouds by depth, so further clouds are rendered first
        self.clouds.sort(key=lambda x: x.depth)

    # Keeps the clouds moving
    def update(self):
        for cloud in self.clouds:
            cloud.update()

    # Displays the clouds
    def render(self, surf, offset=(0, 0)):
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)
