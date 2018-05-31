import pygame


class Ability(object):
    """Represents an ability of a character in a game."""
    def __init__(self, visual, damage, activate_range, cooldown, buttons, explosion=0, healing=False, move=0):
        """Create an ability for a game.
        'visual' is an image file to show on the affected area of the ability (will be converted_alpha).
        'damage' is the amount of damage the ability does.
        'activate_range' is the range from which you can use an ability.
        'cooldown' is how many seconds do you have to wait after using an ability to use it again.
        'explosion' is the range the ability will affect. 0 for target only.
        if 'healing' is True the ability will heal allies instead of damaging enemies.
        'move' is the distance the ability caster will move forward with activation of the ability.
        Negative for backwards movement.
        'buttons' is the buttons to press to activate the ability."""
        self.surface = pygame.image.load(visual).convert_alpha()
        self.damage = damage
        self.activate_range = activate_range
        self.cooldown = cooldown
        self.explosion = explosion
        self.healing = healing
        self.move = move
        self.buttons = buttons
