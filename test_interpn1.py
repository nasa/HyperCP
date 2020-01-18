
from scipy.interpolate import interpn
import numpy as np

arr = np.random.random((4,4,4,4))
x1 = np.array([0, 1, 2, 3])
x2 = np.array([0, 10, 20, 30])
x3 = np.array([0, 10, 20, 30])
x4 = np.array([0, .1, .2, .30])
points = (x1, x2, x3, x4) # 4, 4, 4, 4

x10 = [0.1]                # 1
x20 = [9]                  # 1
x30 = np.linspace(0, 30, 3) # 3
x40 = np.linspace(0, 0.3, 4) # 4

interp_mesh = np.array(np.meshgrid(
    x10, x20, x30, x40)) # 4, 1, 1, 3, 4
# interp_points = np.rollaxis(interp_mesh, 0, 5)
interp_points = np.moveaxis(interp_mesh, 0, -1) # 1, 1, 3, 4, 4
interp_points = interp_points.reshape((interp_mesh.size // 4, 4)) # 12, 4
result = interpn(points, arr, interp_points) # 12

print('done')