import pygame as pg
from pygame.math import Vector2 as vector
from pygame.image import load
import sys
from settings import *
from support import *
from menu import Menu
from timer import Timer
from random import choice, randint

class Editor:
    def __init__(self, land_tiles, switch):
        # main setup
        self.display_surface = pg.display.get_surface()
        self.switch = switch

        # support
        self.canvas_data = {}

        # imports
        self.land_tiles = land_tiles
        self.import_file()

        # clouds
        self.current_clouds = []
        self.cloud_surf = import_folder('../graphics/clouds')
        self.cloud_timer = pg.USEREVENT + 1
        pg.time.set_timer(self.cloud_timer, 2000)
        self.start_clouds()

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

        # objs
        self.canvas_objs = pg.sprite.Group()
        self.fg = pg.sprite.Group()
        self.bg = pg.sprite.Group()
        self.obj_drag_active = False
        self.obj_timer = Timer(400)
        
        # player
        CanvasObj((200, WINDOW_HEIGHT / 2), self.animations[0]['frames'], 0, self.origin, [self.canvas_objs, self.fg])

        # sky
        self.sky_handle = CanvasObj((WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), [self.sky_handle_surf], 1, self.origin, [self.canvas_objs, self.bg])

        # music
        self.editor_music = pg.mixer.Sound('../audio/Explorer.ogg')
        self.editor_music.set_volume(0.4)
        self.editor_music.play(loops = -1)

    # support
    def get_current_cell(self, obj = None):
        distance_origin = vector(pg.mouse.get_pos()) - self.origin if not obj else vector(obj.distance_origin) - self.origin

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
                self.canvas_data[cell].water_top = False

                for name, side in NEIGHBOR_DIRECTIONS.items():
                    neighbor_cell = (cell[0] + side[0],cell[1] + side[1])
                    

                    if neighbor_cell in self.canvas_data:
                        # water top neighbor
                        if self.canvas_data[neighbor_cell].has_water and self.canvas_data[cell].has_water and name == 'A':
                            self.canvas_data[cell].water_top = True

                    # terrain neighbors
                        if self.canvas_data[neighbor_cell].has_terrain:
                            self.canvas_data[cell].terrain_neighbors.append(name)

    def import_file(self):
        self.water_bot = load('../graphics/terrain/water/water_bottom.png').convert_alpha()
        self.sky_handle_surf = load('../graphics/cursors/handle.png').convert_alpha()

        # animations
        self.animations = {}

        for key, value in EDITOR_DATA.items():
            if value['graphics']:
                graphics = import_folder(value['graphics'])
                self.animations[key] = {
                    'frame index' : 0,
                    'frames' : graphics,
                    'length' : len(graphics)
                }

        # preview
        self.preview_surf = {key : load(value['preview']) for key, value in EDITOR_DATA.items() if value['preview']}

    def animation_update(self, dt):
        for value in self.animations.values():
            value['frame index'] += ANIM_SPEED * dt

            if value['frame index'] >= value['length']:
                value['frame index'] = 0

    def mouse_on_obj(self):
        for sprite in self.canvas_objs:
            if sprite.rect.collidepoint(pg.mouse.get_pos()):
                return sprite

    def create_grid(self):
        # add objs to tiles
        for tile in self.canvas_data.values():
            tile.objs = []

        for obj in self.canvas_objs:
            current_cell = self.get_current_cell(obj)
            offset = vector(obj.distance_origin) - (vector(current_cell) * TILE_SIZE)

            if current_cell in self.canvas_data:
                self.canvas_data[current_cell].add_id(obj.tile_id, offset)

            else:
                self.canvas_data[current_cell] = CanvasTile(obj.tile_id, offset)

        # create grid
        # grid offset
        left = sorted(self.canvas_data.keys(), key = lambda tile: tile[0])[0][0]
        top = sorted(self.canvas_data.keys(), key = lambda tile: tile[1])[0][1]

        # empty grid
        layers = {
            'water' : {},
            'bg palms' : {},
            'terrain' : {},
            'enemies' : {},
            'coin' : {},
            'fg objs' : {},
        }

        # fill grid
        for tile_pos, tile in self.canvas_data.items():
            row_adj = tile_pos[1] - top
            col_adj = tile_pos[0] - left
            x = col_adj * TILE_SIZE
            y = row_adj * TILE_SIZE

            if tile.has_water:
                layers['water'][(x, y)] = tile.get_water()

            if tile.has_terrain:
                layers['terrain'][(x, y)] = tile.get_terrain() if tile.get_terrain() in self.land_tiles else 'X'

            if tile.coin:
                layers['coin'][(x + TILE_SIZE // 2, y+ TILE_SIZE // 2)] = tile.coin

            if tile.enemy:
                layers['enemies'][(x, y)] = tile.enemy

            if tile.objs:
                for obj, offset in tile.objs:
                    if obj in [key for key, value in EDITOR_DATA.items() if value['style'] == 'palm_bg']:
                        layers['bg palms'][(int(x + offset.x), int(y + offset.y))] = obj

                    else:
                        layers['fg objs'][(int(x + offset.x), int(y + offset.y))] = obj

        return layers

    # input
    def event_loop(self):
        # event loop
        # close the game
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                self.switch(self.create_grid())
                self.editor_music.stop()
            
            self.pan_input(event)
            self.selection_hotkeys(event)
            self.menu_click(event)
            self.obj_drag(event)
            self.canvas_add()
            self.canvas_remove()

            self.create_clouds(event)

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

            for sprite in self.canvas_objs:
                sprite.pan_pos(self.origin)

        # panning update
        if self.pan_active:
            self.origin = vector(pg.mouse.get_pos()) - self.pan_offset

            for sprite in self.canvas_objs:
                sprite.pan_pos(self.origin)

    def selection_hotkeys(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RIGHT:
                self.selection_idx += 1
            if event.key == pg.K_LEFT:
                self.selection_idx -= 1
        
        self.selection_idx = max(2, min(self.selection_idx, 18))

    def menu_click(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(pg.mouse.get_pos()):
            new_idx = self.menu.click(pg.mouse.get_pos(), pg.mouse.get_pressed())
            self.selection_idx = new_idx if new_idx else self.selection_idx

    def canvas_add(self):
         if pg.mouse.get_pressed()[0] and not self.menu.rect.collidepoint(pg.mouse.get_pos()) and not self.obj_drag_active:
            current_cell = self.get_current_cell()

            if EDITOR_DATA[self.selection_idx]['type'] == 'tile':
            
                if current_cell != self.last_cell:
                    
                    if current_cell in self.canvas_data:
                        self.canvas_data[current_cell].add_id(self.selection_idx)
                    else:
                        self.canvas_data[current_cell] = CanvasTile(self.selection_idx)
            
                    self.check_neighbors(current_cell)
                    self.last_cell = current_cell
            
            else:
                if not self.obj_timer.active:
                    groups = [self.canvas_objs, self.bg] if EDITOR_DATA[self.selection_idx]['style'] == 'palm_bg' else [self.canvas_objs, self.fg]
                    CanvasObj(pg.mouse.get_pos(), self.animations[self.selection_idx]['frames'], self.selection_idx, self.origin, groups)
                self.obj_timer.activate()

    def canvas_remove(self):
        if pg.mouse.get_pressed()[2] and not self.menu.rect.collidepoint(pg.mouse.get_pos()):

            # delete obj
            selected_obj = self.mouse_on_obj()

            if selected_obj:
                if EDITOR_DATA[selected_obj.tile_id]['style'] not in ('player', 'sky'):
                    selected_obj.kill()

            # delete tiles
            if self.canvas_data:
                current_cell = self.get_current_cell()

                if current_cell in self.canvas_data:
                    self.canvas_data[current_cell].remove_id(self.selection_idx)

                    if self.canvas_data[current_cell].is_empty:
                        del self.canvas_data[current_cell]

                    self.check_neighbors(current_cell)

    def obj_drag(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and pg.mouse.get_pressed()[0]:
            for sprite in self.canvas_objs:
                if sprite.rect.collidepoint(event.pos):
                    sprite.start_drag()
                    self.obj_drag_active = True

        if event.type == pg.MOUSEBUTTONUP and self.obj_drag_active:
            for sprite in self.canvas_objs:
                if sprite.selected:
                    sprite.drag_end(self.origin)
                    self.obj_drag_active = False

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
        self.bg.draw(self.display_surface)

        for cell_pos, tile in self.canvas_data.items():
            pos = self.origin + vector(cell_pos) * TILE_SIZE

            if tile.has_terrain:
                terrain_string = ''.join(tile.terrain_neighbors)
                terrain_style = terrain_string if terrain_string in self.land_tiles else 'X'
                self.display_surface.blit(self.land_tiles[terrain_style], pos)

            if tile.has_water:
                if tile.water_top:
                    self.display_surface.blit(self.water_bot, pos)
                else:
                    frames = self.animations[3]['frames']
                    idx = int(self.animations[3]['frame index'])
                    surf = frames[idx]
                    self.display_surface.blit(surf, pos)

            if tile.coin:
                frames = self.animations[tile.coin]['frames']
                idx = int(self.animations[tile.coin]['frame index'])
                surf = frames[idx]
                rect = surf.get_rect(center = (pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))
                self.display_surface.blit(surf, rect)

            if tile.enemy:
                frames = self.animations[tile.enemy]['frames']
                idx = int(self.animations[tile.enemy]['frame index'])
                surf = frames[idx]
                rect = surf.get_rect(midbottom = (pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE))
                self.display_surface.blit(surf, rect)

        self.fg.draw(self.display_surface)

    def preview(self):
        selected_obj = self.mouse_on_obj()
        if not self.menu.rect.collidepoint(pg.mouse.get_pos()):
            if selected_obj:
                # draws lines around objs when hovered over
                rect = selected_obj.rect.inflate(10, 10)
                color = 'black'
                w = 3
                size = 15

                pg.draw.lines(self.display_surface, color, False, ((rect.left, rect.top + size), rect.topleft, (rect.left + size, rect.top)), w) # top left
                pg.draw.lines(self.display_surface, color, False, ((rect.right - size, rect.top), rect.topright, (rect.right, rect.top + size)), w) # top right
                pg.draw.lines(self.display_surface, color, False, ((rect.right - size, rect.bottom), rect.bottomright, (rect.right, rect.bottom - size)), w) # bot right
                pg.draw.lines(self.display_surface, color, False, ((rect.left, rect.bottom - size), rect.bottomleft, (rect.left + size, rect.bottom)), w) # bot left

            else:
                # preview of obj/tile to be placed
                type_dict = {key : value['type'] for key, value in EDITOR_DATA.items()}
                surf = self.preview_surf[self.selection_idx].copy()
                surf.set_alpha(200)

                if type_dict[self.selection_idx] == 'tile':
                    current_cell = self.get_current_cell()
                    rect = surf.get_rect(topleft = self.origin + vector(current_cell) * TILE_SIZE)
                
                else:
                    rect = surf.get_rect(center = pg.mouse.get_pos())

                self.display_surface.blit(surf, rect)

    def display_sky(self, dt):
        self.display_surface.fill(SKY_COLOR)
        
        y = self.sky_handle.rect.centery

        # horizon
        if y > 0:
            horizon_rect1 = pg.Rect(0, y - 10, WINDOW_WIDTH, 10)
            horizon_rect2 = pg.Rect(0, y - 16, WINDOW_WIDTH, 4)
            horizon_rect3 = pg.Rect(0, y - 20, WINDOW_WIDTH, 2)
            pg.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
            pg.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
            pg.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)

            self.display_clouds(dt, y)

        # sea
        if 0 < y < WINDOW_HEIGHT:
            sea_rect = pg.Rect(0, y, WINDOW_WIDTH, WINDOW_HEIGHT)
            pg.draw.rect(self.display_surface, SEA_COLOR, sea_rect)

        if y <= 0:
            self.display_surface.fill(SEA_COLOR)

        pg.draw.line(self.display_surface, HORIZON_COLOR, (0, y), (WINDOW_WIDTH, y), 3)
        

    def display_clouds(self, dt, hy):
        for cloud in self.current_clouds:
            cloud['pos'][0] -= cloud['speed'] * dt
            x = cloud['pos'][0]
            y = hy - cloud['pos'][1]
            self.display_surface.blit(cloud['surf'], (x, y))

    def create_clouds(self, event):
        if event.type == self.cloud_timer:
            surf = choice(self.cloud_surf)

            if randint(0, 4) < 2:
                surf = pg.transform.scale2x(surf)
            
            pos = [WINDOW_WIDTH + randint(50, 100), randint(0, WINDOW_HEIGHT)]
            speed = randint(20, 50)

            self.current_clouds.append({'surf' : surf, 'pos' : pos, 'speed' : speed})

            # remove clouds
            self.current_clouds = [cloud for cloud in self.current_clouds if cloud['pos'][0] > -400]

    def start_clouds(self):
        for i in range(20):
            surf = choice(self.cloud_surf)

            if randint(0, 4) < 2:
                surf = pg.transform.scale2x(surf)

            pos = [randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)]
            speed = randint(20, 50)

            self.current_clouds.append({'surf' : surf, 'pos' : pos, 'speed' : speed})

    # update
    def run(self, dt):
        self.event_loop()

        # updating
        self.animation_update(dt)
        self.canvas_objs.update(dt)
        self.obj_timer.update()

        # drawing
        self.display_surface.fill('gray')
        self.display_sky(dt)
        self.draw_level()
        self.draw_grid_lines()
        self.preview()
        self.menu.display(self.selection_idx)

class CanvasTile:
    def __init__(self, tile_id, offset = vector()):
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

        self.add_id(tile_id, offset = offset)
        self.is_empty = False

    def add_id(self, tile_id, offset = vector()):
        options = {key : value['style'] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case 'terrain' : self.has_terrain = True
            case 'water' : self.has_water = True
            case 'coin' : self.coin = tile_id
            case 'enemy' : self.enemy = tile_id
            case _ :
                if (tile_id, offset) not in self.objs: 
                    self.objs.append((tile_id, offset)) 

    def remove_id(self, tile_id):
        options = {key : value['style'] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case 'terrain' : self.has_terrain = False
            case 'water' : self.has_water = False
            case 'coin' : self.coin = None
            case 'enemy' : self.enemy = None
        
        self.check_content()

    def check_content(self):
        if not self.has_terrain and not self.has_water and not self.coin and not self.enemy:
            self.is_empty = True

    def get_water(self):
        return 'bottom' if self.water_top else 'top'
    
    def get_terrain(self):
        return ''.join(self.terrain_neighbors)

class CanvasObj(pg.sprite.Sprite):
    def __init__(self, pos, frames, tile_id, origin, group):
        super().__init__(group)

        self.tile_id = tile_id

        # animation
        self.frames = frames
        self.frame_idx = 0
        self.image = self.frames[self.frame_idx]
        self.rect = self.image.get_rect(center = pos)

        # movement
        self.distance_origin = vector(self.rect.topleft) - origin
        self.selected = False
        self.mouse_offset = vector()

    def start_drag(self):
        self.selected = True
        self.mouse_offset = vector(pg.mouse.get_pos()) - vector(self.rect.topleft)

    def drag(self):
        if self.selected:
            self.rect.topleft = pg.mouse.get_pos() - self.mouse_offset

    def drag_end(self, origin):
        self.selected = False
        self.distance_origin = vector(self.rect.topleft) - origin

    def animate(self, dt):
        self.frame_idx += ANIM_SPEED * dt
        self.frame_idx = 0 if self.frame_idx >= len(self.frames) else self.frame_idx
        self.image = self.frames[int(self.frame_idx)]
        self.rect = self.image.get_rect(midbottom = self.rect.midbottom)


    def pan_pos(self, origin):
        self.rect.topleft = origin + self.distance_origin

    def update(self, dt):
        self.animate(dt)
        self.drag()