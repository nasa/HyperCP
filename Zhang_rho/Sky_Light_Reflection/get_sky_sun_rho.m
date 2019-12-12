function rho = get_sky_sun_rho(env, sensor)
persistent db quads skyrad0 sunrad0 sdb vdb Radiance_BOA_sca Radiance_BOA_vec
if isempty(db) || isempty(quads) || isempty(skyrad0) || isempty(sunrad0) || ...
        isempty(sdb) || isempty(vdb) || isempty(Radiance_BOA_sca) || ...
        isempty(Radiance_BOA_vec)
    load('db.mat');
end
tmp = [1:size(skyrad0,3)];

sensor.pol = deg2rad(sensor.ang); % the sensor polar coordinate
sensor.vec = my_sph2cart(sensor.pol(2),sensor.pol(1),1); % sensor vector
sensor.pol2 = deg2rad(sensor.ang2); % the skylight polar coordinate
sensor.loc2 = find_quads(quads,sensor.pol2(1),sensor.pol2(2));

% Probability and reflection angle of reflecting skylight into the sensor
[prob,angr_sky] = get_prob(env.wind,sensor.vec,quads);
tprob = sum(prob,1);
ref = sw_Fresnel(sensor.wv,angr_sky,env.wtem,env.sal);

skyrad=squeeze(interpn(db.zen_sun,db.od,tmp,db.wv,skyrad0,...
    env.zen_sun,env.od,tmp,sensor.wv));
N0 = skyrad(sensor.loc2,:);
N = bsxfun(@rdivide,skyrad,N0);
rho.sky = sum(bsxfun(@times,ref.*N,prob/tprob),1);

sunrad=squeeze(interpn(db.zen_sun,db.od,db.wv,sunrad0,...
    env.zen_sun,env.od,sensor.wv))'; % make it a row vector
sun_vec=gen_vec_polar(deg2rad(env.zen_sun),quads.sun05);
[prob_sun,angr_sun]=prob_reflection(-sun_vec,sensor.vec,env.wind);
ref_sun = sw_Fresnel(sensor.wv,angr_sun,env.wtem,env.sal);
rho.sun=(sunrad./N0).*(ref_sun*prob_sun/tprob);

rad_inc_sca = squeeze(interpn(...
    sdb.wind,sdb.od(:,10),sdb.zen_sun,sdb.wv,sdb.zen_view,sdb.azm_view, ...
    Radiance_BOA_sca, ...
    env.wind,env.od,env.zen_sun,sensor.wv,180-sensor.ang(1),180-sensor.ang(2)));
rad_mea_sca = squeeze(interpn(...
    sdb.wind,sdb.od(:,10),sdb.zen_sun,sdb.wv,sdb.zen_view,sdb.azm_view, ...
    Radiance_BOA_sca, ...
    env.wind,env.od,env.zen_sun,sensor.wv,sensor.ang(1),180-sensor.ang(2)));
rho_sca = rad_mea_sca./rad_inc_sca;

rad_inc_vec = squeeze(interpn(...
    vdb.wind,vdb.od(:,10),vdb.zen_sun,vdb.wv,vdb.zen_view,vdb.azm_view, ...
    Radiance_BOA_vec, ...
    env.wind,env.od,env.zen_sun,sensor.wv,180-sensor.ang(1),180-sensor.ang(2)));
rad_mea_vec = squeeze(interpn(...
    vdb.wind,vdb.od(:,10),vdb.zen_sun,vdb.wv,vdb.zen_view,vdb.azm_view, ...
    Radiance_BOA_vec, ...
    env.wind,env.od,env.zen_sun,sensor.wv,sensor.ang(1),180-sensor.ang(2)));
rho_vec = rad_mea_vec./rad_inc_vec;
rho.sca2vec = rho_vec./rho_sca;
rho.sca2vec = (rho.sca2vec(:))';
rho.rho = rho.sky.*rho.sca2vec + rho.sun;
end