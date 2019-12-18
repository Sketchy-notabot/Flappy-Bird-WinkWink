import pygame as pg
import os
import cv2
import dlib
import random
from math import hypot
pg.font.init()


Win_Width = 1200
Win_Height = 700
font = pg.font.SysFont("comicsans", 50)
fontt = cv2.FONT_HERSHEY_DUPLEX
Player_img = pg.transform.scale2x(pg.image.load(os.path.join("images", "icon.png")))
Bg_img = pg.transform.scale2x(pg.image.load(os.path.join("images", "bg1.png")))
ground_img = pg.transform.scale2x(pg.image.load(os.path.join("images", "groud.png")))
pipe_img = pg.transform.scale2x(pg.image.load(os.path.join("images", "pipe.png")))
game_over = pg.transform.scale2x(pg.image.load(os.path.join("images", "bg.png")))


class Player:
    IMG = Player_img
    maxrot = 25
    rotval = 20

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.vel = 0
        self.height = self.y
        self.tick_count = 0
        self.img = self.IMG

    def jump(self):
        self.vel = -12.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel*self.tick_count + 1.5*(self.tick_count**2)

        if d >= 16:
            d = 16
        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.maxrot:
                self.tilt = self.maxrot
        else:
            if self.tilt > -90:
                self.tilt -= self.rotval

    def draw(self, win):
        rot_img = pg.transform.rotate(self.img, self.tilt)
        new_rect = rot_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rot_img, new_rect.topleft)

    def get_mask(self):
        return pg.mask.from_surface(self.img)


class Pipe:
    Gap = 300
    vel = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.pipe_top = pg.transform.flip(pipe_img, False, True)
        self.pipe_bottom = pipe_img

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.pipe_top.get_height()
        self.bottom = self.height + self.Gap

    def move(self):
        self.x -= self.vel

    def draw(self, win):
        win.blit(self.pipe_top, (self.x, self.top))
        win.blit(self.pipe_bottom, (self.x, self.bottom))

    def collision(self, player):
        player_mask = player.get_mask()
        top_mask = pg.mask.from_surface(self.pipe_top)
        bottom_mask = pg.mask.from_surface(self.pipe_bottom)

        b_offset = (self.x - player.x, self.bottom - round(player.y))
        t_offset = (self.x - player.x, self.top - round(player.y))

        b_point = player_mask.overlap(bottom_mask, b_offset)
        t_point = player_mask.overlap(top_mask, t_offset)

        if b_point or t_point:
            return True

        return False


def midpoint(p1, p2):
    return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)


def blinking_ratio(eye, landmarks):
    left_point = (landmarks.part(eye[0]).x, landmarks.part(eye[0]).y)
    right_point = (landmarks.part(eye[3]).x, landmarks.part(eye[3]).y)
    top_point = midpoint(landmarks.part(eye[1]), landmarks.part(eye[2]))
    bottom_point = midpoint(landmarks.part(eye[5]), landmarks.part(eye[4]))

    # gray = cv2.circle(gray, top_point, 3, (0, 0, 255), 1)

    hor_length = hypot(left_point[0] - right_point[0], left_point[1] - right_point[1])
    ver_length = hypot(top_point[0] - bottom_point[0], top_point[1] - bottom_point[1])

    blink_ratio = hor_length / ver_length
    return blink_ratio


def draw_win(win, bird, pipes, score, run):
    win.blit(Bg_img, (0, 0))
    for pipe in pipes:
        pipe.draw(win)

    if run:
        text = font.render("Score: " + str(score), 1, (255, 255, 255))
        win.blit(text, (Win_Width - 10 - text.get_width(), 10))
        bird.draw(win)
    else:
        text = font.render("GAME OVER, Score: " + str(score), 1, (200, 0, 0))
        win.blit(text, (450, 300))

    pg.display.update()
    if not run:
        pg.time.delay(2000)


def main():
    player = Player(200, 200)
    pipes = [Pipe(700), Pipe(1200)]
    win = pg.display.set_mode((Win_Width, Win_Height))
    clock = pg.time.Clock()
    score = 0
    f = 0

    cap = cv2.VideoCapture(0)
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    run = True
    while run:
        clock.tick(30)
        ret, frame = cap.read()
        graay = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(graay)

        for face in faces:
            landmarks = predictor(graay, face)
            cv2.rectangle(graay, (face.left(), face.top()), (face.right(), face.bottom()), (255, 0, 255), 2)

            blink = blinking_ratio([42, 43, 44, 45, 46, 47], landmarks)
            if blink > 3.21:
                f += 1
                if f > 5:
                    player.jump()
                    graay = cv2.putText(graay, "Blink" + str(blink), (50, 50), fontt, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                    f = 0

        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    player.jump()

        add_pipe = False
        rem_pipes = []
        for pipe in pipes:
            if pipe.collision(player):
                run = False

            if pipe.x + pipe.pipe_top.get_width() < 0:
                rem_pipes.append(pipe)

            if not pipe.passed and pipe.x < player.x:
                pipe.passed = True
                add_pipe = True

            pipe.move()

        if add_pipe:
            score += 1
            pipes.append(Pipe(1200))

        for rem in rem_pipes:
            pipes.remove(rem)

        if player.y < 0:
            player.y = 0
        if player.y > 700:
            run = False

        player.move()
        draw_win(win, player, pipes, score, run)
        cv2.imshow('frame', graay)

    print(score)
    pg.quit()
    cap.release()
    cv2.destroyAllWindows()
    quit()


main()
