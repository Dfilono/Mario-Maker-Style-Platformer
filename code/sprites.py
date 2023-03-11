import pygame as pg
from pygame.math import Vector2 as vector
from settings import *
from timer import Timer
from random import choice, randint

class Generic(pg.sprite.Sprite):
    def __init__(self, pos, surf, group, z = LEVEL_LAYERS['main']):
        super().__init__(group)

        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = z

class Block(Generic):
    def __init__(self, pos, size, group):
        surf = pg.Surface(size)

        super().__init__(pos, surf, group)

class Cloud(Generic):
    def __init__(self, pos, surf, group, left_limit):
        super().__init__(pos, surf, group, LEVEL_LAYERS['clouds'])

        self.left_limit = left_limit
        self.pos = vector(self.rect.topleft)
        self.speed = randint(20, 30)

    def update(self, dt):
        self.pos.x -= self.speed * dt
        self.rect.x = round(self.pos.x)

        if self.rect.x <= self.left_limit:
            self.kill()

class Animated(Generic):
    def __init__(self, assets, pos, group, z = LEVEL_LAYERS['main']):
        self.animation_frames = assets
        self.frame_idx = 0

        super().__init__(pos, self.animation_frames[self.frame_idx], group, z)

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
        self.mask = pg.mask.from_surface(self.image)

class Tooth(Generic):
    def __init__(self, assets, pos, group, collision_sprites):
        self.animation_frames = assets
        self.frame_idx = 0
        self.orient = 'right'
        surf = self.animation_frames[f'run_{self.orient}'][self.frame_idx]

        super().__init__(pos, surf, group)

        self.rect.bottom = self.rect.top + TILE_SIZE
        self.mask = pg.mask.from_surface(self.image)

        # movement
        self.direction = vector(choice((1, -1)), 0)
        self.orient = 'left' if self.direction.x < 0 else 'right'
        self.pos = vector(self.rect.topleft)
        self.speed = 120
        self.collision_sprites = collision_sprites

        # destroy tooth if not on floor
        if not [sprite for sprite in collision_sprites if sprite.rect.collidepoint(self.rect.midbottom + vector(0, 10))]:
            self.kill()

    def animate(self, dt):
        animation = self.animation_frames[f'run_{self.orient}']
        self.frame_idx += ANIM_SPEED * dt
        self.frame_idx = 0 if self.frame_idx >= len(animation) else self.frame_idx
        self.image = animation[int(self.frame_idx)]
        self.mask = pg.mask.from_surface(self.image)

    def move(self, dt):
        right_gap = self.rect.bottomright + vector(1, 1)
        right_block = self.rect.midright + vector(1, 0)
        left_gap = self.rect.bottomleft + vector(-1, 1)
        left_block = self.rect.midleft + vector(-1, 0)

        if self.direction.x > 0:
            floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(right_gap)]
            wall_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(right_block)]

            if wall_sprites or not floor_sprites:
                self.direction.x *= -1
                self.orient = 'left'
        
        if self.direction.x < 0:
            floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(left_gap)]
            wall_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(left_block)]

            if wall_sprites or not floor_sprites:
                self.direction.x *= -1
                self.orient = 'right'

        self.pos.x += self.direction.x * self.speed * dt
        self.rect.x = round(self.pos.x)

    def update(self, dt):
        self.animate(dt)
        self.move(dt)

class Shell(Generic):
    def __init__(self, orient, assets, pos, group, pearl_surf, damage_sprites):
        self.orient = orient
        self.animation_frames = assets.copy()

        if orient == 'right':
            for key, value in self.animation_frames.items():
                self.animation_frames[key] = [pg.transform.flip(surf, True, False) for surf in value]

        self.frame_idx = 0
        self.status = 'idle'

        super().__init__(pos, self.animation_frames[self.status][self.frame_idx], group)

        self.rect.bottom = self.rect.top + TILE_SIZE

        # pearl
        self.pearl_surf = pearl_surf
        self.has_shot = False
        self.cooldown = Timer(2000)
        self.damage_group = damage_sprites

    def animate(self, dt):
        animation = self.animation_frames[self.status]
        self.frame_idx += ANIM_SPEED * dt

        if self.frame_idx >= len(animation):
            self.frame_idx = 0

            if self.has_shot:
                self.cooldown.activate()
                self.has_shot = False
        
        self.image = animation[int(self.frame_idx)]

        if int(self.frame_idx) == 2 and self.status == 'attack' and not self.has_shot:
            pearl_direction = vector(-1, 0) if self.orient == 'left' else vector(1, 0)
            offset = (pearl_direction * 50) + vector(0, -10) if self.orient == 'left' else (pearl_direction * 20) + vector(0, -10)
            Pearl(self.rect.center + offset, pearl_direction, self.pearl_surf, [self.groups()[0], self.damage_group])
            self.has_shot = True

    def get_status(self):
        if vector(self.player.rect.center).distance_to((vector(self.rect.center))) < 500 and not self.cooldown.active:
            self.status = 'attack'
        else:
            self.status = 'idle'

    def update(self, dt):
        self.get_status()
        self.animate(dt)
        self.cooldown.update()

class Pearl(Generic):
    def __init__(self, pos, direction, surf, group):
        super().__init__(pos, surf, group)
        self.mask = pg.mask.from_surface(self.image)

        # movement
        self.pos = vector(self.rect.topleft)
        self.direction = direction
        self.speed = 150

        # self destruct
        self.timer = Timer(6000)
        self.timer.activate()

    def update(self, dt):
        self.pos.x += self.direction.x * self.speed * dt
        self.rect.x = round(self.pos.x)
        self.timer.update()

        if not self.timer.active:
            self.kill()

class Player(Generic):
    def __init__(self, pos, assets, group, collision_sprites):
        self.animation_frames = assets
        self.frame_idx = 0
        self.status = 'idle'
        self.orient = 'right'
        surf = self.animation_frames[f'{self.status}_{self.orient}'][self.frame_idx]

        super().__init__(pos, surf, group)

        self.mask = pg.mask.from_surface(self.image)

        # movement
        self.direction = vector()
        self.pos = vector(self.rect.center)
        self.speed = 300
        self.gravity = 4
        self.on_floor = False

        # collision
        self.collision_sprites = collision_sprites
        self.hitbox = self.rect.inflate(-50, 0)

        # inv frames
        self.invul_timer = Timer(200)

    def damage(self):
        if not self.invul_timer.active:
            self.invul_timer.activate()
            self.direction.y -= 1.5

    def get_status(self):
        if self.direction.y < 0:
            self.status = 'jump'
        elif self.direction.y > 0.2:
            self.status = 'fall'
        else:
            if self.direction.x != 0:
                self.status = 'run'
            else:
                self.status = 'idle'

    def animate(self, dt):
        current_state = self.animation_frames[f'{self.status}_{self.orient}']
        self.frame_idx += ANIM_SPEED * dt
        self.frame_idx = 0 if self.frame_idx >= len(current_state) else self.frame_idx
        self.image = current_state[int(self.frame_idx)]
        self.mask = pg.mask.from_surface(self.image)

        if self.invul_timer.active:
            surf = self.mask.to_surface()
            surf.set_colorkey('black')
            self.image = surf

    def inputs(self):
        keys = pg.key.get_pressed()

        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.direction.x = 1
            self.orient = 'right'

        elif keys[pg.K_LEFT] or keys[pg.K_a]:
            self.direction.x = -1
            self.orient = 'left'

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
        self.invul_timer.update()

        self.get_status()
        self.animate(dt)