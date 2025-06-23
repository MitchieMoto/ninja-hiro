# Cycles through images based on the amount of frames and length needed
class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
        
    # Returns a copy of itself
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    # Loops if a continual animation, else cycle only once
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    # Return a still image
    def img(self):
        return self.images[int(self.frame / self.img_duration)]

    # Sets an animation to a specific frame
    def set_frame(self, index):
        index = max(0, min(index, len(self.images) - 1))
        self.frame = self.img_duration * index
