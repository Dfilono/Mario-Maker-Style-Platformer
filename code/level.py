import pygame as pg
from pygame.math import Vector2 as vector
import sys
from settings import *
from support import *
from sprites import Generic, Block, Animated, Particle, Coin, Player, Spikes, Tooth, Shell, Cloud
from random import choice, randint

class Level:
    def __init__(self, grid, switch, asset_dict, audio):
        self.display_surface = pg.display.get_surface()
        self.switch = switch

        # groups
        self.all_sprites = CameraGroup()
        self.coin_sprites = pg.sprite.Group()
        self.damage_sprites = pg.sprite.Group()
        self.collision_sprites = pg.sprite.Group()
        self.shell_sprites = pg.sprite.Group()

        self.build_level(grid, asset_dict, audio['jump'])

        # level limits
        self.level_limits = {
            'left' : -WINDOW_WIDTH,
            'right' : sorted(list(grid['terrain'].keys()), key = lambda pos: pos[0])[-1][0] + 500
        }

        # support
        self.particle_surf = asset_dict['particle']
        self.cloud_surf = asset_dict['clouds']
        self.cloud_timer = pg.USEREVENT + 2
        pg.time.set_timer(self.cloud_timer, 2000)
        self.start_clouds()

        # sounds
        self.bg_music = audio['music']
        self.bg_music.set_volume(0.3)
        self.bg_music.play(loops = -1)

        self.coin_sound = audio['coin']
        self.coin_sound.set_volume(0.3)

        self.hit_sound = audio['hit']
        self.hit_sound.set_volume(0.3)

    def build_level(self, grid, asset_dict, jump_sound):
        for layer_name, layer in grid.items():
            for pos, data in layer.items():
                if layer_name == 'terrain':
                    Generic(pos, asset_dict['land'][data], [self.all_sprites, self.collision_sprites])

                if layer_name == 'water' :
                    if data == 'top' :
                       Animated(asset_dict['water top'], pos, self.all_sprites, LEVEL_LAYERS['water'])
                       pass
                    else:
                        Generic(pos, asset_dict['water bottom'], self.all_sprites, LEVEL_LAYERS['water'])

                match data:
                    case 0 : self.player = Player(pos, asset_dict['player'], self.all_sprites, self.collision_sprites, jump_sound)

                    case 1:
                        self.horizon_y = pos[1]
                        self.all_sprites.horizon_y = pos[1]

                    case 4 : Coin('gold', asset_dict['gold'], pos, [self.all_sprites, self.coin_sprites]) 
                    case 5 : Coin('silver', asset_dict['silver'], pos, [self.all_sprites, self.coin_sprites])
                    case 6 : Coin('diamond', asset_dict['diamond'], pos, [self.all_sprites, self.coin_sprites])

                    case 7 : Spikes(asset_dict['spikes'], pos, [self.all_sprites, self.damage_sprites]) 
                    case 8 : 
                        Tooth(asset_dict['tooth'], pos, [self.all_sprites, self.damage_sprites], self.collision_sprites)
                    case 9 : 
                        Shell('left', asset_dict['shell'], pos, [self.all_sprites, self.collision_sprites, self.shell_sprites], asset_dict['pearl'], self.damage_sprites)
                    case 10 : 
                        Shell('right', asset_dict['shell'], pos, [self.all_sprites, self.collision_sprites, self.shell_sprites], asset_dict['pearl'], self.damage_sprites)

                    case 11 : 
                        Animated(asset_dict['palms']['small_fg'], pos, self.all_sprites)
                        Block(pos, (76, 50), self.collision_sprites)
                    case 12 : 
                        Animated(asset_dict['palms']['large_fg'], pos, self.all_sprites)
                        Block(pos, (76, 50), self.collision_sprites)
                    case 13 : 
                        Animated(asset_dict['palms']['left_fg'], pos, self.all_sprites)
                        Block(pos, (76, 50), self.collision_sprites)
                    case 14 : 
                        Animated(asset_dict['palms']['right_fg'], pos, self.all_sprites)
                        Block(pos + vector(50, 0), (76, 50), self.collision_sprites)

                    case 15 : Animated(asset_dict['palms']['small_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
                    case 16 : Animated(asset_dict['palms']['large_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
                    case 17 : Animated(asset_dict['palms']['left_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
                    case 18 : Animated(asset_dict['palms']['right_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])

        for sprite in self.shell_sprites:
            sprite.player = self.player

    def get_coins(self):
        collided_coins = pg.sprite.spritecollide(self.player, self.coin_sprites, True)

        for sprite in collided_coins:
            self.coin_sound.play()
            Particle(self.particle_surf, sprite.rect.center, self.all_sprites)

    def get_damage(self):
        collision_sprites = pg.sprite.spritecollide(self.player, self.damage_sprites, False, pg.sprite.collide_mask)

        if collision_sprites:
            self.hit_sound.play()
            self.player.damage()

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.switch()
                self.bg_music.stop()

            if event.type == self.cloud_timer:
                surf = choice(self.cloud_surf)
                surf = pg.transform.scale2x(surf) if randint(0, 5) > 3 else surf
                x = self.level_limits['right'] + randint(100, 300)
                y = self.horizon_y - randint(-50, 600)
                Cloud((x, y), surf, self.all_sprites, self.level_limits['left'])
            
    def start_clouds(self):
        for cloud in range(20):
            surf = choice(self.cloud_surf)
            surf = pg.transform.scale2x(surf) if randint(0, 5) > 3 else surf
            x = randint(self.level_limits['left'], self.level_limits['right'])
            y = self.horizon_y - randint(-50, 600)
            Cloud((x, y), surf, self.all_sprites, self.level_limits['left'])

    def run(self, dt):
        #update
        self.event_loop()
        self.display_surface.fill(SKY_COLOR)
        self.get_coins()
        self.get_damage()

        #drawing
        self.all_sprites.update(dt)
        self.all_sprites.custom_draw(self.player)

class CameraGroup(pg.sprite.Group):
    def __init__(self):
        super().__init__()

        self.display_surface = pg.display.get_surface()
        self.offset = vector()

    def draw_horizon(self):
        horizon_pos = self.horizon_y - self.offset.y

        if horizon_pos < WINDOW_HEIGHT:
            rect = pg.Rect(0, horizon_pos, WINDOW_WIDTH, WINDOW_HEIGHT - horizon_pos)
            pg.draw.rect(self.display_surface, SEA_COLOR, rect)

            horizon_rect1 = pg.Rect(0, horizon_pos - 10, WINDOW_WIDTH, 10)
            horizon_rect2 = pg.Rect(0, horizon_pos - 16, WINDOW_WIDTH, 4)
            horizon_rect3 = pg.Rect(0, horizon_pos - 20, WINDOW_WIDTH, 2)
            pg.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
            pg.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
            pg.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)
            pg.draw.line(self.display_surface, HORIZON_COLOR, (0, horizon_pos), (WINDOW_WIDTH, horizon_pos), 3)

        if horizon_pos < 0:
            self.display_surface.fill(SEA_COLOR)

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - (WINDOW_WIDTH / 2)
        self.offset.y = player.rect.centery - (WINDOW_HEIGHT / 2)

        for sprite in self:
            if sprite.z == LEVEL_LAYERS['clouds']:
                offset_rect = sprite.rect.copy()
                offset_rect.center -= self.offset
                self.display_surface.blit(sprite.image, offset_rect)

        self.draw_horizon()

        for sprite in self:
            for layer in LEVEL_LAYERS.values():
                if sprite.z == layer and sprite.z != LEVEL_LAYERS['clouds']:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)