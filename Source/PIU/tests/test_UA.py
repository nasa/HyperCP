import unittest
import numpy as np

from Source.PIU.Uncertainty_Analysis import Propagate


prop = Propagate(M = 100, cores=0)  

# chosen values 16:32 from PySAS sample data - first ensemble, first scan after glitter removal
lt_light = np.array([
    6620.65588235,  6959.4800885 ,  7372.58955882,  7766.46676471,
    8142.29233038,  8520.48823529,  8761.43539823,  9249.94441176,
    10191.20661765, 11352.82426471, 12516.77522124, 13695.03617647,
    14834.61176471, 15742.12794118, 16324.26150442, 16703.12323529,
])
lt_dark = np.array([
    1325.67511675, 1319.2559224 , 1323.94060333, 1323.11565996,
    1317.83253221, 1323.76035975, 1324.39373889, 1324.14863499,
    1321.9420173, 1325.03803638, 1326.51687389, 1326.20325815,
    1326.4754258, 1327.6332966, 1326.33206155, 1325.91130646,
])
lt_cal = np.array([
    1.61522941e-04, 1.58498230e-04, 1.53301471e-04, 1.46732059e-04,
    1.40358702e-04, 1.33141176e-04, 1.25269027e-04, 1.17996176e-04,
    1.11427647e-04, 1.05801471e-04, 1.01249469e-04, 9.77675294e-05,
    9.53468235e-05, 9.40965882e-05, 9.36044248e-05, 9.38898235e-05,
])
rho = np.array([
    0.0277, 0.0277, 0.0277, 0.0277, 
    0.0277, 0.0277, 0.0277, 0.0277,
    0.0277, 0.0277, 0.0277, 0.0277,
    0.0277, 0.0277, 0.0277, 0.0277,
])
li_light = np.array([
    39983.31936947, 41448.93148976, 42681.93131442, 43644.6412309,
    44319.26753673, 44219.77274145, 44557.55951793, 47126.77643206,
    50721.19295145, 53664.04665766, 56037.06705479, 57899.34135208,
    58658.38559102, 57988.78885539, 56446.4236795 , 54774.97044911,
])
li_dark = np.array([
    3937.13742596, 3945.86717543, 3948.69369052, 3947.83475159,
    3946.86685603, 3945.42307123, 3943.10739388, 3938.84798693,
    3943.09281009, 3951.3637574 , 3944.80427067, 3939.32371756,
    3941.49348763, 3953.23270544, 3959.09875018, 3955.68379366,
])
li_cal = np.array([
    1.60693731e-04, 1.54430655e-04, 1.47220299e-04, 1.39550000e-04,
    1.31928060e-04, 1.24348810e-04, 1.17415224e-04, 1.11466667e-04,
    1.06550000e-04, 1.02660000e-04, 9.97705357e-05, 9.83282985e-05,
    9.78740476e-05, 9.82400000e-05, 9.94832239e-05, 1.01331250e-04  
])
es_light = np.array([
    242603.22162162, 264622.24191617, 289980.86227545, 313228.88648649,
    333216.80479042, 349546.28948949, 355388.41197605, 365727.57365269,
    392919.2       , 425053.94251497, 449203.61916168, 469320.97724551,
    487245.65988024, 495126.97964072, 493367.98802395, 485334.28228228
])
es_dark = np.array([
    8024.74991201, 8123.3257612 , 8035.13095279, 8029.606975,
    8032.20908667, 8017.36382029, 8049.58832216, 7992.18768003,
    8044.46455758, 8039.89268465, 8061.29219215, 8041.77414884,
    8053.23282468, 8046.98334147, 8070.55993325, 8127.85665621
])
es_cal = np.array([
    0.00035851, 0.0003366 , 0.000315  , 0.0002939 , 
    0.00027485,0.0002585 , 0.00024496, 0.0002348 , 
    0.0002283 , 0.00022288,0.00022091, 0.00022001, 
    0.00022136, 0.00022419, 0.00022905,0.00023428
])


class test_measurement_functions(unittest.TestCase):

    def test_instruments(self):
        ones = np.ones(len(es_light))
        means = [
            es_light, es_dark,
            li_light, li_dark,
            lt_light, lt_dark,
            es_cal, li_cal, lt_cal,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
        ]

        prop.instruments(*means)
        es = np.array((es_light - es_dark) * es_cal)
        li = np.array((li_light - li_dark) * li_cal)
        lt = np.array((lt_light - lt_dark) * lt_cal)

        es_test = np.array(
            [
                84.41138226,  86.84992132,  89.36720734,  90.1569442 ,
                89.85119169,  88.76023236,  85.43762422,  84.39503954,
                88.35307495,  93.48276454,  97.99107072, 102.07136407,
                106.64692125, 109.78039441, 111.78091107, 112.39032747,
            ]
        )
        li_test = np.array(
            [
                5.76253522, 5.78849375, 5.69045965, 5.52085496, 
                5.32943694,4.98122587, 4.70105875, 4.77902392, 
                4.98022493, 5.08650212,5.17472448, 5.29911457, 
                5.35044231, 5.29401402, 5.20207752,5.13632976
            ]
        )
        lt_test = np.array(
            [
                0.85480109, 0.89403332, 0.92822867, 0.94590248, 
                0.95758379, 0.960193  , 0.92948299, 0.92878907, 
                0.98516964, 1.06081286, 1.1319507 , 1.20809775, 
                1.28875213, 1.35998437, 1.40483227, 1.4436626
            ]
        )
        for i in range(len(es_light)):
            self.assertAlmostEqual(es[i], es_test[i], delta=1)
            self.assertAlmostEqual(li[i], li_test[i], delta=0.1)
            self.assertAlmostEqual(lt[i], lt_test[i], delta=0.1)

    def test_rrs_hyper(self):
        ones = np.ones(len(es_light))
        means = [
            lt_light, lt_dark,
            rho,
            li_light, li_dark,
            es_light, es_dark,
            es_cal, li_cal, lt_cal,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
        ]

        rrs = prop.RRS(*means)
        rrs_test = np.array(
            [
                0.00825507, 0.00848941, 0.00865582, 0.00882336,
                0.00906053, 0.00927642, 0.00939125, 0.00954061,
                0.0096705, 0.0098884, 0.0101438 , 0.01046205,
                0.01073842, 0.01106971, 0.01132391, 0.01163325,
            ]
        )
        for i in range(len(es_light)):
            self.assertAlmostEqual(rrs[i], rrs_test[i], delta=1e-3)

    def test_lw_hyper(self):
        ones = np.ones(len(lt_light))
        means = [
            lt_light, lt_dark,
            rho,
            li_light, li_dark,
            li_cal, lt_cal,
            ones, ones,
            ones, ones,
            ones, ones,
            ones, ones,
            ones, ones,
        ]

        lw = prop.Lw(*means)
        lw_test = np.array(
            [
                0.69423227, 0.73295843, 0.76874232, 0.79144281, 0.8098025 ,
                0.81895654, 0.79905958, 0.801384  , 0.84972034, 0.91907712,
                0.98852353, 1.06176909, 1.13907878, 1.20877977, 1.25871185,
                1.30060534
            ]
        )
        for i in range(len(lt_light)):
            self.assertAlmostEqual(lw[i], lw_test[i], delta=1e-3)

    def test_l2_uncs(self):
        ones = np.ones(len(es_light))
        means_lw = [
            lt_light, lt_dark,
            rho,
            li_light, li_dark,
            li_cal, lt_cal,
            ones, ones,
            ones, ones,
            ones, ones,
            ones, ones,
            ones, ones,
        ]
        uncs_lw = [
            ones*0.01, lt_dark*0.001,
            rho*0.003,
            li_light*0.01, li_dark*0.001,
            li_cal*0.018, lt_cal*0.02,
            ones*0.01, ones*0.01,
            ones*0.02, ones*0.02,
            ones*0.03, ones*0.03,
            ones*0.01, ones*0.01,
            ones*0.024, ones*0.024,
        ]
        means_rrs = [
            lt_light, lt_dark,
            rho,
            li_light, li_dark,
            es_light, es_dark,
            es_cal, li_cal, lt_cal,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
            ones, ones, ones,
        ]
        uncs_rrs = [
            ones*0.01, lt_dark*0.001,
            rho*0.003,
            li_light*0.01, li_dark*0.001,
            es_light*0.01, es_dark*0.001,
            es_cal*0.018, li_cal*0.02, lt_cal*0.02,
            ones*0.01, ones*0.01, ones*0.01,
            ones*0.02, ones*0.02, ones*0.02,
            ones*0.03, ones*0.03, ones*0.03,
            ones*0.01, ones*0.01, ones*0.01,
            ones*0.024, ones*0.024, ones*0.024,
        ]

        lw  = prop.Lw(*means_lw)
        rrs = prop.RRS(*means_rrs)

        lwAbsUnc = prop.Propagate_Lw_HYPER(means_lw, uncs_lw)
        rrsAbsUnc = prop.Propagate_RRS_HYPER(means_rrs, uncs_rrs)
        lwRelUnc = (lwAbsUnc / lw)*100
        rrsRelUnc = (rrsAbsUnc / rrs)*100
        
        from Source.PIU.Breakdown_CB import PlotMaths

        BD_UNCS , _ = PlotMaths.classBasedL2(prop, means_lw, means_rrs, uncs_lw, uncs_rrs, cul=False)
        validation = {}
        for k, signal in zip(BD_UNCS.keys(), [lw, rrs]):  # for ['lw' 'rrs']
            validation[k] = np.sqrt(
                sum([v**2 for v in BD_UNCS[k].values()])  # add in quad
            ) / signal
        for i in range(len(es_light)):
            self.assertAlmostEqual(validation['Lw'][i], lwRelUnc[i], delta=1e-2)
            self.assertAlmostEqual(validation['Rrs'][i], rrsRelUnc[i], delta=1e-2)


if __name__ == '__main__':
    unittest.main()
