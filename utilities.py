from pygame import Color


class Colors(object):
    """Colors in 32 depth pygame surface"""
    white = Color(255, 255, 255, 255)
    black = Color(0, 0, 0, 255)
    blue = Color(0, 0, 255, 255)
    green = Color(0, 255, 0, 255)
    red = Color(255, 0, 0, 255)
    gray = Color(128, 128, 128, 255)
    purple = Color(128, 0, 128, 255)
    teal = Color(0, 128, 128, 255)
    yellow = Color(255, 255, 0, 255)
    transparent = Color(0, 0, 0, 0)

    def __init__(self, (red, green, blue), alpha=255):
        """Make a color. alpha is transparency, 0 is invisible and 255 is no transparency."""
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha
        self.color = Color(red, green, blue, alpha)


class Direction(object):
    """Directions for a moving object"""
    def __init__(self, speed, direction):
        """Make a new Direction object.
        'speed' is an int.
        'direction' is the angle the object will be moving at. 0 is up and going clockwise"""
        self.speed = speed
        self.direction = direction
