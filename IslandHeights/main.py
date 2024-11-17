import requests
import pygame
from settings import *

class Tile():
    def __init__(self, x, y, height, max_height):
        self.mx = y * TILESIZE
        self.my = x * TILESIZE
        self.x = x
        self.y = y
        self.height = int(height)
        self.surface = pygame.Surface((TILESIZE, TILESIZE))
        self.color = None
        self.set_color(self.height_to_color(max_height))
        self.checked = False

    def height_to_color(self, max_height):
        normalized = (self.height - MIN_HEIGHT)/(max_height - MIN_HEIGHT)
        normalized = max(0, min(1, normalized))

        if normalized == 0:
            return BLUE
        elif normalized < 0.4:
            ratio = normalized * 2
            r = int(GREEN[0] + ratio * (YELLOW[0] - GREEN[0]))
            g = int(GREEN[1] + ratio * (YELLOW[1] - GREEN[1]))
            b = int(GREEN[2] + ratio * (YELLOW[2] - GREEN[2]))
        elif normalized < 0.8:
            ratio = (normalized - 0.4) * 2
            r = int(YELLOW[0] + ratio * (BROWN[0] - YELLOW[0]))
            g = int(YELLOW[1] + ratio * (BROWN[1] - YELLOW[1]))
            b = int(YELLOW[2] + ratio * (BROWN[2] - YELLOW[2]))

        else:
            ratio = (normalized - 0.8) * 2
            r = int(BROWN[0] + ratio * (WHITE[0] - BROWN[0]))
            g = int(BROWN[1] + ratio * (WHITE[1] - BROWN[1]))
            b = int(BROWN[2] + ratio * (WHITE[2] - BROWN[2]))

        return r, g, b

    def draw(self, map_surface):
        map_surface.blit(self.surface, (self.mx, self.my))

    def check(self):
        self.checked = not self.checked

    def set_color(self, color):
        self.color = color
        self.surface.fill(self.color)

class Map:
    def __init__(self):
        self.req = requests.get(URL).text.split()
        self.map_surface = pygame.Surface((WIDTH, HEIGHT))
        self.map_matrix = [[None for _ in range(COLS)] for _ in range(ROWS)]

        max_height = max(list(map(int, self.req)))
        for i in range(len(self.req)):
            x = i % ROWS
            y = i // ROWS  # This will move to the next row when x fills up
            height = int(self.req[i])
            self.map_matrix[x][y] = Tile(x, y, height, max_height)


    def check_island(self, mx, my):
        if mx >= COLS or mx < 0 or my >= ROWS or my < 0:
            return 0

        suma = 0
        if not self.map_matrix[mx][my].checked and self.map_matrix[mx][my].height > 0:
            suma += self.map_matrix[mx][my].height
            self.map_matrix[mx][my].check();
            suma += self.check_island(mx + 1, my)
            suma += self.check_island(mx, my + 1)
            suma += self.check_island(mx - 1, my)
            suma += self.check_island(mx, my - 1)

        return suma

    def uncheck_island(self, x, y):
        if x >= COLS or x < 0 or y >= ROWS or y < 0:
            return 0

        num = 0
        if self.map_matrix[x][y].checked:
            num += 1
            self.map_matrix[x][y].check()
            num += self.uncheck_island(x + 1, y)
            num += self.uncheck_island(x, y + 1)
            num += self.uncheck_island(x - 1, y)
            num += self.uncheck_island(x, y - 1)

        return num

    def calculate_best_average(self):
        maks = -1
        for row in self.map_matrix:
            for tile in row:
                total_height = self.check_island(tile.x, tile.y)
                total_tiles = self.uncheck_island(tile.x, tile.y)
                average = total_height/total_tiles if total_tiles > 0 else -1

                if average > maks:
                    maks = average

        return maks

    def display_map(self):
        for row in self.map_matrix:
            for tile in row:
                tile.draw(self.map_surface)


class Game():
    def __init__(self):
        self.best_average = None
        self.map = None
        self.attempts = None
        self.score = START_SCORE
        self.running = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('IslandHeights')
        self.font = pygame.font.SysFont("Arial", 48)
        self.font_score = pygame.font.SysFont("Arial", 40)

        pygame.mixer.init()
        self.victory_sound = pygame.mixer.Sound("cheer.wav")
        self.wrong_sound = pygame.mixer.Sound("wrong.wav")
        self.game_over_sound = pygame.mixer.Sound("game_over.wav")
        pygame.mixer.music.load("casual_music.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

    def new(self):
        self.map = Map()
        self.map.display_map()
        self.best_average = self.map.calculate_best_average()
        self.attempts = ATTEMPT_NUM
        # print('Max: ' + str(self.best_average))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    my, mx = pygame.mouse.get_pos()
                    col = mx // TILESIZE
                    row = my // TILESIZE

                    if self.map.map_matrix[col][row].color == RED or self.map.map_matrix[col][row].color == BLUE:
                        continue


                    self.map.map_matrix[col][row].set_color(RED)
                    self.map.display_map()
                    total_height = self.map.check_island(col, row)
                    total_tiles = self.map.uncheck_island(col, row)
                    average = total_height / total_tiles if total_tiles > 0 else -1

                    if average == self.best_average:
                        self.victory_sound.play()
                        self.score += 1
                        self.display_you_win()

                    else:
                        self.color_wrong_island(col, row)
                        self.map.display_map()
                        self.attempts -= 1
                        self.wrong_sound.play()
                        if self.attempts == 0:
                            self.game_over_sound.play()
                            self.game_over()

                self.screen.blit(self.map.map_surface, (0, 0))
                self.display_score(self.score)
                pygame.display.flip()

    def color_wrong_island(self, x, y):
        if x >= COLS or x < 0 or y >= ROWS or y < 0:
            return 0

        if not self.map.map_matrix[x][y].checked and self.map.map_matrix[x][y].height > 0:
            self.map.map_matrix[x][y].check()
            self.map.map_matrix[x][y].set_color(RED)
            self.color_wrong_island(x + 1, y)
            self.color_wrong_island(x, y + 1)
            self.color_wrong_island(x - 1, y)
            self.color_wrong_island(x, y - 1)

    def display_message(self, message, color):
        self.screen.fill(color)
        text_surface = self.font.render(message, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()

    def display_score(self, score):
        score_text = self.font_score.render(f"Score: {str(score)}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

    def game_over(self):
        self.display_game_over()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.score = START_SCORE
                    self.new()
                    return

    def display_you_win(self):
        self.screen.fill(GREEN)
        text_surface = self.font.render('Correct!', True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

        text_surface = self.font.render("Score: " + str(self.score), True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()

        pygame.time.wait(1500)
        self.new()

    def display_game_over(self):
        self.screen.fill(RED)
        text_surface = self.font.render('Game Over!', True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

        text_surface = self.font.render("Score: " + str(self.score), True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
        self.screen.blit(text_surface, text_rect)

        text_surface = self.font.render('Press R to Restart', True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 350))
        self.screen.blit(text_surface, text_rect)

        pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    game = Game()
    game.new()
    game.run()
    pygame.quit()