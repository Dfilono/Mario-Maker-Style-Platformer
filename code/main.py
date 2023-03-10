import pygame as pg
from pygame.image import load
import sys
from settings import *
from editor import Editor
from support import *

class Main:
    def __init__(self):
        pg.init()
        self.display_surface = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pg.time.Clock()
        self.imports()

        self.editor = Editor(self.land_tiles)

        # cursor
        surf = load('../graphics/cursors/mouse.png').convert_alpha()
        cursor = pg.cursors.Cursor((0, 0), surf)
        pg.mouse.set_cursor(cursor)

    def imports(self):
        self.land_tiles = import_folder_dict('../graphics/terrain/land')

    def run(self):
        while True:
            dt = self.clock.tick() / 1000

            self.editor.run(dt)
            pg.display.update()

if __name__ == '__main__':
    main = Main()
    main.run()