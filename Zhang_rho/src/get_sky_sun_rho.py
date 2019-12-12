import argparse
from functools import partial
import pathlib
import sys

import numpy as np
import xarray as xr

π = np.pi

db_path = '../db.mat'
#Groups in db.mat
db, quads, sdb, vdb = None, None, None, None
#Vars. in db.mat
skyrad0, sunrad0, rad_boa_sca, rad_boa_vec = None, None, None, None


def parse_command_line(args):
    'Maps command line arguments to available options.'

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, 
                                     description='Generates ToA Radiance')
    parser.add_argument('-i', '--input_path', type=str, required='True', 
                        help='path to l2 file with Lt available')
    parser.add_argument('-t', '--input_type', type=str, default=)
    parser.add_argument('-o', '--output', type=str, help='Output filename', default='Lt')
    parser.add_argument('-l', '--lines', type=int, default=2030, 
                        help='number of lines to process (top-down)')
    parser.add_argument('-p', '--pixels', type=int, default=1354,
                        help='number of pixels to process (left-right)')
    return parser.parse_args(args)


def gen_vec_quad():
    pass


def get_prob(wind, vec,):
    """
    Computes probability of sky light being reflected into the seson

    Inputs
    ------
    wind :
    vec :

    Outputs
    -------
    prob [np.array] :  probability of sky light reflected into the sensor
    angr_sky[np.array] : reflection angle
    """
    
    with xr.open_dataset(db_path, group='quads') as quads:
        prob = np.Nan * np.ones((quads.zen.size, wind.size*vec.shape[0]))
    angr_sky = prob.copy()
    
    angr_sky, prob = skylight_reflection2(wind, vec)    
    
def skylight_reflection2(wind, sensor, quads):
    """
    Computes probability of light reflection at angle.

    Inputs
    ------
    wind :
            Wind speed (m/s)
    sensor : Numpy array
             The vector of reflected light measured by the sensor

    quads :
            Sky light quads
    """
    # ...
    # p_vec = gen_vec_polar(zen0, quads.sun05, num)
    # prob, ang = prob_reflection(-p_vec, sensor, wind)
    # ...
    # half_azm = np.linspace()
    # sky = gen_vec(quads.zen...)
    # prob, ang = prob_reflection(...)
    

def my_sph2cart(azm, zen, r=1):
    """
    Converts spherical coordinates to cartesian

    Inputs
    -------
    azm [Numpy array] : -azimuth angle 
    zen [Numpy array] : zenith angle
    r  [float] : radius = 1

    Outputs
    -------
    x :
    y :
    z :
    """
    def sph2cart(azm, elev, r):
        cos_elev = np.cos(elev)
        x = r * cos_elev * np.cos(azm)
        y = r * cos_elev * np.sin(azm)
        z = r * np.sin(elev)
        return x, y, z
    x, y, z = sph2cart(azm, π/2 - zen, r)
    return np.c_[x.ravel(), y.ravel(), z.ravel()].squeeze()


def find_quads(zen, azm):
    """
    Finds location in quads (why is it called find_quads?)

    Inputs
    ------
    zen :
    azm :

    Outputs
    -------
    locs :
    """
    loc = None
    try:
        with xr.open_dataset(db_path, group='quads') as quads:
            tmp = np.sqrt((quads.zen[:] - zen)**2 + (quads.azm[:] - azm)**2)
            loc = np.argmin(tmp)
    except:
        pass
    finally:
        return loc

def sw_fresnel():
    """
    Calcualtes Fresnel reflectance for seawater.

    Inputs
    ------
    wv :
         Wavelength (nm)
    ang :
          Reflectance angle
    T :
        Temperature (̊ C)
    S :
        Salinity (PSU)

    Outputs
    -------
    m :
        Refractive index
    ref :
         Fresnel reflectance of seawater
    """
    pass

def index_w(wv, T, S):
    """
    Calculates water refractive index

    Inputs
    -------
    wv :
         Wavelength (nm)
    T :
    Temperature (̊ C)
    S :
        Salinity (PPT)
    """
    pass

def fresnel(m ,ang):
    """
    Calculates Fresnel reflectances.

    Inputs
    ------
    m :
        Refractive index
    ang :
        Reflectance angle

    Outputs
    -------
    R :
        Fresnel reflectance matrix element (1, 1)
    R12 :
          Fresnel reflectance matrix element (1, 2)
    R33 :
          Fresnel reflectance matrix element (3, 3)
    """
    pass

def gen_vec_polar(zen, sun05, num=10):
    """
    Generates vectros for the polar cap, quad, and sun disk.
    By convention, the sun disk is at XZ plane, i.e., azimuth = 0.

    Inputs
    ------
    zen :
         Sun zenith angle

    sun05 :

    num :
          Number of angles to consider
    Outputs
    -------
    vec :
          Polar cap vector
    """
    
    ϕ = np.linspace(0, 2*π, 100)
    sin_sun05 = np.sin(sun05)
    tmp = np.c_[sin_sun05*np.cos(ϕ), sin_sun05 * np.sin(ϕ), np.cos(sun05)*np.ones_like(ϕ)]
    tmp = np.insert(tmp, 0, [0, 0, 1], axis=0)
    ry = np.c_[[np.cos(zen), 0, np.sin(zen)], 
               [0, 1, 0], 
               [-np.sin(zen), 0, np.cos(zen)]]
    vec = tmp @ ry
    return vec    

def prob_reflection(inc, refl, wind):
    """
    Estimates probability of facets reflecting incident ligth into given direction and wind.

    Inputs
    ------
    inc :
          incident light vector
    refl :
            reflected light vector
    wind :
            wind speeds

    Outputs
    -------
    prob :
           Probability
    ang :
            Reflection angle
    """
    pass


def get_sky_run_rho(env, sensor):
    """
    Computes sea surface reflectance of skylight.

    Inputs
    ------

    Outputs
    -------
    ρ :
        Sea surface reflectance of skylight
    """
    # calls:
    #   deg2rad()✅
    #   my_sph2cart()✅
    #   deg2rad()✅
    #   find_quads()
    #   get_prob()
    #   sum()
    #   sw_Fresnel()
    #   squeeze(interpn())
    #   bsxfun()
    #   sum(bsxfun())
    #   squeeze(interpn())
    #   get_vec_polar(deg2rad())
    #   prob_reflection()

   
"""
def load_db(db_path='./db.mat'):
    global db, quads, sdb, vdb
    global skyrad0, sunrad0, rad_boa_sca, rad_boa_vec
    
    db = xr.open_dataset(db_path, group='db')
    quads = xr.open_dataset(db_path, group='quads')
    sdb = xr.open_dataset(db_path, group='sdb')
    vdb = xr.open_dataset(db_path, group='vdb')
    skyrad0 = xr.open_dataset(db_path)['skyrad0']
    sunrad0 = xr.open_dataset(db_path)['sunrad0']
    rad_boa_sca = xr.open_dataset(db_path)['Radiance_BOA_sca']
    rad_boa_vec = xr.open_dataset(db_path)['Radiance_BOA_vec']
"""



def main(args):
    env_vars = ['wind', 'od', 'C', 'zen_sun', 'wtem', 'sal']
    pargs = parse_command_line(args)    
    with open(pargs.env_file_path) as fenv:
        rows = fenv.readlines()
        env = {k:v for k,v in zip(rows[0].strip().split(','),
                                  np.array(rows[1].strip().split(','), 
                                           dtype='f2')
                                  )
               }
    sensor = dict.fromkeys(['ang', 'wv', 'ang2'])
    sensor['ang'] = np.array([40, 45])
    sensor['wv'] = np.arange(350, 1010, 10)
    sensor['ang2'] = sensor['ang'] + np.array([0, 180])
    sensor['pol'] = np.deg2rad(sensor['ang'])
    sensor['vec'] = my_sph2cart(sensor['pol'][1], sensor['pol'][0])
    sensor['loc2'] = find_quads(*sensor['pol2'])
    
    # Probability and reflection angle of reflecting skylight into the sensor
    prob, angr_sky = get_prob(env['wind'], sensor['vec'])
                                
                                
"""
if __name__ == "__main__":
    main(sys.argv[1:])
"""