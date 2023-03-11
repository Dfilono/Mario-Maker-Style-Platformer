import pygame as pg
from pygame.math import Vector2 as vector
from settings import *

class Generic(pg.sprite.Sprite):
    def __init__(self, pos, surf, group):
        super().__init__(group)

        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)

class Block(Generic):
    def __init__(self, pos, size, group):
        surf = pg.Surface(size)

        super().__init__(pos, surf, group)

class Animated(Generic):
    def __init__(self, assets, pos, group):
        self.animation_frames = assets
        self.frame_idx = 0

        super().__init__(pos, self.animation_frames[self.frame_idx], group)

    def animate(self, dt):
        self.frame_idx += ANIM_SPEED * dt
        self.frame_idx = 0 if self.frame_idx >= len(self.animation_frames) else self.frame_idx
        self.image = self.animation_frames[int(self.frame_idx)]

    def update(self, dt):
        self.animate(dt)

class Particle(Animated):
    def __init__(self, assets, pos, group):
        super().__init__(assets, pos, group)
        
        self.rect = self.image.get_rect(center = pos)

    def animate(self, dt):
        self.frame_idx += ANIM_SPEED * dt
        
        if self.frame_idx < len(self.animation_frames):
            self.image = self.animation_frames[int(self.frame_idx)]

        else:
            self.kill()

class Coin(Animated):
    def __init__(self, coin_type, assets, pos, group):
        super().__init__(assets, pos, group)
        
        self.rect = self.image.get_rect(center = pos)
        self.coin_type = coin_type

class Spikes(Generic):
    def __init__(self, surf, pos, group):
        super().__init__(pos, surf, group)

class Tooth(Generic):
    def __init__(self, assets, pos, group):
        self.animation_frames = assets
        self.frame_idx = 0
        self.orient = 'right'
        surf = self.animation_frames[f'run_{self.orient}'][self.frame_idx]

        super().__init__(pos, surf, group)

        self.rect.bottom = self.rect.top + TILE_SIZE

class Shell(Generic):
    def __init__(self, orient, assets, pos, group):
        self.orient = orient
        self.animation_frames = assets.copy()

        if orient == 'right':
            for key, value in self.animation_frames.items():
                self.animation_frames[key] = [pg.transform.flip(surf, True, False) for surf in value]

        self.frame_idx = 0
        self.status = 'idle'

        super().__init__(pos, self.animation_frames[self.status][self.frame_idx], group)

        self.rect.bottom = self.rect.top + TILE_SIZE

class Player(Generic):
    def __init__(self, pos, group, collision_sprites):
        super().__init__(pos, pg.Surface((80, 64)), group)
        
        self.image.fill('red')

        # movement
        self.direction = vector()
        self.pos = vector(self.rect.center)
        self.speed = 300
        self.gravity = 4
        self.on_floor = False

        # collision
        self.collision_sprites = collision_sprites
        self.hitbox = self.rect.inflate(-50, 0)

    def inputs(self):
        keys = pg.key.get_pressed()

        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.direction.x = 1

        elif keys[pg.K_LEFT] or keys[pg.K_a]:
            self.direction.x = -1

        else:
            self.direction.x = 0

        if keys[pg.K_SPACE] and self.on_floor:
            self.direction.y = -2

    def move(self, dt):
        # horizonal
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        # vertical
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def apply_gravity(self, dt):
        self.direction.y += self.gravity * dt
        self.rect.y += self.direction.y

    def check_floor(self):
        floor_rect = pg.Rect((self.hitbox.bottomleft), (self.hitbox.width, 2))
        floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.colliderect(floor_rect)]
        self.on_floor = True if floor_sprites else False

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.rect.left
                    
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.rect.right
                    
                    self.rect.centerx = self.hitbox.centerx
                    self.pos.x = self.hitbox.centerx
                else:
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.rect.bottom
                    
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.rect.top
                    
                    self.rect.centery = self.hitbox.centery
                    self.pos.y = self.hitbox.centery
                    self.direction.y = 0

    def update(self, dt):
        self.inputs()
        self.apply_gravity(dt)
        self.move(dt)
        self.check_floor()