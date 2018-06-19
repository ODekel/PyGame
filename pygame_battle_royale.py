import pygame
import sys
import imp
import socket
import threading
character = imp.load_source("character", "modules\\character.py")
Character = character.Character
game = imp.load_source("game", "modules\\game.py")
Game = game.Game


RESOLUTION = (1280, 720)
FLAGS = 0
DEPTH = 32
CAPTION = "PYGAME BATTLE ROYALE"


def main():
    ip = raw_input("Server IP: ")
    # ip = "localhost"  # For Debugging
    game_with_game_class(ip)
    # game_main_loop(surface)
    # for offset in range(145):
    #    surface.blit(minimap.subsurface((0 + offset * 16, 0 + offset * 9, 720, 480)), (0, 0))
    #    surface.blit(character, get_center(surface, character))
    #    print(get_center(surface, character))
    #    # blit_image(surface, (0, 0), (0 + offset * 16, 0 + offset * 9, 720, 480), minimap)
    #    pygame.time.Clock().tick(fps)
    #    pygame.display.flip()
    # wait_keyboard(pygame.K_SPACE)
    # pygame.quit()


def game_with_game_class(ip):
    """The main loop of the using the Game class."""
    server = socket.socket()
    try:
        server.connect((ip, 5233))
    except socket.error:
        raw_input("Could not connect to server. Press enter to exit.")
        pygame.quit()
        sys.exit(0)
    screen = start_pygame(RESOLUTION, FLAGS, DEPTH, CAPTION)
    hero = Character(r"assets\ALLIES_player.png", 200, 4, 10, 15, 1, 5, {}, (1000, 1000))
    gamemap = r"assets\dungeon_map.jpg"
    allies = pygame.sprite.OrderedUpdates()
    enemies = pygame.sprite.OrderedUpdates()
    my_game = Game(screen, gamemap, hero, allies, enemies, server)
    my_game.connect_to_server()
    threading.Thread(target=my_game.handle_movement_online).start()
    while not my_game.exit:
        try:
            my_game.utilities()
        except pygame.error:
            pass    # Game ended.
        pygame.time.Clock().tick(my_game.fps)
    print("KGKGKGKGK")
    for t in threading.enumerate():
        print(t)


def start_pygame(resolution, flags, depth, caption="PyGame"):
    """Initializes pygame to run the game.
    Returns the screen surface.
    caption is the caption for the pygame window, other variables are the same as pygame.display.set_mode method."""
    pygame.init()
    pygame.register_quit(quit_func)
    surface = pygame.display.set_mode(resolution, flags, depth)
    pygame.display.set_caption(caption)
    return surface


def wait_keydown(*keys):
    """Waits for a keyboard press (Removes events from queue and throws all other key presses!).
    Returns the pressed event."""
    # pygame.event.poll()
    event = pygame.event.wait()
    while not (event.type == pygame.KEYDOWN and event.key in keys):
        event = pygame.event.wait()
    return event


def quit_func():
    """Function to call when quitting pygame"""
    pygame.quit()
    sys.exit(0)


# def game_main_loop(screen):
#     """The main loop for the game"""
#     xmap = 500
#     ymap = 500
#     minimap, character, fps, step = prepare_game_loop(screen, "assets\dungeon_map.jpg", "assets\game_character.png", xmap, ymap, 300)
#     # pygame.time.Clock().tick(float(1000) / float(60))
#     # event = wait_event(pygame.QUIT, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)
#     enemies = load_others(("assets\orc1-128.png", (2000, 2000)))
#     for enemy in enemies:
#         minimap.blit(enemy[0], enemy[1])
#     # orcs = [Character(pygame.image.load("assets\orc1-128.png").convert_alpha(), 200, 250, 10, 20, 1, 0, [], (1000, 1000))]
#     events = pygame.event.get()
#     while pygame.QUIT not in [event.type for event in events]:
#         xmap, ymap = game_pressed_keys_handle(xmap, ymap, step, minimap.get_width() - screen.get_width(), minimap.get_height() - screen.get_height())
#         charmap = minimap.subsurface((xmap, ymap, screen.get_width(), screen.get_height()))
#         game_screen_handle(screen, charmap, character)
#         pygame.time.Clock().tick(fps)
#         events = pygame.event.get()
#         # event = wait_event(pygame.QUIT, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)


# def prepare_game_loop(screen, map_image, character_image, xmap, ymap, speed):
#     """Prepare the variables for the game's main loop.
#     map_image - loads map for this image.
#     character_image - loads character from this image.
#     xmap, ymap - the coordinates to load map on (top left).
#     speed - Amount of pixels the character can move in a second."""
#     minimap = pygame.image.load(map_image).convert()
#     character = pygame.image.load(character_image).convert_alpha()
#     charmap = minimap.subsurface((xmap, ymap, screen.get_width(), screen.get_height()))
#     screen.blit(charmap, (0, 0))
#     screen.blit(character, get_center(screen, character))
#     pygame.display.flip()
#     fps = get_refresh_rate(win32api.EnumDisplayDevices())
#     step = float(speed) / float(fps)  # The amount of pixels to move each step
#     return minimap, character, fps, step


def load_others(*others):
    """Calls convert_alpha on all files and returns a list of pygame.surfaces for them.
    others are tuples of file names and coordinates: (file, (x, y)).
    Designed to work with game_screen_handle's others."""
    return [(pygame.image.load(other[0]).convert_alpha(), other[1]) for other in others]


def only_event_types(events, *types):
    """Returns a list with only the events which type is in types."""
    return [event for event in events if event.type in types]


def wait_event(*events):
    """Like wait_keydown for mouse(UP and DOWN with no button distinction!) and pygame.QUIT too."""
    ev = pygame.event.wait()
    while is_event(ev, events) is None:
        ev = pygame.event.wait()
    return ev


def game_keys_handle(events, xmap, ymap, step, x_upper_limit, y_upper_limit, x_lower_limit=0, y_lower_limit=0, pressed=False):
    """Handles a single pygame.KEYDOWN event in the game.
    xmap - x on map to change.
    ymap - y on map to change.
    step - change by how much.
    lower_limit - lower limit of xmap and ymap.
    upper_limit - upper limit of xmap and ymap.
    pressed - if True checks also pressed keys.
    Returns the new xmap and ymap in tuple: (xmap, ymap)"""
    for event in events:
        if event.key == pygame.K_w:
            ymap = limited_minus(ymap, step, y_lower_limit)
        if event.key == pygame.K_a:
            xmap = limited_minus(xmap, step, x_lower_limit)
        if event.key == pygame.K_s:
            ymap = limited_plus(ymap, step, y_upper_limit)
        if event.key == pygame.K_d:
            xmap = limited_plus(xmap, step, x_upper_limit)
    if pressed:
        xmap, ymap = game_pressed_keys_handle(xmap, ymap, step, x_upper_limit, y_upper_limit, x_lower_limit, y_lower_limit)
    return tuple([xmap, ymap])


def game_pressed_keys_handle(xmap, ymap, step, x_upper_limit, y_upper_limit, x_lower_limit=0, y_lower_limit=0):
    """Handles the held down keys in the game.
    Parameters help is the same as in game_keys_handle."""
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_w]:
        ymap = limited_minus(ymap, step, y_lower_limit)
    if pressed[pygame.K_a]:
        xmap = limited_minus(xmap, step, x_lower_limit)
    if pressed[pygame.K_s]:
        ymap = limited_plus(ymap, step, y_upper_limit)
    if pressed[pygame.K_d]:
        xmap = limited_plus(xmap, step, x_upper_limit)
    return tuple([xmap, ymap])


# def game_screen_handle(screen, backmap, character, others=()):
#     """Call this at the end of each frame to calculate and the next one and update the screen.
#     'screen' is the surface of the entire screen.
#     'backmap' is the map (background) to show behind characters. Recommended to be the same size as screen.
#     MUST be same size or smaller than screen.
#     'character' is the player character to show in the middle of the screen.
#     'others' are tuples of surfaces and the places to blit them on 'screen', (surface, (x, y)).
#     order of blitting from first to last: backmap, others, character."""
#     screen.blit(backmap, (0, 0))
#     for other in others:
#         screen.blit(other[0], other[1])
#     screen.blit(character, get_center(screen, character))
#     pygame.display.flip()


def is_event(ev, events):
    """Is ev in events. Returns the event ev if it is in events or None if it is not."""
    if ev.type in events:
        return ev
    if ev.type == pygame.KEYDOWN and ev.key in events:
        return ev
    return None


def limited_plus(add_to, add_by, limit):
    """A plus limited by limit value. if the result is bigger than limit returns limit."""
    return add_by + add_to if add_by + add_to <= limit else limit


def limited_minus(sub_from, sub_by, limit):
    """A minus limited by limit value. if the result is smaller than limit returns limit."""
    return sub_from - sub_by if sub_from - sub_by >= limit else limit


if __name__ == '__main__':
    main()
