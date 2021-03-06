import pygame
import math
import socket
import threading
import pickle
import win32api
import imp
Sock = imp.load_source("game_sock", "modules\\game_sock.py").Sock


DEBUG = False


class Game(object):
    """Represents an object used to store data and help control a game.
    Once a Game object is initialized, it calls pygame.register_quit with his own quit func."""

    ally_team = "ALLIES"
    enemy_team = "ENEMIES"
    FUNCTION_KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]
    SERVER_KICK_MSG = "PLAYER KICKED"

    server_character = "SERVER SIDE"
    client_character = "CLIENT SIDE"

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
        server_socket is the Sock of the server for online games.
        If provided, game_map might change according to the server."""
        self.screen = screen
        self.__game_map = pygame.image.load(game_map).convert()
        self.hero = hero
        self.allies = allies
        self.enemies = enemies
        self.__minimap = pygame.image.load(game_map).convert()
        self._uppery = (self.__game_map.get_height()) - (self.screen.get_height() / 2)
        self._upperx = (self.__game_map.get_width()) - (self.screen.get_width() / 2)
        self._lowerx = self.screen.get_width() / 2
        self._lowery = self.screen.get_height() / 2
        self.fps = get_refresh_rate(win32api.EnumDisplayDevices())
        self.server_socket = server_socket
        self.timeout = 0.1
        self.__recv = False  # Turns to False when the client stops communicating with the server.
        self.__send = False  # Turns to False when the client stops communicating with the server.
        pygame.register_quit(self.quit_func)
        # self.__inactive_timeout = None
        self.__exit = False

    @property
    def exit(self):
        """If True, program should exit."""
        return self.__exit

    def handle_user_input(self):
        """Handles the used input for all keyboard, mouse and other keys. Changes the x and y of hero.rect.
        If pygame.QUIT is pressed, pygame.quit will be called."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
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

    def connect_to_server(self, character_side):
        """
        self.server_socket must be provided. Connects the client to the server and allows to start the game.
        :param character_side: Character object determined by client or server.
        Use Game.server_character and Game.client_character to choose.
        :return: True if succeeded, False otherwise.
        """
        try:
            self.__waiting_for_players()
            self.sync_with_server()
            self.__info_for_server(character_side)
        except socket.error:
            return False
        return True

    def __waiting_for_players(self):
        """Handles the communication with the server while it is waiting for all players to connect."""
        default_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.timeout)
        if self.server_socket.recv_by_size() == "WAITING":
            print("Waiting for other players to connect...")
            socket.setdefaulttimeout(None)
            if not self.server_socket.recv_by_size() == "CONTINUE":
                raise (socket.error, "Server did not answer correctly to the request.")
        socket.setdefaulttimeout(default_timeout)

    def _wait_for_string(self, s):
        """
        Waits for string from server, while making sure pygame doesn't crash.
        :param s: The string to wait for.
        :return: True if received continue, False otherwise.
        """
        default_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.timeout)
        did_get_string = None
        while did_get_string is None:    # Doesn't really run forever...
            try:
                if self.server_socket.recv_by_size() == s:
                    did_get_string = True
                else:
                    did_get_string = False
            except socket.timeout:
                self.utilities()    # Make sure pygame doesn't crash while the server is waiting for players to connect.
        socket.setdefaulttimeout(default_timeout)
        return did_get_string

    def _get_game_state(self):
        """Get the state of the game when connecting to server.
        Returns True if succeeded, False otherwise."""
        if self.server_socket.recv_by_size() != "ALLIES":
            return False
        lst_allies = pickle.loads(self.server_socket.recv_by_size())
        if self.server_socket.recv_by_size() != "ENEMIES":
            return False
        lst_enemies = pickle.loads(self.server_socket.recv_by_size())
        Game._fix_team_image(lst_allies, Game.ally_team)    # Since pygame.surface objects cannot be pickled,
        Game._fix_team_image(lst_enemies, Game.enemy_team)  # Character object are sent without image.
        self.allies = pygame.sprite.OrderedUpdates(*lst_allies)
        self.enemies = pygame.sprite.OrderedUpdates(*lst_enemies)
        if self.server_socket.recv_by_size() != "HERO POS":
            return False
        try:
            self.hero = self.allies.sprites()[int(self.server_socket.recv_by_size())]
        except ValueError:
            return False
        return True

    def handle_movement_online(self):
        """
        server_sock must be a valid game server for this method to work.
        :return: None. This method will run until closed,
        constantly talking to the server and updating variables in the Game object.
        """
        debug_print("HANDLE")
        if not self._get_game_state():
            raise socket.error("synchronizing failed")
        self.__recv = True
        self.__send = True
        sender = threading.Thread(target=self.__handle_pressed_online)
        receiver = threading.Thread(target=self.__handle_receiving_updates)
        sender.start()
        receiver.start()
        debug_print("HANDLER @")

    def utilities(self):
        """Must be called in a non-ending loop. Recommended to wrap in try and except block of pygame.error."""
        if self.server_socket is None or (self.__send or self.__recv):
            self.update_screen()
        self._handle_events()

    def _handle_events(self):
        """Handles the events of pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop_online_connection()
                pygame.quit()

    def __handle_pressed_online(self):
        """
        server_sock must be a valid game server for this method to work.
        :return: None. This method will run until closed,
        constantly sending info to the game server.
        """
        self.__send = True
        self.server_socket.settimeout(self.timeout)
        cnt = 0
        while self.__send:
            try:
                functional = Game._functional_keys_dict(pygame.key.get_pressed())
                if functional is not None:    # No need to send if nothing is pressed
                    self.server_socket.send_by_size(pickle.dumps(functional, pickle.HIGHEST_PROTOCOL))
                    debug_print("sent: ", str(cnt))
                    cnt += 1
            except socket.timeout:
                Game._exit_msg("You were inactive for too long, and kicked out of the game.")
            except socket.error:
                self.__handle_send_socket_error()
            else:
                pygame.time.Clock().tick(self.fps)

    @staticmethod
    def _functional_keys_dict(pressed):
        """Returns a dictionary with only the functional keys, True or False."""
        one_true = False
        functional = {}
        for key in Game.FUNCTION_KEYS:
            key_bool = pressed[key]
            if key_bool:
                one_true = True
            functional[key] = key_bool
        return functional if one_true else None

    def __handle_receiving_updates(self):
        """
        server_sock must be a valid game server for this method to work.
        :return: None. This method will run until closed,
        constantly receiving info from the game server.
        """
        self.__recv = True
        self.server_socket.settimeout(self.timeout)
        cnt = 0
        while self.__recv:
            try:
                info = self.server_socket.recv_by_size()
                debug_print("recv: ", str(cnt))
                debug_print(info)
                cnt += 1
                self._handle_online_info(info)
            except socket.timeout:
                pass    # Constantly to keep running smoothly.
            except (TypeError, socket.error):
                self.__handle_recv_socket_error()
            except pygame.error:
                pass   # Game quit.
            else:
                try:
                    self._handle_events()
                except pygame.error:
                    pass   # Game quit.

    def _handle_online_info(self, info):
        """Handles the info received from he server."""
        if self._online_info_check_end(info):
            raise pygame.error  # End the loop if Player is kicked out of the game.
        for line in [line for line in info.split("\n\n") if line != ""]:  # 2 newlines in a row separate each line.
            self.__handle_character_info_online(line)

    def _online_info_check_end(self, info):
        """Checked if the server ended the game/kicked the player, and handles it.
        Returns True if Player was kicked from the server, False otherwise, or if error syntax is wrong."""
        try:
            if info[:len(Game.SERVER_KICK_MSG)] == Game.SERVER_KICK_MSG:    # Server kicked player.
                self.handle_end_game(info.split("~")[1])
                return True
        except IndexError:
            return False
        return False

    def __handle_character_info_online(self, info):
        """Gets the info (line) on a character as received from the server, and returns (group, pos, map_pos)"""
        parts = info.split("~")
        action = parts[0]
        if action == "UPDATE":
            self.__change_character_attribute(parts[1], parts[2], parts[3], "~".join(parts[4:]))
        elif action == "ADD":
            self.__add_character(parts[1], "~".join(parts[2:]))
        elif action == "REMOVE":
            self.__remove_character(*parts[1:])

    def __change_character_attribute(self, side, index, attribute, pickled_value):
        """Change a character's attribute according to data received from the server."""
        if side == Game.ally_team:
            setattr(self.allies.sprites()[int(index)], attribute, pickle.loads(pickled_value))
        else:
            setattr(self.enemies.sprites()[int(index)], attribute, pickle.loads(pickled_value))

    def __add_character(self, side, pickled_character):
        """Adds a character to the game according to data received from the server."""
        character = pickle.loads(pickled_character)
        if side == Game.ally_team:
            character.image = Game.get_team_image(Game.ally_team)
            self.allies.add(character)
        else:
            character.image = Game.get_team_image(Game.enemy_team)
            self.enemies.add(character)

    def __remove_character(self, side, index):
        """Removes a character from the game according to data received from the server."""
        if side == Game.ally_team:
            self.allies.sprites()[int(index)].kill()
        else:
            self.enemies.sprites()[int(index)].kill()

    def __handle_recv_socket_error(self):
        """When there's a socket error on __handle_receiving_updates, this function handles it."""
        if not self.__recv:
            return
        debug_print("Error on receiving.")
        Game._exit_msg("Communication Error.")

    def __handle_send_socket_error(self):
        """When there's a socket error on __handle_pressed_online, this function handles it."""
        if not self.__send:
            return
        debug_print("Error on sending.")
        Game._exit_msg("Communication error.")

    @staticmethod
    def _fix_team_image(chars, team):
        """calls Game.get_team_image on each character in chars, with team as parameter."""
        for char in chars:
            char.image = Game.get_team_image(team)

    @staticmethod
    def get_team_image(team):
        """Updates the image of the character."""
        return pygame.image.load("assets\\" + team + "_player.png").convert_alpha()

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
        self.screen.blit(self.__game_map.subsurface(pygame.Rect(screen_left, screen_top, self.screen.get_width(),
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
        self.erase_last()
        outdated = [self._fit_rect(self.hero.rect)]    # Always returns hero's rect.
        sc_top, sc_left, sc_bottom, sc_right = self._get_screen_limits()
        for rect in self.enemies.draw(self.__game_map) + self.allies.draw(self.__game_map):
            if rect.bottom > sc_top and rect.top < sc_bottom and rect.right > sc_left and rect.left < sc_right:
                self.screen.blit(self.__game_map, self._fit_rect(rect))
                outdated.append(self._fit_rect(rect))
        self.draw_hero()
        return outdated

    def erase_last(self):
        """erases hero, enemies and allies from __game_map. Does not update/flip the screen."""
        self.allies.clear(self.__game_map, self.__minimap)
        self.enemies.clear(self.__game_map, self.__minimap)
        self.erase_hero()

    def erase_hero(self):
        """Erases the hero from __game_map. Does not update/flip the screen."""
        self.__game_map.blit(self.__minimap.subsurface(self.hero.rect), self.hero.rect)

    def draw_hero(self):
        """Draws the hero to __game_map. Does not update/flip the screen."""
        self.__game_map.blit(self.hero.image, self.hero.rect)

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

    def sync_with_server(self):
        """Connect to the game's server using the sock provided,
        which must already be TCP connected to the server connection port.
        Returns a Sock object that is TCP connected to the game server."""
        # self.server_socket.settimeout(self.timeout)
        try:
            if self.server_socket.recv_by_size() != "GAME SERVER":
                raise socket.error
            self.server_socket.send_by_size("GAME CLIENT")
            connect = self.server_socket.recv_by_size().split(" ")
            if connect[0] != "CONNECTED":
                raise socket.error
            if int(connect[1]) != self.server_socket.getpeername()[1]:
                self.__connect_to_new_server(int(connect[1]))
                return self.sync_with_server()
        except socket.error or TypeError:
            Game._exit_msg("Unable to connect to server.")
        return self.server_socket

    def __connect_to_new_server(self, new_port):
        """Connects to a new server if sync_with_server needs it."""
        server_addr = self.server_socket.getpeername()
        self.server_socket.close()
        self.server_socket = Sock()
        self.server_socket.connect((server_addr[0], new_port))
        # self.server_socket.close()
        # temp_sock = Sock()
        # temp_sock.bind(("0.0.0.0", new_port))
        # temp_sock.listen(0)
        # self.server_socket, server_addr = temp_sock.accept()
        return self.server_socket

    def __info_for_server(self, character_side):
        """
        self.server_socket must be a valid game socket.
        :return: True if succeeded, False otherwise.
        """
        try:
            if character_side == Game.client_character:
                if self.server_socket.recv_by_size() == "CHARACTER?":
                    self.server_socket.send_by_size(self.hero.pickled_no_image())
                else:
                    self.stop_online_connection()
                    return False
            if self.server_socket.recv_by_size() == "TEAM?":
                self.server_socket.send_by_size("RED")
            else:
                self.stop_online_connection()
                return False
            if self.server_socket.recv_by_size() == "FPS?":
                self.server_socket.send_by_size(str(self.fps))
            else:
                self.stop_online_connection()
                return False
            if self.server_socket.recv_by_size() == "RESOLUTION WIDTH":
                self.server_socket.send_by_size(str(self.screen.get_width()))
            else:
                self.stop_online_connection()
                return False
            if self.server_socket.recv_by_size() == "RESOLUTION HEIGHT":
                self.server_socket.send_by_size(str(self.screen.get_height()))
            else:
                self.stop_online_connection()
                return False
            if not self.server_socket.recv_by_size() == "OK END":
                self.stop_online_connection()
                return False
            self.__get_map_name()
            if character_side == Game.server_character:
                self.hero = self.__get_hero_from_server()
            # self.__get_inactive_timeout()
            return True
        except socket.error:
            self.stop_online_connection()
            Game._exit_msg("Could not connect to server.")

    def __get_map_name(self):
        """Part of the info_for_server method, initializes the map."""
        self.server_socket.send_by_size("MAP NAME")
        map_name = self.server_socket.recv_by_size()
        self._update_map(map_name)

    def __get_hero_from_server(self):
        """Gets the Character object to be used as hero from the server and returns it."""
        self.server_socket.send_by_size("CHARACTER")
        hero = pickle.loads(self.server_socket.recv_by_size())
        hero.image = Game.get_team_image(Game.ally_team)
        return hero

    # def __get_inactive_timeout(self):
    #     self.__sendd("INACTIVE TIMEOUT")
    #     self.__inactive_timeout = self.server_socket.recv_by_size()

    def _update_map(self, map_name):
        """Updates the map of the game from 'assets'."""
        self.__game_map = pygame.image.load("assets\\" + map_name).convert()
        self.__minimap = pygame.image.load("assets\\" + map_name).convert()

    def _endgame_message(self, msg, color=pygame.Color(255, 0, 0)):
        """Print msg to the pygame screen."""
        pygame.font.init()
        size = (self.screen.get_width() / len(msg)) * 2    # I found that this about fills the screen.
        text = pygame.font.SysFont(None, size, bold=True).render(msg, True, color)
        self.screen.blit(text, pygame.Rect(0, 0, 0, 0))
        pygame.display.flip()

    def handle_end_game(self, msg):
        """Ends the game in an organized way."""
        self.stop_online_connection()
        print(msg)
        self._endgame_message(msg)

    def stop_online_connection(self):
        """Stops the client from communicating with the server.
        Call this function when the game stops connection to the server for any reason."""
        try:
            self.server_socket.settimeout(self.timeout)
            self.server_socket.send_by_size("DISCONNECT")
        except socket.error:
            pass
        self.__recv = False
        self.__send = False

    @staticmethod
    def _exit_msg(msg):
        """Displays the message and waits for Enter press to exit."""
        pygame.quit()
        raw_input("%s. Press Enter to exit." % msg)

    def quit_func(self):
        """Function to call when quitting pygame"""
        self.stop_online_connection()
        debug_print("Exiting")
        pygame.display.quit()
        pygame.quit()
        self.__exit = True


def debug_print(*s):
    if DEBUG:
        print("".join([str(word) for word in s]))


def get_refresh_rate(device):
    """Returns the refresh rate of the monitor."""
    return getattr(win32api.EnumDisplaySettings(device.DeviceName, -1), "DisplayFrequency")
