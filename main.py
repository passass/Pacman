import sys
import pygame
from csv import reader
from time import time
from random import choice

pygame.font.init()
font = pygame.font.Font(pygame.font.match_font('consolas'), 30)

pygame.display.set_caption('Pacman')

width, height = 928, 372
screen = pygame.display.set_mode((width, height))
sprite = pygame.sprite.Sprite()
all_sprite = pygame.sprite.Group()
clock = pygame.time.Clock()
running = True


def terminate():
    pygame.quit()
    sys.exit()


def start_screen(text):
    intro_text = [text]

    # fon = pygame.transform.scale(pygame.image.load('data/fon.jpg'), (width, height))`
    # screen.blit(fon, (0, 0))
    text_coord = 150
    for line in intro_text:
        string_rendered = font.render(line, True, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        pygame.display.flip()
        clock.tick(50)


start_screen('Нажмите любую кнопку чтобы продолжить')

levels_settings = {
    # картинка карты, картинка хитбоксов карты, координаты спавна пакмана,
    # координаты спавна призраков, координаты кнопки старт, менять ли размер окна (пустой если не надо),
    # координаты зоны из которой выходят призраки
    1: (pygame.transform.scale(pygame.image.load("data/level_1_background.png"), (width, height - 100)),
        pygame.transform.scale(pygame.image.load("data/level_1_walls_hitbox.png"), (width, height - 100)),
        (570, 272), [(528, 147, 'red', 0, 1), (595, 147, 'pink', 0, 20), (560, 147, 'blue', 15, 20)],
        (525, 200), (), (520, 130, 623, 192)),
}


class Location(pygame.sprite.Sprite):
    def __init__(self, picture, *group):
        super().__init__(*group)
        self.image = picture
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 0
        self.rect.y = 40

    def update(self):
        pass


class Circle_of_point(pygame.sprite.Sprite):
    def __init__(self, x, y, *group):
        super().__init__(*group)
        self.image = sprites['circle_of_point']
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = x - 3
        self.rect.y = y - 3


def reset_game():
    global CURRENT_LEVEL, attempts, points, TOTAL_POINTS
    TOTAL_POINTS = 0
    attempts = 2
    CURRENT_LEVEL = 1
    points = pygame.sprite.Group()
    load_points_locations()
    load_level()


def load_points_locations():
    with open(f'data/level_{CURRENT_LEVEL}_points_places.csv', 'r', newline='') as csvfile:
        global points
        csvfile = reader(csvfile, delimiter=';')
        for x, y in csvfile:
            points.add(Circle_of_point(int(x) * 2, int(y) * 2 + 40))


def load_level():
    global Location_obj, ghosts, all_sprites, Pacman_obj
    if levels_settings[CURRENT_LEVEL][5]:
        global width, height, screen
        width, height = levels_settings[CURRENT_LEVEL][5][0], levels_settings[CURRENT_LEVEL][5][1]
        screen = pygame.display.set_mode((width, height))
    all_sprites = pygame.sprite.Group()
    all_sprites.add(Location(levels_settings[CURRENT_LEVEL][0]))
    all_sprites.add(Location(levels_settings[CURRENT_LEVEL][1]))
    Location_obj = all_sprites.sprites()[-1]
    Location_obj.image.set_alpha(0)
    all_sprites.add(Pacman(*levels_settings[CURRENT_LEVEL][2]))
    Pacman_obj = all_sprites.sprites()[-1]
    ghosts = pygame.sprite.Group()
    for x in points:
        all_sprites.add(x)
    for stats in levels_settings[CURRENT_LEVEL][3]:
        all_sprites.add(Ghost(*stats))
        ghosts.add(all_sprites.sprites()[-1])
    time_to_hide_text = time() + 2
    string_rendered = font.render('START!', True, pygame.Color('yellow'))
    intro_rect = string_rendered.get_rect()
    intro_rect.x = levels_settings[CURRENT_LEVEL][4][0]
    intro_rect.top = levels_settings[CURRENT_LEVEL][4][1]
    while time() < time_to_hide_text:
        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        screen.blit(string_rendered, intro_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        clock.tick(50)


def add_points(count):
    global TOTAL_POINTS, points_tab
    TOTAL_POINTS += count
    points_tab = font.render(str(TOTAL_POINTS), True, pygame.Color('white'))


def WIN():
    global CURRENT_LEVEL
    CURRENT_LEVEL += 1
    pygame.display.flip()
    if CURRENT_LEVEL not in levels_settings:
        time_to_win = time() + 0.75
        while time() < time_to_win:
            pass
        screen.fill((0, 0, 0))
        pygame.display.flip()
        start_screen('Вы выиграли, но вы можете продолжить играть. Нажмите любую кнопку чтобы продолжить')
        reset_game()
    else:
        start_screen('Нажмите любую кнопку чтобы продолжить')
        load_points_locations()
        load_level()


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, color, release_time=10, rage_time=20, *group):
        super().__init__(*group)
        self.color = color
        self.image = sprites['ghost'][color][LEFT][0]
        self.animation_stage = 0
        self.animation_change_delay = time() + 0.2
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = x
        self.rect.y = y
        self.motion = choice([LEFT, RIGHT])
        self.motion_dont_move_to = []
        self.release_time = time() + release_time
        self.rage_time = self.release_time + rage_time
        self.last = []

    def sees_pacman(self):
        return False

    def possible_move_to_sides(self, sides=None, block_motion=True):
        last_rect = self.rect
        if sides is None:
            sides = [LEFT, RIGHT, DOWN, UP]
        for x in sides:
            self.rect = last_rect
            self.rect = self.rect.move(x[0] * 16, x[1] * 16)
            if not pygame.sprite.collide_mask(self, Location_obj):
                if x not in self.motion_dont_move_to:
                    if block_motion:
                        self.motion_dont_move_to.append(x)
                    yield x
            elif x in self.motion_dont_move_to:
                if block_motion:
                    self.motion_dont_move_to.remove(x)
        self.rect = last_rect

    def choose_side_to_move(self):
        global CURRENT_LEVEL
        sides = list(self.possible_move_to_sides([LEFT, RIGHT, DOWN, UP]))
        if self.motion in self.motion_dont_move_to:
            self.motion_dont_move_to.remove(self.motion)
        new_sides = []
        for x in sides:
            if abs(x[0]) != abs(self.motion[0]) or not list(self.possible_move_to_sides([self.motion], False)):
                new_sides.append(x)
        new_sides.append(self.motion)
        '''if time() >= self.rage_time:
            if len(new_sides) == 1:
                return new_sides[0]
            else:
                return self.rage_move(moves_made)
        else:'''
        if len(new_sides) == 1:
            return new_sides[0]
        x1, y1, x2, y2 = levels_settings[CURRENT_LEVEL][6]
        if x1 < self.rect.x < x2 and y1 < self.rect.y < y2:
            start_pos = self.rect
            moves_count = [0] * len(new_sides)
            for i in range(len(new_sides)):
                while x1 < self.rect.x < x2 and y1 < self.rect.y < y2 and moves_count[i] < 12:
                    moves_count[i] += 1
                    if pygame.sprite.collide_mask(self, Location_obj):
                        moves_count[i] = 12
                        break
                    elif isinstance(new_sides[i], tuple) and self.possible_move_to_sides(new_sides[i], False):
                        self.do_a_move(new_sides[i], False)
                self.rect = start_pos
            return new_sides[moves_count.index(min(moves_count))]
        else:
            if DOWN in new_sides and x1 < self.rect.x < x2 and y1 < self.rect.y + pacman_width[1] + 3 < y2:
                new_sides.remove(DOWN)
            if self.sees_pacman():  # если призрак видит пакмана, но эта функция не реализована, должна возвращать False если пакман находиться там, откуда пришёл призрак
                return
            else:
                return choice(new_sides)

    def do_a_move(self, side_to_move=None, take_into_collision=True):
        if self.rect.x < -25:
            self.rect.x = width - pacman_width[0]
        elif self.rect.x > width - 3:
            self.rect.x = 1
        self.last = self.rect.x, self.rect.y
        if side_to_move is None:
            side_to_move = self.choose_side_to_move()
        self.rect = self.rect.move(*side_to_move)
        self.motion = side_to_move
        if pygame.sprite.collide_mask(self, Location_obj) and take_into_collision:
            self.motion_dont_move_to = []
            self.motion = self.choose_side_to_move()
            self.rect.x, self.rect.y = self.last

    def update(self):
        self.image = sprites['ghost'][self.color][self.motion][self.animation_stage]
        if time() >= self.release_time:
            self.do_a_move()
        if time() >= self.animation_change_delay:
            self.animation_change_delay = time() + 0.2
            self.animation_stage = abs(self.animation_stage - 1)


class Pacman(pygame.sprite.Sprite):
    def __init__(self, x, y, *group):
        super().__init__(*group)
        self.image = sprites['pacman']['IDLE']
        self.animation_stage = 0
        self.animation_change_delay = time() + 0.2
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = x
        self.rect.y = y
        self.last = None
        self.last_motion = LEFT

    def possible_to_move(self, side):
        self.rect = self.rect.move(side[0] * 16, side[1] * 16)
        return pygame.sprite.collide_mask(self, Location_obj)

    def can_move_to(self, side):
        last_positions = self.rect.x, self.rect.y
        can = self.possible_to_move(side)
        self.rect.x, self.rect.y = last_positions
        x1, y1, x2, y2 = levels_settings[CURRENT_LEVEL][6]
        return not can and (side != DOWN or not (x1 < self.rect.x < x2 and y1 < self.rect.y + pacman_width[1] + 3 < y2))

    def death(self):
        global attempts, ghosts
        time_to_load_new_level = time() + 1
        while time() < time_to_load_new_level:
            clock.tick(30)
        time_to_load_new_level = time() + 2.5
        time_to_next_animation = time()
        by_account = -1
        ghosts = pygame.sprite.Group()
        while time() < time_to_load_new_level:
            screen.fill((0, 0, 0))
            if time() >= time_to_next_animation:
                if by_account < 10:
                    by_account += 1
                    self.image = sprites['pacman']["DEATH"][by_account]
                    if by_account == 10:
                        self.image.set_alpha(255)
                        time_to_next_animation = time() + 0.3
                    else:
                        time_to_next_animation = time() + 0.1
                else:
                    self.image.set_alpha(0)
            all_sprites.draw(screen)
            pygame.display.flip()
            clock.tick(120)
        time_to_load_new_level = time() + .2
        screen.fill((0, 0, 0))
        pygame.display.flip()
        while time() < time_to_load_new_level:
            clock.tick(30)
        attempts -= 1
        if attempts < 0:
            start_screen('Вы проиграли, но вы можете продолжить. Нажмите любую кнопку чтобы продолжить')
            reset_game()
        else:
            load_level()

    def update(self):
        self.image = sprites['pacman'][self.last_motion][self.animation_stage]
        if pygame.sprite.spritecollideany(self, points):
            for x in pygame.sprite.spritecollide(self, points, False):
                add_points(10)
                x.kill()
            if not points:
                WIN()
        if pygame.sprite.spritecollideany(self, ghosts):
            self.death()
        elif not pygame.sprite.collide_mask(self, Location_obj):
            if self.rect.x < -25:
                self.rect.x = width - pacman_width[0]
            elif self.rect.x > width - 3:
                self.rect.x = 1
            self.last = self.rect.x, self.rect.y
            self.rect = self.rect.move(*self.last_motion)
            if pygame.sprite.collide_mask(self, Location_obj):
                self.rect = self.rect.move(self.last[0] - self.rect.x, self.last[1] - self.rect.y)
                self.animation_stage = 0
            elif time() >= self.animation_change_delay:
                self.animation_change_delay = time() + 0.1
                self.animation_stage = abs(self.animation_stage - 1)
        if self.can_move_to(motion):
            self.last_motion = motion


LEFT, RIGHT, DOWN, UP = (-1, 0), (1, 0), (0, 1), (0, -1)

motion = LEFT

pacman_width = (28, 32)

sprites = {
    'ghost': {'red': {LEFT: (pygame.transform.scale(pygame.image.load("data/ghost_red_01.png"), pacman_width),
                             pygame.transform.scale(pygame.image.load("data/ghost_red_02.png"), pacman_width)),
                      RIGHT: (pygame.transform.scale(pygame.image.load("data/ghost_red_11.png"), pacman_width),
                              pygame.transform.scale(pygame.image.load("data/ghost_red_12.png"), pacman_width)),
                      DOWN: (pygame.transform.scale(pygame.image.load("data/ghost_red_21.png"), pacman_width),
                             pygame.transform.scale(pygame.image.load("data/ghost_red_22.png"), pacman_width)),
                      UP: (pygame.transform.scale(pygame.image.load("data/ghost_red_31.png"), pacman_width),
                           pygame.transform.scale(pygame.image.load("data/ghost_red_32.png"), pacman_width))},
              'pink': {LEFT: (pygame.transform.scale(pygame.image.load("data/ghost_pink_01.png"), pacman_width),
                             pygame.transform.scale(pygame.image.load("data/ghost_pink_02.png"), pacman_width)),
                      RIGHT: (pygame.transform.scale(pygame.image.load("data/ghost_pink_11.png"), pacman_width),
                              pygame.transform.scale(pygame.image.load("data/ghost_pink_12.png"), pacman_width)),
                      DOWN: (pygame.transform.scale(pygame.image.load("data/ghost_pink_21.png"), pacman_width),
                             pygame.transform.scale(pygame.image.load("data/ghost_pink_22.png"), pacman_width)),
                      UP: (pygame.transform.scale(pygame.image.load("data/ghost_pink_31.png"), pacman_width),
                           pygame.transform.scale(pygame.image.load("data/ghost_pink_32.png"), pacman_width))},
              'blue': {LEFT: (pygame.transform.scale(pygame.image.load("data/ghost_blue_01.png"), pacman_width),
                              pygame.transform.scale(pygame.image.load("data/ghost_blue_02.png"), pacman_width)),
                       RIGHT: (pygame.transform.scale(pygame.image.load("data/ghost_blue_11.png"), pacman_width),
                               pygame.transform.scale(pygame.image.load("data/ghost_blue_12.png"), pacman_width)),
                       DOWN: (pygame.transform.scale(pygame.image.load("data/ghost_blue_21.png"), pacman_width),
                              pygame.transform.scale(pygame.image.load("data/ghost_blue_22.png"), pacman_width)),
                       UP: (pygame.transform.scale(pygame.image.load("data/ghost_blue_31.png"), pacman_width),
                            pygame.transform.scale(pygame.image.load("data/ghost_blue_32.png"), pacman_width))},},
    'pacman': {'ATTEMPT': pygame.transform.scale(pygame.image.load('data/pacman_attempts.png'), (20, 22)),
               'IDLE': pygame.transform.scale(pygame.image.load("data/pacman_idle.png"), pacman_width),
               'DEATH': (pygame.transform.scale(pygame.image.load("data/pacman_death1.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death2.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death3.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death4.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death5.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death6.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death7.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death8.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death9.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death10.png"), pacman_width),
                         pygame.transform.scale(pygame.image.load("data/pacman_death11.png"), (30, 22))),
               LEFT: (pygame.transform.scale(pygame.image.load("data/pacman01.png"), pacman_width),
                      pygame.transform.scale(pygame.image.load("data/pacman02.png"), pacman_width)),
               RIGHT: (pygame.transform.scale(pygame.image.load("data/pacman11.png"), pacman_width),
                       pygame.transform.scale(pygame.image.load("data/pacman12.png"), pacman_width)),
               DOWN: (pygame.transform.scale(pygame.image.load("data/pacman21.png"), pacman_width),
                      pygame.transform.scale(pygame.image.load("data/pacman22.png"), pacman_width)),
               UP: (pygame.transform.scale(pygame.image.load("data/pacman31.png"), pacman_width),
                    pygame.transform.scale(pygame.image.load("data/pacman32.png"), pacman_width))},
    'circle_of_point': pygame.transform.scale(pygame.image.load("data/circle_of_point.png"), (8, 8)),
}

attempts = 2
TOTAL_POINTS = 0

reset_game()

points_tab = font.render(str(TOTAL_POINTS), True, pygame.Color('white'))
intro_rect = points_tab.get_rect()
intro_rect.x = 10
intro_rect.top = 10

while running:
    screen.fill((0, 0, 0))
    for i in range(attempts):
        screen.blit(sprites['pacman']['ATTEMPT'], (30 + 30 * i, 330))
    screen.blit(points_tab, intro_rect)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            print(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                last_motion = motion
                motion = LEFT
            elif event.key == pygame.K_RIGHT:
                last_motion = motion
                motion = RIGHT
            if event.key == pygame.K_UP:
                last_motion = motion
                motion = UP
            elif event.key == pygame.K_DOWN:
                last_motion = motion
                motion = DOWN
    all_sprites.draw(screen)
    all_sprites.update()
    clock.tick(90)
    pygame.display.flip()
pygame.quit()