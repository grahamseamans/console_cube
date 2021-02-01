from math import sin, cos, sqrt
import numpy as np


class shape:
    def __init__(self, spin=0.01):
        self.angle = 0
        self.spin_change = spin
        self.points = None
        self.rotated = None
        self.tris = None
        self.tris_to_render = None
        self.rotation_matrix = None
        self.surface_normals = None

    def calculate_rotation_matrix(self):
        self.rotation_matrix = self.x_rotation() @ self.y_rotation() @ self.z_rotation()

    def x_rotation(self):
        return np.array(
            [
                [1, 0, 0],
                [0, cos(self.angle), -sin(self.angle)],
                [0, sin(self.angle), cos(self.angle)],
            ]
        )

    def y_rotation(self):
        return np.array(
            [
                [cos(self.angle), 0, -sin(self.angle)],
                [0, 1, 0],
                [sin(self.angle), 0, cos(self.angle)],
            ]
        )

    def z_rotation(self):
        return np.array(
            [
                [cos(self.angle), -sin(self.angle), 0],
                [sin(self.angle), cos(self.angle), 0],
                [0, 0, 1],
            ]
        )

    def update_rotated_points(self):
        rotated_points = []
        for point in self.points:
            rotated_points.append(self.rotation_matrix @ point)
        self.rotated = np.asarray(rotated_points)

    def spin(self):
        self.angle += self.spin_change
        self.calculate_rotation_matrix()
        self.update_rotated_points()
        self.calculate_surface_normals()

    def seen_tris_mask(self, seen_mask):
        self.tris_to_render = self.tris_to_render[seen_mask > 0]

    def calculate_surface_normals(self):
        # https://sites.google.com/site/dlampetest/python/
        #       calculating-normals-of-a-triangle-mesh-using-numpy
        tris_verts = self.rotated[self.tris]  # epic that this works
        self.surface_normals = np.cross(
            tris_verts[::, 1] - tris_verts[::, 0], tris_verts[::, 2] - tris_verts[::, 0]
        )
        self.surface_normals = self.normalize_v3(self.surface_normals)

    def normalize_v3(self, arr):
        # https://sites.google.com/site/dlampetest/python/
        #        calculating-normals-of-a-triangle-mesh-using-numpy
        lens = np.sqrt(arr[:, 0] ** 2 + arr[:, 1] ** 2 + arr[:, 2] ** 2)
        arr[:, 0] /= lens
        arr[:, 1] /= lens
        arr[:, 2] /= lens
        return arr


class cube(shape):
    def __init__(self, spin=0.01):
        super().__init__(spin)
        self.angle = 0
        len = 1 / sqrt(3)
        self.points = np.array(
            [
                [-len, -len, -len],
                [len, -len, -len],
                [len, len, -len],
                [-len, len, -len],
                [-len, -len, len],
                [len, -len, len],
                [len, len, len],
                [-len, len, len],
            ]
        )
        self.tris = np.array(
            [
                [2, 5, 6],
                [2, 1, 5],
                [1, 0, 4],
                [1, 4, 5],
                [3, 2, 6],
                [3, 6, 7],
                [0, 3, 7],
                [0, 7, 4],
                [7, 6, 5],
                [7, 5, 4],
                [2, 3, 0],
                [3, 0, 2],
            ]
        )
        self.render = None


class tetrahedron(shape):
    def __init__(self, spin=0.01):
        super().__init__(spin)
        self.angle = 0
        self.points = np.array(
            [
                [sqrt(8 / 9), 0, -1 / 3],
                [-sqrt(2 / 9), sqrt(2 / 3), -1 / 3],
                [-sqrt(2 / 9), -sqrt(2 / 3), -1 / 3],
                [0, 0, 1],
            ]
        )
        self.tris = np.array([[0, 2, 3], [0, 3, 1], [0, 1, 2], [1, 3, 2]])
        self.render = None
