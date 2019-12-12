%%
% Example on how to use get_sky_run_rho.m to compute the rho for skylight
% reflection.
%
% Zhang, X., S. He, A. Shabani, P.-W. Zhai, and K. Du. 2017. Spectral sea
% surface reflectance of skylight. Opt. Express 25: A1-A13,
% doi:10.1364/OE.25.0000A1.
%
clear variables

% === environmental conditions during experiment ===
env.wind = 10; % wind speeds in m/s
env.od = 0.1; % aersosol optical depth at 550 nm
env.C = 0; % cloud cover. 
env.zen_sun = 30; % sun zenith angle
env.wtem = 25; % water temperature (Deg C)
env.sal = 34; % salinity PSU

% === The sensor ===
% the zenith and azimuth angles of light that the sensor will see
% 0 azimuth angle is where the sun located
% positive z is upward
sensor.ang = [40, 45]; % zenith and azimuth angle in degree
sensor.wv = [350:10:1000]; % wavelength in nm
sensor.ang2 = sensor.ang + [0, 180]; % location where skylight is measured

rho = get_sky_sun_rho(env, sensor);
plot(sensor.wv,rho.rho);
xlabel('wavelength (nm)');
ylabel('\rho');
