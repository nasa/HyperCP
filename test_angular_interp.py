
import numpy as np
import scipy.interpolate
from scipy.interpolate import splev, splrep

new_x = [0, 25, 35, 55]
x = [0,10,20,30, 40, 50,60]
y = [0, 0,65,180,270,0, 90]
#     0, 122.5, 225, 45

# complement360 = np.rad2deg(np.unwrap(np.deg2rad(y)))
y_rad = np.deg2rad(y)


f = scipy.interpolate.interp1d(x,y_rad,kind='linear', bounds_error=False, fill_value=None)
new_y_rad = f(new_x)%(2*np.pi)
new_y = np.rad2deg(new_y_rad)
print(new_y)
# print(np.rad2deg(2*np.pi))