import pygame
# from utilities import *


class Character(pygame.sprite.Sprite):
    """A character in a pygame game. Inherits from pygame.sprite.Sprite.
    If you want to update the Character's position on a map, update using Character.rect."""
    def __init__(self, visual, health, speed, damage, attack_range, attack_speed, death_timer, abilities, center):
        """Create a new game character.
        'visual' is an image file (will be converted_alpha, so transparent background is supported).
        'health' and 'damage' are integers.
        'speed' is how fast can the character move.
        'damage' is the amount of damage the character does per attack.
        'attack_range' is an integer representing range from which this character can attack.
        'attack_speed' is how many times can the character attack per second.
        'death_timer' is an integer representing how many seconds
        it takes for the character to return to life after it died. 0 for permadeath.
        'abilities' is the dictionary of Ability objects for the character where the key is the name of the ability.
        'center' is where the center of the character will be on the game's map."""
        super(Character, self).__init__()
        self.image = pygame.image.load(visual).convert_alpha()
        self.rect = self.image.get_rect(center=center)
        self.health = health
        self.speed = speed
        self.damage = damage
        self.attack_range = attack_range
        self.attack_speed = attack_speed
        self.death_timer = death_timer
        self.abilities = abilities
