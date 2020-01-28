import numpy as np
import time

π = np.pi
length = 92476
zen = np.random.rand(1,length)
du = np.array(0.00731553)
azm = np.random.rand(1,length)
dphi = np.array(0.00930842)
num = 10 

prob = np.empty(length)*np.nan
ang = prob.copy()

sensor = np.random.rand(3)
wind = 10

def my_sph2cart(azm, zen, r=1):    
    def sph2cart(azm, elev, r):
        cos_elev = np.cos(elev)
        x = r * cos_elev * np.cos(azm)
        y = r * cos_elev * np.sin(azm)
        z = r * np.sin(elev)
        return x, y, z

    x, y, z = sph2cart(azm, π/2 - zen, r)
    return np.c_[x.ravel(), y.ravel(), z.ravel()].squeeze()

def my_cart2sph(n):
    def cart2sph(x,y,z):
        azimuth = np.arctan2(y,x)
        elevation = np.arctan2(z,np.sqrt(x**2 + y**2))
        r = np.sqrt(x**2 + y**2 + z**2)
        return azimuth, elevation, r

    azm,zen,r = cart2sph(n[:,0],n[:,1],n[:,2])
    zen = π/2 - zen
    return azm, zen, r

def gen_vec(zens,azms):
        zens,azms = np.meshgrid(zens,azms)
        zens = zens[:]
        azms = azms[:]
        vec = my_sph2cart(azms,zens,1)
        return vec

def gen_vec_quad(zen,du,azm,dphi,num):
    half_azm = np.linspace(-dphi/2,dphi/2,num)
    half_zen = np.linspace(-du/2/np.sin(zen), du/2/np.sin(zen),num)
    vec = gen_vec(zen+half_zen, azm+half_azm)
    return vec

def prob_reflection(inc, refl, wind):    
    def vec_length(a):
        al = np.sum(abs(a)**2, 1)**0.5
        return al
    def cox_munk(wind):
        sigma = np.sqrt(0.003+0.00512*wind)
        return sigma
    def rayleighcdf(x,s):
        t = (x/s)**2
        y = 1-np.exp(-t/2)
        return y
    
    n = refl - inc
    vLen = vec_length(n).reshape(vec_length(n)[:].shape[0],1)
    n = n/vLen
    azm_n,zen_n,_ = my_cart2sph(n)
    slope = np.tan(zen_n)
    sigma = cox_munk(wind)
    sigma = sigma/np.sqrt(2)
    p1 = rayleighcdf(max(slope),sigma)-rayleighcdf(min(slope),sigma)
    azm_nx = max(azm_n)
    azm_nn = min(azm_n)

    if azm_nx*azm_nn >0: # not an issue
        p2 = (azm_nx-azm_nn)/2/π
    elif any(abs(azm_n)<π/2): # cases 1 and 3 
        p2 = (azm_nx-azm_nn)/2/π
    else: # case 2
        ind = azm_n<0
        azm_n[ind] = azm_n[ind]+2*π
        azm_nx = max(azm_n)
        azm_nn = min(azm_n)
        p2 = (azm_nx-azm_nn)/2/π

    prob = 2*p1*p2 # factor 2 accounts for 180 degree ambiguity    
    cosw = np.sum(n*refl,1)
    ang = np.arccos(cosw)
    ind = ang>π/2
    ang[ind] = π - ang[ind]
    ang = np.mean(ang)

    return prob, ang



t0 = time.time()
''' standard loop. 100%+ CPU, low RAM.
Takes ages. 46 sec, which is actually significantly less than get_sky_sun_rho @268 sec.'''
# for i in np.arange(1, prob.size):        
#     sky = gen_vec_quad(zen[0][i],du,azm[0][i],dphi,num)
#     prob[i],ang[i] = prob_reflection(-sky,sensor,wind)

''' vectorized solution for sky. Unable to allocate an array this large 924760x924760'''
# sky = gen_vec_quad(zen[0],du,azm[0],dphi,num)

''' comprehension. CPU 100%+. After lengthy delay -> Exception: Too many values to unpack'''    
# prob, ang = [(prob_reflection(
#                 -gen_vec_quad(zen[0][i],
#                 du,azm[0][i],
#                 dphi,num),sensor,wind)) for i in np.arange(1, prob.size)]

''' mapped, nested lambdas. Returns a map? Not callable'''
# sky = map(lambda zen : map(lambda azm : gen_vec_quad(zen,du,azm,dphi,num), 
#         azm[0]), 
#         zen[0])

''' lambda sky plus loop. Takes same time as loop. 100%+ CPU, low RAM'''
sky = lambda x, y: gen_vec_quad(x,du,y,dphi,num)
for i in np.arange(1, prob.size):
    prob[i],ang[i] = prob_reflection(-sky(zen[0][i], azm[0][i]),sensor,wind)

# '''nested lambdas. Unable to allocate an array with shape 924760x924760 '''
# probref = lambda x, y, z: prob_reflection(-x, y, z)
# prob, ang = probref(-sky(zen[0], azm[0]), sensor, wind)
t1 = time.time()
print(f'Time elapsed: {t1-t0}')