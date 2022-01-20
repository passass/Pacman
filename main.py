import sys
import pygame
from csv import reader
from time import time
from random import choice, randint

pygame.font.init()
font = pygame.font.Font(pygame.font.match_font('consolas'), 30)
screen_font = pygame.font.Font(pygame.font.match_font('consolas'), 24)

pygame.display.set_caption('Pacman')

width, height = 928, 392
screen = pygame.display.set_mode((width, height))
sprite = pygame.sprite.Sprite()
all_sprite = pygame.sprite.Group()
clock = pygame.time.Clock()
running = True


def terminate():
    pygame.quit()
    sys.exit()


def start_screen(*text, indent=240):
    screen.fill((0, 0, 0))
    pygame.display.flip()
    text_coord = 180
    for line in text:
        string_rendered = screen_font.render(line, True, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = indent
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

now = 0

start_screen('Нажмите любую кнопку чтобы продолжить')

levels_settings = {
    # картинка карты, картинка хитбоксов карты, координаты спавна пакмана,
    # параметры призраков, координаты кнопки старт, менять ли размер окна (пустой если не надо),
    # координаты зоны из которой выходят призраки
    1: (pygame.transform.scale(pygame.image.load("data/level_1_background.png"), (width, height - 120)),
        pygame.transform.scale(pygame.image.load("data/level_1_walls_hitbox.png"), (width, height - 120)),
        (570, 292), ((528, 167, 'red', 0), (595, 167, 'pink', 0), (565, 167, 'yellow', 450), (560, 167, 'blue', 900)),
        (525, 220), (928, 392), (520, 150, 623, 212)),
    2: (pygame.transform.scale(pygame.image.load("data/level_2_background.png"), (448, 496)),
        pygame.transform.scale(pygame.image.load("data/level_2_walls_hitbox.png"), (448, 496)),
        (212, 420), ((178, 280, 'red', 0), (240, 280, 'pink', 0), (206, 280, 'yellow', 450), (230, 280, 'blue', 900)),
        (178, 332), (448, 616), (168, 260, 280, 324)),
}

pygame.mixer.init()

sounds = {
    'chomp': pygame.mixer.Sound('data/pacman_chomp.wav'),
    'eatfruit': pygame.mixer.Sound('data/pacman_eatfruit.wav'),
    'eatghost': pygame.mixer.Sound('data/pacman_eatghost.wav'),
    'backtobase': pygame.mixer.Sound('data/pacman_ghostbacktobase.wav')
}


def music_player(sound):
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(f'data/{sound}')
        pygame.mixer.music.play()
        pygame.mixer.music.set_volume(0.1)


class Location(pygame.sprite.Sprite):
    def __init__(self, picture, *group):
        super().__init__(*group)
        self.image = picture
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 0
        self.rect.y = 60

    def update(self):
        pass


class Circle_of_point(pygame.sprite.Sprite):
    def __init__(self, x, y, point_type='normal', *group):
        super().__init__(*group)
        if point_type == 'fruit':
            self.image = choice(sprites['circle_of_point'][point_type])
            self.rect = self.image.get_rect()
            self.rect.x, self.rect.y = x - 3, y - 3
            while pygame.sprite.collide_mask(self, Location_obj):
                self.rect.y += 1
            self.rect.y += 1
        else:
            self.image = sprites['circle_of_point'][point_type]
            self.rect = self.image.get_rect()
            if point_type == 'killer':
                self.rect.x, self.rect.y = x - 6, y - 6
            else:
                self.rect.x, self.rect.y = x - 3, y - 3
        self.type = point_type


class Point_title(pygame.sprite.Sprite):
    def __init__(self, x, y, count=100, *group):
        super().__init__(*group)
        self.image = sprites[count]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x, self.rect.y = x + 3, y
        self.tick_count = 0

    def update(self):
        self.tick_count += 1
        if self.tick_count % 3 == 0:
            self.rect.y -= 1
        if self.tick_count >= 60:
            self.kill()


def reset_game():
    global CURRENT_LEVEL, attempts, points, TOTAL_POINTS, all_fruits, BEST_SCORE_TAB
    try:
        with open('best_score.txt', 'r') as file:
            BEST_SCORE_TAB = font.render(str(file.readlines()[0]), True, pygame.Color('white'))
    except Exception:
        BEST_SCORE_TAB = font.render('0', True, pygame.Color('white'))
    TOTAL_POINTS = 0
    all_fruits = 0
    attempts = 2
    CURRENT_LEVEL = 1
    load_points_locations()
    load_level()


def load_points_locations():
    with open(f'data/level_{CURRENT_LEVEL}_points_places.csv', 'r', newline='') as csvfile:
        global points
        points = pygame.sprite.Group()
        list_of_points = list(reader(csvfile, delimiter=';'))
        for x, y in list_of_points[:-4]:
            points.add(Circle_of_point(int(x) * 2, int(y) * 2 + 60, 'normal'))
        for x, y in list_of_points[-4:]:
            points.add(Circle_of_point(int(x) * 2, int(y) * 2 + 60, 'killer'))


def load_level():
    global Location_obj, ghosts, all_sprites, Pacman_obj, time_to_create_fruit, motion
    motion = LEFT
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
    music_player('pacman_beginning.wav')
    string_rendered = font.render('START!', True, pygame.Color('yellow'))
    intro_rect = string_rendered.get_rect()
    intro_rect.x = levels_settings[CURRENT_LEVEL][4][0]
    intro_rect.top = levels_settings[CURRENT_LEVEL][4][1]
    a = time() + 4
    while time() < a:
        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        screen.blit(string_rendered, intro_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        clock.tick(50)
    time_to_create_fruit = now + randint(1350, 2250)


def add_points(count):
    global TOTAL_POINTS, points_tab
    TOTAL_POINTS += count
    points_tab = font.render(str(TOTAL_POINTS), True, pygame.Color('white'))


def WIN():
    global CURRENT_LEVEL, all_fruits
    CURRENT_LEVEL += 1
    all_fruits = 0
    time_to_win = 0
    pygame.display.flip()
    if CURRENT_LEVEL not in levels_settings:
        while time_to_win < 34:
            time_to_win += 1
            clock.tick(34)
        try:
            with open('best_score.txt', 'r') as file1:
                global TOTAL_POINTS
                if int(file1.readlines()[0]) < TOTAL_POINTS:
                    with open('best_score.txt', 'w+') as file2:
                        file2.write(str(TOTAL_POINTS))
        except Exception:
            with open('best_score.txt', 'w+') as file2:
                file2.write(str(TOTAL_POINTS))
        start_screen(f'Вы выиграли, но вы можете продолжить играть. Нажмите любую кнопку чтобы продолжить',
                     f'                 Ваш итоговый счёт {TOTAL_POINTS}', indent=10)
        reset_game()
    else:
        while time_to_win < 34:
            time_to_win += 1
            clock.tick(34)
        start_screen('Нажмите любую кнопку чтобы продолжить')
        global points
        points = pygame.sprite.Group()
        load_points_locations()
        load_level()


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, color, release_time=10, *group):
        super().__init__(*group)
        self.color = color
        self.image = sprites['ghost'][color][LEFT][0]
        self.animation_stage = False
        self.animation_change_delay = 0
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.start_pos = (x, y)
        self.rect.x = x
        self.rect.y = y
        self.motion = choice([LEFT, RIGHT])
        self.motion_dont_move_to = []
        self.release_time = now + release_time
        self.released = now >= self.release_time
        self.stucked = None
        self.fright_time = 0
        self.is_scary = False
        self.is_death = False
        self.glowing = False
        self.glowing_time = 0
        self.back_to_start_pos_at = 0

    def killed(self):
        ticks = 0
        while ticks < 15:
            ticks += 1
            clock.tick(30)
        self.is_death = True
        self.is_scary = False
        self.fright_time = 0
        self.back_to_start_pos_at = now + 450
        self.motion_dont_move_to = []


    def sees_pacman(self, sides):
        last_rect = self.rect
        for x in sides:
            while True:
                self.do_a_move(x, False)
                if pygame.sprite.collide_mask(self, Location_obj):
                    break
                elif pygame.sprite.collide_mask(self, Pacman_obj):
                    self.rect = last_rect
                    return x
            self.rect = last_rect
        return False

    def choice_move_to_base(self, sides, base_coords):
        x1, y1, x2, y2 = base_coords
        if self.stucked:
            del sides[sides.index(self.motion)]

        if x1 < self.rect.x < x2 :
            if y1 < self.rect.y < y2:
                return DOWN
            elif y1 - 38 < self.rect.y < y1:
                if DOWN in sides:
                     return DOWN
        elif self.rect.x < x1:
            if RIGHT in sides:
                 return RIGHT
        else:
            if LEFT in sides:
                return LEFT
        if self.rect.y < y1:
            if DOWN in sides:
                return DOWN
        else:
            if UP in sides:
                return UP
        return False

    def possible_move_to_sides(self, sides=None, block_motion=True):
        last_rect = self.rect
        if sides is None:
            sides = [LEFT, RIGHT, DOWN, UP]
        for x in sides:
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
        if list(self.possible_move_to_sides([self.motion], False)):
            new_sides = [x for x in sides if abs(x[0]) != abs(self.motion[0])]
        else:
            new_sides = sides
        if not new_sides:
            return self.motion
        new_sides.append(self.motion)
        x1, y1, x2, y2 = levels_settings[CURRENT_LEVEL][6]
        if self.is_death:
            if now > self.back_to_start_pos_at:
                self.is_death = False
                self.rect.x, self.rect.y = self.start_pos
                return self.choose_side_to_move()
            if x1 < self.rect.x < x2 and y1 + 6 < self.rect.y < y2:
                self.is_death = False
            return self.choice_move_to_base(new_sides, (x1, y1, x2, y2)) or choice(new_sides)
        elif x1 < self.rect.x < x2 and y1 < self.rect.y < y2:
            if x1 < self.rect.x < x2 and y1 < self.rect.y < y2:
                self.is_death = False
            if UP in new_sides and (not self.stucked or self.motion != UP):
                return UP
            start_pos = self.rect
            moves_count = [0] * len(new_sides)
            for i in range(len(new_sides)):
                while x1 < self.rect.x < x2 and y1 < self.rect.y < y2 and moves_count[i] < 11:
                    moves_count[i] += 1
                    if pygame.sprite.collide_mask(self, Location_obj):
                        moves_count[i] = 12
                        break
                    elif self.possible_move_to_sides(new_sides[i], False):
                        self.do_a_move(new_sides[i], False)
                self.rect = start_pos
            return new_sides[moves_count.index(min(moves_count))]
        else:
            if DOWN in new_sides and x1 < self.rect.x < x2 and y1 < self.rect.y + pacman_width[1] + 3 < y2:
                new_sides.remove(DOWN)
            return not self.is_scary and self.sees_pacman(new_sides) or choice(new_sides)

    def do_a_move(self, side_to_move=None, take_into_collision=True):
        self.stucked = False
        if self.rect.x < -25:
            self.rect.x = width - pacman_width[0]
        elif self.rect.x > width - 3:
            self.rect.x = 1
        last_x, last_y = self.rect.x, self.rect.y
        if side_to_move is None:
            side_to_move = self.choose_side_to_move()
        self.rect = self.rect.move(*side_to_move)
        self.motion = side_to_move
        if pygame.sprite.collide_mask(self, Location_obj) and take_into_collision:
            self.stucked = True
            self.motion_dont_move_to = [self.motion]
            self.motion = self.choose_side_to_move()
            self.rect.x, self.rect.y = last_x, last_y

    def update(self):
        self.image = self.is_death and sprites['ghost']['death'][self.motion] or \
            not self.is_scary and sprites['ghost'][self.color][self.motion][self.animation_stage] or \
            sprites['ghost']['scary'][self.glowing][self.animation_stage]
        if self.is_scary:
            if now > self.glowing_time:
                self.glowing = not self.glowing
                self.glowing_time = now + 23
        if self.released:
            self.do_a_move()
            if self.is_death:
                self.do_a_move()
            if now > self.fright_time or self.is_death:
                self.do_a_move()
                if self.fright_time and not self.is_death:
                    self.fright_time = 0
                    self.is_scary = False
        else:
            self.released = now >= self.release_time
            if now > self.fright_time and self.fright_time:
                self.fright_time = 0
                self.is_scary = False
        if now >= self.animation_change_delay:
            self.animation_change_delay = now + 9
            self.animation_stage = not self.animation_stage


class Pacman(pygame.sprite.Sprite):
    def __init__(self, x, y, *group):
        super().__init__(*group)
        self.image = sprites['pacman']['IDLE']
        self.animation_stage = False
        self.animation_change_delay = 0
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = x
        self.rect.y = y
        self.last = None
        self.last_motion = LEFT
        self.must_play_eat_sound = False
        self.time_to_play_sound = 0

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
        ticks = 0
        while ticks < 30:
            ticks += 1
            clock.tick(30)
        time_to_load_new_level = ticks + 150
        time_to_next_animation = ticks
        by_account = -1
        ghosts = pygame.sprite.Group()
        music_player('pacman_death.wav')
        while ticks < time_to_load_new_level:
            ticks += 1
            screen.fill((0, 0, 0))
            if ticks >= time_to_next_animation:
                if by_account < 10:
                    by_account += 1
                    self.image = sprites['pacman']["DEATH"][by_account]
                    if by_account == 10:
                        time_to_next_animation = ticks + 18
                    else:
                        time_to_next_animation = ticks + 6
                else:
                    self.kill()
                    time_to_next_animation = ticks + 120
            all_sprites.draw(screen)
            pygame.display.flip()
            clock.tick(60)
        time_to_load_new_level = ticks + 6
        screen.fill((0, 0, 0))
        pygame.display.flip()
        while ticks < time_to_load_new_level:
            ticks += 1
            clock.tick(30)
        attempts -= 1
        if attempts < 0:
            start_screen('Вы проиграли, но вы можете продолжить. Нажмите любую кнопку чтобы продолжить')
            reset_game()
        else:
            load_level()

    def do_a_move(self):
        if pygame.sprite.spritecollideany(self, points):
            global all_fruits, EATED_GHOSTS_COUNT
            for x in pygame.sprite.spritecollide(self, points, False):
                if x.type == 'fruit':
                    add_points(100)
                    all_fruits -= 1
                    sounds['eatfruit'].play()
                    all_sprites.add(Point_title(x.rect.x, x.rect.y, 100))
                elif x.type == 'killer':
                    EATED_GHOSTS_COUNT = 1
                    for x1 in ghosts:
                        x1.is_scary = True
                        x1.fright_time = now + 450
                        x1.glowing_time = now + 315
                        x1.glowing = False
                else:
                    add_points(10)
                x.kill()
            if not points or len(points) == all_fruits:
                WIN()
            else:
                self.must_play_eat_sound = True
        if self.must_play_eat_sound and now >= self.time_to_play_sound:
            self.must_play_eat_sound = False
            self.time_to_play_sound = now + sounds['chomp'].get_length() * 45
            sounds['chomp'].play()
        for x in pygame.sprite.spritecollide(self, ghosts, False):
            if not x.is_death:
                if now > x.fright_time:
                    self.death()
                    return
                else:
                    sounds['eatghost'].play()
                    x.killed()
                    add_points(200 * EATED_GHOSTS_COUNT)
                    all_sprites.add(Point_title(x.rect.x, x.rect.y, 200 * EATED_GHOSTS_COUNT))
                    EATED_GHOSTS_COUNT *= 2
        if not pygame.sprite.collide_mask(self, Location_obj):
            if self.rect.x < -25:
                self.rect.x = width - pacman_width[0]
            elif self.rect.x > width - 3:
                self.rect.x = 1
            self.last = self.rect.x, self.rect.y
            self.rect = self.rect.move(*self.last_motion)
            if pygame.sprite.collide_mask(self, Location_obj):
                self.rect = self.rect.move(self.last[0] - self.rect.x, self.last[1] - self.rect.y)
                self.animation_stage = False
            elif now >= self.animation_change_delay:
                self.animation_change_delay = now + 5
                self.animation_stage = not self.animation_stage
        if self.can_move_to(motion):
            self.last_motion = motion

    def update(self):
        self.image = sprites['pacman'][self.last_motion][self.animation_stage]
        self.do_a_move()
        self.do_a_move()


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
                            pygame.transform.scale(pygame.image.load("data/ghost_blue_32.png"), pacman_width))},
              'yellow': {LEFT: (pygame.transform.scale(pygame.image.load("data/ghost_yellow_01.png"), pacman_width),
                                pygame.transform.scale(pygame.image.load("data/ghost_yellow_02.png"), pacman_width)),
                         RIGHT: (pygame.transform.scale(pygame.image.load("data/ghost_yellow_11.png"), pacman_width),
                                 pygame.transform.scale(pygame.image.load("data/ghost_yellow_12.png"), pacman_width)),
                         DOWN: (pygame.transform.scale(pygame.image.load("data/ghost_yellow_21.png"), pacman_width),
                                pygame.transform.scale(pygame.image.load("data/ghost_yellow_22.png"), pacman_width)),
                         UP: (pygame.transform.scale(pygame.image.load("data/ghost_yellow_31.png"), pacman_width),
                              pygame.transform.scale(pygame.image.load("data/ghost_yellow_32.png"), pacman_width))},
              'scary': ((pygame.transform.scale(pygame.image.load("data/ghost_scary1.png"), pacman_width),
                        pygame.transform.scale(pygame.image.load("data/ghost_scary2.png"), pacman_width)),
                        (pygame.transform.scale(pygame.image.load("data/ghost_white_scary1.png"), pacman_width),
                                pygame.transform.scale(pygame.image.load("data/ghost_white_scary2.png"), pacman_width))),
              'death': {LEFT: pygame.transform.scale(pygame.image.load("data/ghost_eye_0.png"), pacman_width),
                     RIGHT: pygame.transform.scale(pygame.image.load("data/ghost_eye_1.png"), pacman_width),
                     DOWN: pygame.transform.scale(pygame.image.load("data/ghost_eye_2.png"), pacman_width),
                     UP: pygame.transform.scale(pygame.image.load("data/ghost_eye_3.png"), pacman_width)}},
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
    'circle_of_point': {'normal': pygame.transform.scale(pygame.image.load("data/circle_of_point.png"), (8, 8)),
                        'killer': pygame.transform.scale(pygame.image.load("data/circle_of_point.png"), (16, 16)),
                        'fruit': (pygame.transform.scale(pygame.image.load("data/fruit1.png"), (30, 30)),
                                  pygame.transform.scale(pygame.image.load("data/fruit2.png"), (24, 30)),
                                  pygame.transform.scale(pygame.image.load("data/fruit3.png"), (24, 30)),
                                  pygame.transform.scale(pygame.image.load("data/fruit4.png"), (30, 30)),),
                        },
    100: pygame.transform.scale(pygame.image.load("data/100.png"), (26, 14)),
    200: pygame.transform.scale(pygame.image.load("data/200.png"), (30, 14)),
    400: pygame.transform.scale(pygame.image.load("data/400.png"), (30, 14)),
    800: pygame.transform.scale(pygame.image.load("data/800.png"), (30, 14)),
    1600: pygame.transform.scale(pygame.image.load("data/1600.png"), (32, 14)),
}

attempts = 2
TOTAL_POINTS = time_to_create_fruit = CURRENT_LEVEL = EATED_GHOSTS_COUNT = 0

reset_game()

points_tab = font.render(str(TOTAL_POINTS), True, pygame.Color('white'))
points_tab_intro_rect = points_tab.get_rect()
points_tab_intro_rect.x = 10
points_tab_intro_rect.top = 30

BEST_SCORE_TAB_intro_rect = BEST_SCORE_TAB.get_rect()
BEST_SCORE_TAB_intro_rect.x = 200
BEST_SCORE_TAB_intro_rect.top = 30

points_tab_text = font.render('SCORE    BEST SCORE', True, pygame.Color('white'))
points_tab_text_intro_rect = points_tab_text.get_rect()
points_tab_text_intro_rect.x = 10
points_tab_text_intro_rect.top = 5

sounds_delay = {
    'backtobase': 0
}

# Процесс игры
while running:
    screen.fill((0, 0, 0))
    for i in range(1, attempts + 1):
        screen.blit(sprites['pacman']['ATTEMPT'], (30 * i, height - 42))
    screen.blit(points_tab, points_tab_intro_rect)
    screen.blit(points_tab_text, points_tab_text_intro_rect)
    screen.blit(BEST_SCORE_TAB, BEST_SCORE_TAB_intro_rect)
    now += 1
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
    if now >= time_to_create_fruit:
        with open(f'data/level_{CURRENT_LEVEL}_points_places.csv', 'r', newline='') as csvfile:
            csvfile = reader(csvfile, delimiter=';')
            temp1 = []
            for x, y in csvfile:
                temp1.append((x, y))
            temp2 = 0
            while temp2 < len(temp1):
                temp2 += 1
                temp = choice(temp1)
                x, y = int(temp[0]) * 2, int(temp[1]) * 2 + 40
                temp = Circle_of_point(x, y, 'fruit')
                if not pygame.sprite.spritecollideany(temp, points) and not (x - 40 < Pacman_obj.rect.x < x + 72 and
                                                                             y - 40 < Pacman_obj.rect.y < y + 68):
                    all_fruits += 1
                    all_sprites.add(temp)
                    points.add(temp)
                    break
            time_to_create_fruit = now + randint(1575, 2250)
    all_sprites.draw(screen)
    all_sprites.update()
    pygame.display.flip()
    clock.tick(45)
    if now > sounds_delay['backtobase'] and list(filter(lambda x: x.is_death, ghosts)):
        sounds['backtobase'].play()
        sounds_delay['backtobase'] = now + sounds['backtobase'].get_length() * 45
    if list(filter(lambda x: x.is_scary, ghosts)):
        music_player('pacman_ghostscary.wav')
    else:
        music_player('pacman_ghosts_sounds.wav')
pygame.quit()
