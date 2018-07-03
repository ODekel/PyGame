import pygame
import sys
import imp
import socket
import threading
character = imp.load_source("character", "modules\\character.py")
Character = character.Character
game = imp.load_source("game", "modules\\game.py")
Game = game.Game
Sock = imp.load_source("game_sock", "modules\\game_sock.py").Sock


RESOLUTION = (1280, 720)
FLAGS = 0
DEPTH = 32
CAPTION = "PYGAME BATTLE ROYALE"
PORT = 5233


def main():
    ip = raw_input("Server IP: ")
    # ip = "localhost"  # For Debugging
    server = Sock()
    try_connect(server, ip, PORT)
    screen = start_pygame(RESOLUTION, FLAGS, DEPTH, CAPTION)
    my_game = start_game_class(screen, server)
    my_game.connect_to_server(Game.server_character)
    threading.Thread(target=my_game.handle_movement_online).start()
    while not my_game.exit:
        call_utilities(my_game)
        pygame.time.Clock().tick(my_game.fps)


def call_utilities(my_game):
    """
    Calls my_game.utilities. Excepts pygame.error and and does nothing with it.
    :param my_game: A Game object.
    :return: None.
    """
    try:
        my_game.utilities()
    except pygame.error:
        pass  # Game ended (probably).


def try_connect(sock, ip, port):
    """
    Tries to connect to the server and exits the program if socket.error is raised.
    :param sock: A socket.socket object.
    :param ip: IP of server.
    :param port: Port to try to connect to.
    :return: None.
    """
    try:
        sock.connect((ip, port))
    except socket.error:
        raw_input("Could not connect to server. Press enter to exit.")
        sys.exit(0)


def start_pygame(resolution, flags, depth, caption="PyGame"):
    """Initializes pygame to run the game.
    Returns the screen surface.
    caption is the caption for the pygame window, other variables are the same as pygame.display.set_mode method."""
    pygame.init()
    pygame.register_quit(quit_func)    # Will be changed by Game class.
    surface = pygame.display.set_mode(resolution, flags, depth)
    pygame.display.set_caption(caption)
    return surface


def start_game_class(screen, server):
    """
    :param screen: For Game class initializer.
    :param server: For Game class initializer.
    :return: A Game object.
    """
    hero = Character(r"assets\ALLIES_player.png", 200, 4, 10, 15, 1, 5, {}, (1000, 1000))  # Not actually used.
    gamemap = r"assets\dungeon_map.jpg"
    allies = pygame.sprite.OrderedUpdates()
    enemies = pygame.sprite.OrderedUpdates()
    return Game(screen, gamemap, hero, allies, enemies, server)


def quit_func():
    """Function to call when quitting pygame"""
    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
