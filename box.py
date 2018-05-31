from utilities import *
import math


class Box(object):
    """Represents a moving box on screen"""
    def __init__(self, rect, color, direction=None):
        """Make a new Box object.
        'Direction is a utilities.Direction object.
        'color' is a utilities.Colors object.
        'rect' is a pygame.Rect object"""
        self.direction = direction
        self.rect = rect
        self.color = color

    #def step(self):
    #    """Move the box box one step according to its direction"""
    #    if self.direction is None:
    #        print("Cannot use Box.step() when Box.direction is None.")
    #        return None
    #    self.move(self.direction.speed * math.cos(math.radians(self.direction.direction)), self.direction.speed * math.sin(math.radians(self.direction.direction)), newd=False)

    def move(self, x, y, newd=True):
        """Moves the Box by the given offset like pygame.rect.move, updates self.rect.
        If newd is True update the direction value of the Box to match the movement."""
        if newd:
            self.direction.speed = math.sqrt((x ** 2) + (y ** 2))
            self.direction.direction = calc_direction(x, y)
        self.rect = self.rect.move(x, y)


def calc_direction(x, y):
    """Calculates the directions of an object after moving with offsets."""
    if x == 0:
        if y > 0:
            return 180
        return 0
    if y == 0:
        if x > 0:
            return 90
        return 270
    if x > 0:
        if y > 0:
            return 180 - math.degrees(math.atan2(x, y))
        return 90 - math.degrees(math.atan2(abs(y), x))
    else:
        if y > 0:
            return 270 - math.degrees(math.atan2(y, abs(x)))
        return 360 - math.degrees(math.atan2(abs(x), abs(y)))
