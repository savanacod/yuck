import os
import random
import math
import pygame
import sys
from os import listdir
from os.path import isfile, join
from os.path import join, dirname
pygame.init()

pygame.display.set_caption("Platformer")


WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface ((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            scaled_frame = pygame.transform.scale(surface, (64, 64))
            sprites.append(scaled_frame)

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "block1.jpg")
    image = pygame.image.load(path).convert()
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, 64, 64) 
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale(surface, (size, size))

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("Character", "guy", 32, 32, True)
    ANIMATION_DELAY = 2.5

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.sprite = self.SPRITES["idle_left"][0]

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
       

        
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
             self.direction = "left"
             self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
        self.fall_count += 1 

        self.animation_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.y_vel != 0:
            if self.jump_count == 1:
                sprite_sheet ="jump"
            elif self.jump_count == 2:
                sprite_sheet = "jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        if self.x_vel > 0:
            self.direction = "right"
            sprite_sheet = "walk"
        elif self.x_vel < 0:
            self.direction = "left"
            sprite_sheet = "walk"
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // int(self.ANIMATION_DELAY)) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None): 
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image)
        

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

        collided_objects.append(obj)
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(PLAYER_VEL)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(PLAYER_VEL)

    handle_vertical_collision(player, objects, player.y_vel)

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("skyy.png")

    block_size = 96

    player = Player(100, (HEIGHT - 64 - 32), 32, 32)
    blocks = []

    level_map = [
       "." * 5 + "." * 35 + "X" * 3 + "." * 62,
       "." * 5 + "." * 28 + "X" * 2 + "." * 70,
       "." * 5 + "." * 21 + "X" * 4 + "." * 75,
       "." * 5 + "." * 14 + "X" * 3 + "." * 83,
       "." * 5 + "." * 7 + "X" * 4 + "." * 89,
       "." * 105,
       "X" * 105
    ]

    for row_index, row in enumerate(level_map):
        for col_index, char in enumerate(row):
            if char =="X":
                x_pos = col_index * 64
                y_pos = (HEIGHT - (len(level_map) * 64)) + (row_index * 64)

                blocks.append(Block(x_pos, y_pos, 64))

    objects = [*blocks]
    
    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_UP or event.key == pygame.K_SPACE or event.key == pygame.K_w) and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
            (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit() 
    sys.exit()

if __name__ == "__main__":
    main(window) 
