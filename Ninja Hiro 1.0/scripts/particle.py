# Base particle class, runs for a full animation cycle
class Particle:
    def __init__(self, game, p_type, pos, velocity=[0, 0], frame=0, alpha=255):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = list(velocity)
        self.animation = self.game.assets['particle/' + p_type].copy()
        self.animation.frame = frame
        self.alpha = alpha 
    
    # Runs a full animation of the particle
    def update(self):
        kill = False
        if self.animation.done:
            kill = True
        # Updates particle positioning for each frame of the animation
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.animation.update()
        # Returns true when the animation is finished
        return kill
    
    # Centers and displays objects with potential fade with alpha
    def render(self, surf, offset=(0, 0)):
        img = self.animation.img()
        if self.alpha < 255:
            img = img.copy()
            img.set_alpha(self.alpha)
        surf.blit(img, (
            self.pos[0] - offset[0] - img.get_width() // 2,
            self.pos[1] - offset[1] - img.get_height() // 2
        ))
