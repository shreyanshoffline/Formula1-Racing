from pygame.math import Vector2

class Camera:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.pos = Vector2(0,0)

    def update(self, target: Vector2):
        self.pos = Vector2(target)

    def world_to_screen(self, p):
        return Vector2(p) - self.pos + Vector2(self.w/2, self.h/2)

    def resize(self, w, h):
        self.w = w
        self.h = h