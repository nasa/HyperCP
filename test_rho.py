
import collections
import numpy as np
import get_sky_sun_rho

relAz = 135
 # === environmental conditions during experiment ===
env = collections.OrderedDict()
env['wind'] = 10
env['od'] = 0.1
env['C'] = 0 
env['zen_sun'] = 30
env['wtem'] = 25
env['sal'] = 34

# === The sensor ===
# the zenith and azimuth angles of light that the sensor will see
# 0 azimuth angle is where the sun located
# positive z is upward
sensor = collections.OrderedDict()
sensor['ang'] = [40,180-relAz]
sensor['wv'] = np.arange(350, 1001,10).tolist()

rho = get_sky_sun_rho.Main(env,sensor)

print(rho['ρ'])