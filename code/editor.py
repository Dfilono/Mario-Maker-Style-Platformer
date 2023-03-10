import pygame as pg
from pygame.math import Vector2 as vector
import sys
from settings import *
from menu import Menu

class Editor:
    def __init__(self, land_tiles):
        # main setup
        self.display_surface = pg.display.get_surface()

        # support
        self.canvas_data = {}

        # imports
        self.land_tiles = land_tiles

        # navigation
        self.origin = vector()
        self.pan_active = False
        self.pan_offset = vector()

        # support lines
        self.support_line_surf = pg.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.support_line_surf.set_colorkey('green')
        self.support_line_surf.set_alpha(30)

        # selection
        self.selection_idx = 2
        self.last_cell = None

        # menu
        self.menu = Menu()

    # support
    def get_current_cell(self):
        distance_origin = vector(pg.mouse.get_pos()) - self.origin

        if distance_origin.x > 0:
            col = int(distance_origin.x / TILE_SIZE)
        else:
            col = int(distance_origin.x / TILE_SIZE) - 1

        if distance_origin.y > 0:
            row = int(distance_origin.y / TILE_SIZE)
        else:
            row = int(distance_origin.y / TILE_SIZE) - 1

        return col, row

    def check_neighbors(self, cell_pos):
        # create cluster
        cluster_size = 3
        local_cluster = [
			(cell_pos[0] + col - int(cluster_size / 2), cell_pos[1] + row - int(cluster_size / 2)) 
			for col in range(cluster_size) 
			for row in range(cluster_size)]
        
        # check neigbors
        for cell in local_cluster:
             if cell in self.canvas_data:
                self.canvas_data[cell].terrain_neighbors = []

                for name, side in NEIGHBOR_DIRECTIONS.items():
                    neighbor_cell = (cell[0] + side[0],cell[1] + side[1])

                    if neighbor_cell in self.canvas_data:
                         if self.canvas_data[neighbor_cell].has_terrain:
                             self.canvas_data[cell].terrain_neighbors.append(name)


    # input
    def event_loop(self):
        # event loop
        # close the game
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            
            self.pan_input(event)
            self.selection_hotkeys(event)
            self.menu_click(event)
            self.canvas_add()

    def pan_input(self, event):
        # middle moust button pressed/released
        if event.type == pg.MOUSEBUTTONDOWN and pg.mouse.get_pressed()[1]:
            self.pan_active = True
            self.pan_offset = vector(pg.mouse.get_pos()) - self.origin

        if not pg.mouse.get_pressed()[1]:
            self.pan_active = False

        # mouse wheel
        if event.type == pg.MOUSEWHEEL:
            if pg.key.get_pressed()[pg.K_LCTRL]:
                self.origin.y -= event.y * 50
            else:
                self.origin.x -= event.y * 50

        # panning update
        if self.pan_active:
            self.origin = vector(pg.mouse.get_pos()) - self.pan_offset

    def selection_hotkeys(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RIGHT:
                self.selection_idx += 1
            if event.key == pg.K_LEFT:
                self.selection_idx -= 1
        
        self.selection_idx = max(2, min(self.selection_idx, 18))

    def menu_click(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(pg.mouse.get_pos()):
            self.selection_idx = int(self.menu.click(pg.mouse.get_pos(), pg.mouse.get_pressed()))

    def canvas_add(self):
         if pg.mouse.get_pressed()[0] and not self.menu.rect.collidepoint(pg.mouse.get_pos()):
            current_cell = self.get_current_cell()
            
            if current_cell != self.last_cell:
                
                if current_cell in self.canvas_data:
                    self.canvas_data[current_cell].add_id(self.selection_idx)
                else:
                    self.canvas_data[current_cell] = CanvasTile(self.selection_idx)
		
                self.check_neighbors(current_cell)
                self.last_cell = current_cell
            

    # drawing
    def draw_grid_lines(self):
        cols = WINDOW_WIDTH // TILE_SIZE
        rows = WINDOW_HEIGHT // TILE_SIZE

        offset_vec = vector(x = self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE, y = self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE)

        self.support_line_surf.fill('green')

        for col in range(cols + 1):
            x = offset_vec.x + (col * TILE_SIZE)
            pg.draw.line(self.support_line_surf, LINE_COLOR, (x, 0), (x, WINDOW_HEIGHT))

        for row in range(rows + 1):
            y = offset_vec.y + (row * TILE_SIZE)
            pg.draw.line(self.support_line_surf, LINE_COLOR, (0, y), (WINDOW_WIDTH, y))
            
        self.display_surface.blit(self.support_line_surf, (0, 0))

    def draw_level(self):
        for cell_pos, tile in self.canvas_data.items():
            pos = self.origin + vector(cell_pos) * TILE_SIZE

            if tile.has_terrain:
                terrain_string = ''.join(tile.terrain_neighbors)
                terrain_style = terrain_string if terrain_string in self.land_tiles else 'X'
                self.display_surface.blit(self.land_tiles[terrain_style], pos)

            if tile.has_water:
                test_surf = pg.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill('blue')
                self.display_surface.blit(test_surf, pos)

            if tile.coin:
                test_surf = pg.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill('yellow')
                self.display_surface.blit(test_surf, pos)

            if tile.enemy:
                test_surf = pg.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill('red')
                self.display_surface.blit(test_surf, pos)

    # update
    def run(self, dt):
        self.event_loop()

        # drawing
        self.display_surface.fill('gray')
        self.draw_level()
        self.draw_grid_lines()
        self.menu.display(self.selection_idx)

class CanvasTile:
    def __init__(self, tile_id):
        # terrain
        self.has_terrain = False
        self.terrain_neighbors = []

        # water
        self.has_water = False
        self.water_top = False

        # coin
        self.coin = None 

        # enemy
        self.enemy = None

        # objs
        self.objs = []

        self.add_id(tile_id)

    def add_id(self, tile_id):
        options = {key : value['style'] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case 'terrain' : self.has_terrain = True
            case 'water' : self.has_water = True
            case 'coin' : self.coin = tile_id
            case 'enemy' : self.enemy = tile_id
