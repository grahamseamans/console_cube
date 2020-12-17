import os
import time

screen_height = 25
screen_width = 50
pixels = 25 * 50


class render:
    def __init__(self):
        self.pre_screen = []
        self.post_screen = []

        for _ in range(pixels):
            self.pre_screen.append("@")

        for _ in range(pixels):
            self.post_screen.append(" ")

        os.system("clear")

    def cordinates_from_index(i):
        y = i // screen_width
        x = i % screen_width
        return (x, y)

    def index_from_cordinates(x, y):
        return (y * screen_width) + x

    def render(self):
        for j, (post, pre) in enumerate(zip(self.post_screen, self.pre_screen)):
            if pre != post:
                pass
                x, y = self.index_from_cordinates(j)
                os.system(f' echo "\x1B[{y};{x}H{post}"')
                self.pre_screen[j] = self.post_screen[j]


r = render()

for i in range(100):
    r.render()
    r.post_screen[(i * 15) % pixels] = "#"


os.system(f' echo "\x1B[{screen_height};{0}Hall done"')
