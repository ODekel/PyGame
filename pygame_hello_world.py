import pygame
#from pygame.locals import *
from utilities import *
import win32api


def main():
    """The main loop for the game"""
    pygame.init()   # Set up pygame.
    surface = pygame.display.set_mode((720, 480), 0, 32)
    pygame.display.set_caption("Hello World!")
    wait_keyboard(pygame.K_SPACE)
    font = pygame.font.SysFont(None, 48)
    text = font.render("Hello World!", True, Colors.white, Colors.blue)
    text_rect = text.get_rect()
    text_rect.centerx = surface.get_rect().centerx
    text_rect.centery = surface.get_rect().centery
    surface.fill(Colors.white)
    pygame.draw.polygon(surface, Colors.green, ((146, 0), (291, 106), (236, 277), (56, 277), (0, 106)), 20)
    pygame.draw.line(surface, Colors.blue, (60, 60), (120, 60), 10)
    pygame.draw.line(surface, Colors.blue, (120, 60), (60, 120), 3)
    pygame.draw.line(surface, Colors.blue, (60, 120), (120, 120), 10)
    pygame.draw.circle(surface, Colors.yellow, (300, 50), 30)
    pygame.draw.ellipse(surface, Colors.red, (300, 50, 40, 80), 1)
    pygame.draw.rect(surface, Colors.teal, (text_rect.left - 20, text_rect.top - 20, text_rect.width + 40, text_rect.height + 40), 0)
    pixels = pygame.PixelArray(surface)
    for pixel in range(10):
        pixels[480][380 + pixel] = Colors.black
    del pixels
    surface.blit(text, text_rect)
    pygame.display.update()
    wait_keyboard(pygame.K_SPACE)
    text_rect = text_rect.move(100, -200)
    pygame.draw.rect(surface, Colors.teal, (text_rect.left - 20, text_rect.top - 20, text_rect.width + 40, text_rect.height + 40), 0)
    pygame.display.update()
    wait_keyboard(pygame.K_SPACE)
    minimap = pygame.image.load("dungeon_map.jpg").convert()
    fps = get_refresh_rate(win32api.EnumDisplayDevices())
    # pygame.time.Clock().tick(float(1000) / float(60))
    for offset in range(145):
        blit_image(surface, (0, 0), (0 + offset * 16, 0 + offset * 9,  720, 480), minimap)
        pygame.time.Clock().tick(fps)
        pygame.display.flip()
    # minimap = pygame.image.load("dungeon_map.jpg").convert()
    # crop_rect = (0, 0, 720, 480)
    # cropped_map = minimap.subsurface(crop_rect)
    # pygame.image.save(cropped_map, "cropped_map.jpg")
    # surface.blit(cropped_map, (0, 0))
    # pygame.display.update()
    wait_keyboard(pygame.K_SPACE)
    pygame.quit()


def get_refresh_rate(device):
    """Returns the refresh rate of the monitor."""
    return getattr(win32api.EnumDisplaySettings(device.DeviceName, -1), "DisplayFrequency")


def blit_image(surface, dest, crop, minimap):
    """Blit an image onto the surface"""
    # minimap = pygame.image.load(image).convert()
    #cropped_map = minimap.subsurface(crop)
    #pygame.image.save(cropped_map, "cropped_map.jpg")
    surface.blit(minimap.subsurface(crop), dest)


def wait_keyboard(*keys):
    """Waits for a space press (Removes events from queue and throws all other key presses!)"""
    # pygame.event.poll()
    event = pygame.event.wait()
    while not (event.type == pygame.KEYDOWN and event.key in keys):
        event = pygame.event.wait()


if __name__ == '__main__':
    main()
