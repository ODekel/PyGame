import pygame
# from utilities import *
import math
import socket
from sys import exit as sysexit
import threading
import pickle
import win32api


class Game(object):
    """Represents an object used to store data and help control a game."""
    def __init__(self, screen, game_map, hero, allies, enemies, server_socket=None):
        """Create a new game object.
        screen is the surface which is used to display the game on screen.
        __game_map is the map of the game (obviously) and is an image file.
        After the game starts, might have blitted images on it.
        hero is the Character object the player will play as.
        allies and enemies are pygame.sprite.OrderedUpdates objects. Each sprite's location is its location on game_map.
        containing all the allies and enemies of the hero respectively.
        self.fps is an automatically calculated refresh rate of the screen (might not work for multi-screen setups).
        You can change it as you like or not use it at all by passing vsync=False to update_screen.
        server_socket is the socket of the server for online games.
        If provided, game_map might change."""
        self.screen = screen
        self.__game_map = pygame.image.load(game_map).convert()
        self.hero = hero
        self.allies = pygame.sprite.OrderedUpdates(hero)
        self.allies.add(allies)
        self.enemies = enemies
        self.__minimap = pygame.image.load(game_map).convert()
        self._uppery = (self.__game_map.get_height()) - (self.screen.get_height() / 2)
        self._upperx = (self.__game_map.get_width()) - (self.screen.get_width() / 2)
        self._lowerx = self.screen.get_width() / 2
        self._lowery = self.screen.get_height() / 2
        self.fps = get_refresh_rate(win32api.EnumDisplayDevices())
        self.server_socket = server_socket
        self.__recv = False  # Turns to False when the client stops communicating with the server.
        self.__send = False  # Turns to False when the client stops communicating with the server.

    def __sendd(self, s):
        """
        Sends the string to the client.
        :param s: A string to send to the client.
        :return: None.
        """
        self.server_socket.sendall(s)

    def __send_by_size(self, s, header_size):
        """
        Sends by size to the client.
        :param s: A string to send to the client.
        :param header_size: The size (in bytes) of the header.
        :return: None.
        """
        self.server_socket.sendall(str(len(s)).zfill(header_size))
        self.server_socket.sendall(s)

    def __recvd(self, size):
        """
        Receive a string from the client.
        :param size: The size (in bytes) to receive. Max.
        :return: The string received.
        """
        return self.server_socket.recv(size)

    def __recv_by_size(self, header_size):
        """
        Receive by size a string from the client.
        :param header_size: The size (in bytes) of the header.
        :return: The string received.
        """
        size = int(self.server_socket.recv(header_size))
        return self.server_socket.recv(size)

    def handle_user_input(self):
        """Handles the used input for all keyboard, mouse and other keys. Changes the x and y of hero.rect.
        If pygame.QUIT is pressed, pygame.quit will be called."""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.stop_online_connection()
                pygame.quit()
        self.hero.rect.centerx, self.hero.rect.centery = self.handle_movement()

    def handle_movement(self):
        """
        Handle the value of new x and y of hero on map based on pressed keys and hero's attributes.
        :return: New x and y of hero.
        Return syntax: newx, newy.
        """
        newy = self.hero.rect.centery
        newx = self.hero.rect.centerx
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_w]:
            newy -= self.hero.speed
        if pressed[pygame.K_a]:
            newx -= self.hero.speed
        if pressed[pygame.K_s]:
            newy += self.hero.speed
        if pressed[pygame.K_d]:
            newx += self.hero.speed
        if newx != self.hero.rect.centerx and newy != self.hero.rect.centery:
            newx, newy = self._fix_diagonal_movement(newx, newy)
        return self._updatex(newx), self._updatey(newy)

    def connect_to_server(self):
        """
        self.server_socket must be provided. Connects the client to the server and allows to start the game.
        :return: True if succeeded, False otherwise.
        """
        try:
            self.sync_with_server()
            self.__info_for_server()
        except socket.error:
            return False
        return True

    def handle_movement_online(self):
        """
        server_sock must be a valid game server for this method to work.
        :return: None. This method will run until closed,
        constantly talking to the server and updating variables in the Game object.
        """
        self.__recv = True
        self.__send = True
        sender = threading.Thread(target=self.__handle_pressed_online())
        sender.start()
        receiver = threading.Thread(target=self.__handle_receiving_updates())
        receiver.start()
        sender.join()
        receiver.join()

    def __handle_pressed_online(self):
        """
        server_sock must be a valid game server for this method to work.
        :return: None. This method will run until closed,
        constantly sending info to the game server.
        """
        while self.__send:
            # pressed = pygame.key.get_pressed()
            # try:
            #     if pressed[pygame.K_w]:
            #         self.server_socket.sendall("K_w")
            #     if pressed[pygame.K_a]:
            #         self.server_socket.sendall("K_a")
            #     if pressed[pygame.K_s]:
            #         self.server_socket.sendall("K_s")
            #     if pressed[pygame.K_d]:
            #         self.server_socket.sendall("K_d")
            # except socket.error:
            #     _exit_msg("Communication Error.")
            try:
                self.__send_by_size(pickle.dumps(pygame.key.get_pressed()), 32)
            except socket.error:
                _exit_msg("Communication error.")
            pygame.time.Clock().tick(self.fps)

    def __handle_receiving_updates(self):
        """
        server_sock must be a valid game server for this method to work.
        :return: None. This method will run until closed,
        constantly receiving info from the game server.
        """
        while self.__recv:
            info = None
            try:
                info = self.__recv_by_size(32)
            except TypeError or socket.error:
                _exit_msg("Communication Error.")
            self._handle_online_info(info)

    def _handle_online_info(self, info):
        """Handles the info received from he server."""
        for line in info:
            group, pos, map_pos = Game.__character_info_online(line)
            self.__handle_character_info_online(group, pos, map_pos)

    @staticmethod
    def __character_info_online(info):
        """Gets the info (line) on a character as received from the server, and returns (group, pos, map_pos)"""
        words = info.split("~")
        group = words[0]
        pos = None
        if group != "HERO":
            pos = words[1]
            map_pos = words[2]
        else:
            map_pos = words[1]
        return group, pos, map_pos

    def __handle_character_info_online(self, group, pos, map_pos):
        """Changes the Game class attributes according to the info about the character received from the server."""
        # Always receives the center of the rect of the character it is repositioning.
        if group == "HERO":
            self.hero.rect.center = pickle.loads(map_pos)
        elif group == "ALLIES":
            if pos.isdecimal():
                if map_pos == "REMOVE":
                    self.allies.sprites()[int(pos)].kill()
                else:
                    self.allies.sprites()[int(pos)].rect.center = pickle.loads(map_pos)
            elif pos == "ADD":
                self.allies.add(pickle.loads(map_pos))
        elif group == "ENEMIES":
            if pos.isdecimal():
                if map_pos == "REMOVE":
                    self.enemies.sprites()[int(pos)].kill()
                else:
                    self.enemies.sprites()[int(pos)].rect.center = pickle.loads(map_pos)
            elif pos == "ADD":
                self.enemies.add(pickle.loads(map_pos))

    def stop_online_connection(self):
        """Stops the client from communicating with the server.
        Call this function when the game stops connection to the server for any reason."""
        try:
            if self.__send:
                self.server_socket.sendall("DISCONNECT")
        except socket.error:
            pass
        self.__recv = False
        self.__send = False

    def _updatex(self, newx):
        """Returns value of hero's x based on newx and limits of map."""
        if newx > self._upperx:
            return self._upperx
        elif newx < self._lowerx:
            return self._lowerx
        else:
            return newx

    def _updatey(self, newy):
        """Returns value of hero's y based on newy. and limits of map."""
        if newy > self._uppery:
            return self._uppery
        elif newy < self._lowery:
            return self._lowery
        else:
            return newy

    def _fix_diagonal_movement(self, newx, newy):
        """
        Fixes newx, newy so hero won't move too fast when moving diagonally.
        ASSUMES IT IS NEEDED FOR IT TO BE CALLED.
        :param newx: new character x after checking keys, before updating self.hero.
        :param newy: new character y after checking keys, before updating self.hero.
        :return: newx, newy.
        """
        return self.hero.rect.centerx + ((newx - self.hero.rect.centerx) / math.sqrt(2)),\
            self.hero.rect.centery + ((newy - self.hero.rect.centery) / math.sqrt(2))

    def update_screen(self, vsync=True):
        """Updates the screen of the game. Returns None."""
        screen_top, screen_left, screen_bottom, screen_right = self._get_screen_limits()
        self.sprite_updates()
        self.screen.blit(self.__game_map.subsurface((screen_left, screen_top, self.screen.get_width(),
                                                    self.screen.get_height())), (0, 0))
        pygame.display.flip()
        # UPDATE SO IT DOESN'T FLIP THE SCREEN WHEN NOT NEEDED.
        # if self.__heroposx == self.hero.rect.centerx and self.__heroposy == self.hero.rect.centery:
        #     # #self.screen.blit(self.__minimap.subsurface((screen_left, screen_top,
        #                                                 # self.screen.get_width(), self.screen.get_height())), (0, 0))
        #     pygame.display.update(self.sprite_updates())
        # else:
        #     self.screen.blit(self.__minimap.subsurface((screen_left, screen_top,
        #                                                self.screen.get_width(), self.screen.get_height())), (0, 0))
        #     self.sprite_updates()
        #     pygame.display.flip()
        #     self.__heroposx = self.hero.rect.centerx
        #     self.__heroposy = self.hero.rect.centery
        if vsync:
            pygame.time.Clock().tick(self.fps)

    def sprite_updates(self):
        """
        Returns a list of pygame.rects that need to be updated.
        This func can be used with pygame.display.update.
        Always returns hero in the list too, in the last place in the list.
        Clears and draws all game attributes on __game_map, returns only the once seen on screen.
        """
        self.delete_last()
        outdated = []
        sc_top, sc_left, sc_bottom, sc_right = self._get_screen_limits()
        for rect in self.enemies.draw(self.__game_map) + self.allies.draw(self.__game_map):
            if rect.bottom > sc_top and rect.top < sc_bottom and rect.right > sc_left and rect.left < sc_right:
                self.screen.blit(self.__game_map, self._fit_rect(rect))
                outdated.append(self._fit_rect(rect))
        self.__game_map.blit(self.hero.image, self.hero.rect)
        self.screen.blit(self.hero.image, self._fit_rect(self.hero.rect))
        outdated.append(self._fit_rect(self.hero.rect))
        return outdated

    def delete_last(self):
        """Deletes hero, enemies and allies from __game_map."""
        self.allies.clear(self.__game_map, self.__minimap)
        self.enemies.clear(self.__game_map, self.__minimap)
        self.__game_map.blit(self.__minimap.subsurface(self.hero.rect), self.hero.rect)

    def _get_screen_limits(self):
        """
        :return: The screen limits in relation to __game_map. (Inside __game_map). top, left, bottom, right.
        """
        return self.hero.rect.centery - (self.screen.get_height() / 2),\
            self.hero.rect.centerx - (self.screen.get_width() / 2),\
            self.hero.rect.centery + (self.screen.get_height() / 2),\
            self.hero.rect.centerx + (self.screen.get_width() / 2)

    def _fit_rect(self, rect):
        """
        :param rect: A pygame.rect object on self.__game_map, at least partially on self.screen
        (calculated by self.hero)(coordinates-wise).
        :return: The rect to draw on screen.
        """
        sc_top, sc_left, sc_bottom, sc_right = self._get_screen_limits()
        return rect.fit(self.screen.get_rect(top=sc_top, bottom=sc_bottom, left=sc_left, right=sc_right))

    def sync_with_server(self, timeout=socket.getdefaulttimeout()):
        """Connect to the game's server using the sock provided,
        which must already be TCP connected to the server connection port.
        Returns a socket.socket object that is TCP connected to the game server."""
        self.server_socket.setdefaulttimeout(timeout)
        try:
            if self.server_socket.recv(11) != "GAME SERVER":
                raise socket.error
            self.server_socket.sendall("GAME CLIENT")
            connect = self.server_socket.recv(32).split(" ")
            if connect[0] != "CONNECTED":
                raise socket.error
            if int(connect[1]) != self.server_socket.getpeername()[1]:
                return self.sync_with_server(self.__connect_to_new_server(int(connect[1])))
        except socket.error or TypeError:
            _exit_msg("Unable to connect to server.")
        return self.server_socket

    def __connect_to_new_server(self, new_port):
        """Connects to a new server if sync_with_server needs it."""
        ip, port = self.server_socket.getpeername()
        self.server_socket.close()
        self.server_socket = socket.socket()
        self.server_socket.connect((ip, new_port))
        return self.server_socket

    def __info_for_server(self):
        """
        self.server_socket must be a valid game socket.
        :return: True if succeeded, False otherwise.
        """
        try:
            if self.__recvd(10) == "CHARACTER?":
                self.__send_by_size(pickle.loads(self.hero), 32)
            else:
                self.stop_online_connection()
                return False
            if self.__recvd(5) == "TEAM?":
                self.__send_by_size("RED", 32)
            else:
                self.stop_online_connection()
                return False
            if self.__recvd(4) == "FPS?":
                self.__send_by_size(str(self.fps), 32)
            else:
                self.stop_online_connection()
                return False
            if self.__recvd(16) == "RESOLUTION WIDTH":
                self.__send_by_size(str(self.screen.get_width()), 32)
            else:
                self.stop_online_connection()
                return False
            if self.__recvd(17) == "RESOLUTION HEIGHT":
                self.__send_by_size(self.screen.get_height(), 32)
            else:
                self.stop_online_connection()
                return False
            if self.__recvd(6) == "OK END":
                pass
            else:
                self.stop_online_connection()
                return False
            self.__sendd("MAP NAME")
            map_name = self.__recv_by_size(32)
            self._update_map(map_name)
            return True
        except socket.error:
            self.stop_online_connection()
            _exit_msg("Could not connect to server.")

    def _update_map(self, map_name):
        """Updates the map of the game from 'assets'."""
        self.__game_map = pygame.image.load("assets\\" + map_name).convert()
        self.__minimap = pygame.image.load("assets\\" + map_name).convert()


def _exit_msg(msg):
    """Displays the message and waits for Enter press to exit."""
    raw_input(msg + " Press Enter to exit.")
    pygame.quit()
    sysexit(0)


def get_refresh_rate(device):
    """Returns the refresh rate of the monitor."""
    return getattr(win32api.EnumDisplaySettings(device.DeviceName, -1), "DisplayFrequency")
