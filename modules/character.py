import pygame
import pickle
import copy


class Character(pygame.sprite.Sprite):
    """A character in a pygame game. Inherits from pygame.sprite.Sprite.
    If you want to update the Character's position on a map, update using Character.rect."""

    def __init__(self, visual, health, speed, damage, attack_range, attack_speed, death_timer, abilities, location):
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
        self.rect = self.image.get_rect(center=location)
        self.health = health
        self.speed = speed
        self.damage = damage
        self.attack_range = attack_range
        self.attack_speed = attack_speed
        self.death_timer = death_timer
        self.abilities = abilities

    @property
    def location(self):    # A simpler way of changing the character's location.
        return self.rect.center

    @location.setter
    def location(self, value):    # A simpler way of changing the character's location.
        self.rect.center = value

    def pickled_no_image(self):
        """Returns a string with the Character object pickled but image is set to None
        since Surface objects cannot be pickled."""
        temp_image = self.image.copy()
        self.image = None
        pickled = pickle.dumps(self)
        self.image = temp_image
        return pickled

    def character_no_image(self):
        """Returns a copy of the same Character object, without the image.
        Mainly used for pickling."""
        temp_image = self.image.copy()
        self.image = None
        char = copy.deepcopy(self)
        self.image = temp_image
        return char
