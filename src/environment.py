import numpy as np
from render import render


class environment:
    def __init__(self) -> None:
        self.light_source = np.array([0, 1, 0])
        self.camera = np.array([0, 0, -1])
        self.shapes = []
        self.renderer = render()

    def add_shape(self, shape):
        self.shapes.append(shape)

    def spin_shapes(self):
        for shape in self.shapes:
            shape.spin()

    def time_step(self):
        self.spin_shapes()
        self.shading()
        self.who_is_seen()
        self.render_shapes()

    def render_shapes(self):
        for shape in self.shapes:
            self.renderer.to_buff(shape)
        self.renderer.render()

    def shading(self):
        for shape in self.shapes:
            shading = np.dot(shape.surface_normals, self.light_source)
            shading = np.transpose([shading])
            shape.tris_to_render = np.append(shape.tris, shading, axis=1)

    def who_is_seen(self):
        for shape in self.shapes:
            seen_mask = np.dot(shape.surface_normals, self.camera)
            shape.seen_tris_mask(seen_mask)
