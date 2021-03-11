# main.py Graham Seamans 2020

import cProfile
import pstats
import time

from shapes import tetrahedron, cube
from environment import environment


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    env = environment()
    env.add_shape(cube())
    env.add_shape(tetrahedron(spin=-0.01))

    for i in range(10000):
        env.time_step()
        time.sleep(0.01)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.strip_dirs().sort_stats("tottime").print_stats(10)
