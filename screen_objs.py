class ScreenObjects(object):
    """Represents a collection of objectss appearing on a game screen."""
    def __init__(self, screenmap, character, *others):
        """Create a new ScreenObjects object.
        screenmap is the map shown behind the screen (background).
        character is the character surface that will appear in the center of the screen.
        others are tuples of surfaces and their location on the screen (surface, (x, y))."""
        self.screenmap = screenmap
        self.character = character
        self.others = others
