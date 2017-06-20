import numpy as np
from scipy.interpolate import NearestNDInterpolator

points = np.array([[1.1, 2.5],
                   [1.5, 5.2],
                   [3.1, 3.0],
                   [2.0, 6.0],
                   [2.8, 4.7]])
values = np.array([0, 1, 1, 0, 0])

myInterpolator = NearestNDInterpolator(points, values)

print myInterpolator(1.1,2.5)

print myInterpolator(1.7,4.5)

print myInterpolator(2.5,4.0)
