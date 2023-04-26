"""
Functions to read spectral response function data with pyspectral
"""

import numpy as np
from pyspectral.rsr_reader import RelativeSpectralResponse
from typing import Union, List, Tuple, Iterator, Optional


"""___Authorship___"""
__author__ = "Sam Hunt"
__created__ = "5/11/2020"


def return_band_names(
        platform_name: str,
        sensor_name: str,
        band_names: Optional[List[str]] = None,
        min_wl: Optional[float] = None,
        max_wl: Optional[float] = None
) -> List[str]:
    """
    Returns band names for specified sensor from `pyspectral <https://pyspectral.readthedocs.io/en/master/installation.html#static-data>`_ library.

    :param platform_name: satellite name
    :param sensor_name: name of instrument on satellite
    :param band_names: (optional) if omitted all sensor band names are returned, otherwise submitted band names validated and returned
    :param min_wl: minimum wavelength to include in range
    :param max_wl: maximum wavelength to include in range

    :return: band names
    """

    srf_util = SensorSRFUtil(platform_name, sensor_name)
    return srf_util.return_band_names(band_names=band_names, min_wl=min_wl, max_wl=max_wl)


def return_band_centres(
        platform_name: str,
        sensor_name: str,
        band_names: Optional[List[str]] = None,
        detector_name: Optional[str] = None,
        min_wl: Optional[float] = None,
        max_wl: Optional[float] = None
) -> np.ndarray:
    """
    Returns band centres for specified sensor from `pyspectral <https://pyspectral.readthedocs.io/en/master/installation.html#static-data>`_ library.

    :param platform_name: satellite name
    :param sensor_name: name of instrument on satellite
    :param band_names: name of bands to return band centres of, if omitted all band returned
    :param detector_name: name of sensor detector. Can be used in sensor has SRF data for for different
    detectors separately - if not specified in this case different
    :param min_wl: minimum wavelength to include in range
    :param max_wl: maximum wavelength to include in range

    :return: band centres in nm
    """

    srf_util = SensorSRFUtil(platform_name, sensor_name, detector_name, band_names=band_names)
    return srf_util.return_band_centres(min_wl=min_wl, max_wl=max_wl)


def return_srf(
        platform_name: str,
        sensor_name: str,
        band_name: str = None,
        detector_name: Union[None, str] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """

    Returns srf data for named band of for specified sensor from `pyspectral <https://pyspectral.readthedocs.io/en/master/installation.html#static-data>`_ library.

    :param platform_name: satellite name
    :param sensor_name: name of instrument on satellite
    :param band_name: name of sensor band
    :param detector_name: (optional) name of sensor detector. Can be used in sensor has SRF data for for different
    detectors separately - if not specified in this case different

    :return: band srf
    :return: band srf wavelength coordinates
    """

    srf_util = SensorSRFUtil(platform_name, sensor_name, detector_name)
    return srf_util.return_srf(band_name)


def return_iter_srf(
        platform_name: str,
        sensor_name: str,
        band_names: Optional[List[str]] = None,
        detector_name: Optional[str] = None,
) -> Iterator:
    """
    Returns iterable of band srfs for specified sensor from `pyspectral <https://pyspectral.readthedocs.io/en/master/installation.html#static-data>`_ library.

    :param platform_name: satellite name
    :param sensor_name: name of instrument on satellite
    :param band_names: name of bands to iterate through, if omitted all bands included
    :param detector_name: name of sensor detector. Can be used in sensor has SRF data for for different
    detectors separately - if not specified in this case different

    :return: iterable that returns band srf and srf wavelength coordinates at each iteration
    """

    srf_util = SensorSRFUtil(platform_name, sensor_name, detector_name, band_names=band_names)
    return iter(srf_util)


class SensorSRFUtil:
    """
    Helper class to define repeating functions along a coordinate axis

    from `pyspectral <https://pyspectral.readthedocs.io/en/master/installation.html#static-data>`_ library.

    :param platform_name: satellite name
    :param sensor_name: name of instrument on satellite
    :param detector_name: (optional) name of sensor detector. Can be used in sensor has SRF data for for different
    detectors separately - if not specified in this case different
    :param band_names: (optional) sensor bands to evaluate band integral for, if omitted band integral evaluated for
    all bands within spectral range of datar
    """

    def __init__(
        self,
        platform_name,
        sensor_name,
        detector_name: Union[None, str] = "det-1",
        band_names: Union[None, List[str]] = None
    ):

        # Set attributes from arguments
        self.sensor = RelativeSpectralResponse(platform_name, sensor_name)
        self.detector_name = "det-1" if detector_name is None else detector_name

        # Unpack and validate selected bands
        self.band_names = self.return_band_names(band_names)
        self.band_centres = self.return_band_centres()

    def return_band_names(
            self,
            band_names: Optional[str] = None,
            min_wl: Optional[float] = None,
            max_wl: Optional[float] = None
    ) -> List[str]:
        """
        Returns band names for specified sensor bands

        :param band_names: if omitted all sensor band names are returned,
         otherwise submitted band names validated and returned
        :param min_wl: minimum wavelength to include in range
        :param max_wl: maximum wavelength to include in range

        :return: band names
        """

        sensor_band_names = self.return_sensor_band_names()
        sensor_band_centres = self.return_band_centres()

        selected_band_centres = self.return_band_centres(min_wl=min_wl, max_wl=max_wl)

        selected_band_names = [b for b, c in zip(sensor_band_names, sensor_band_centres) if c in selected_band_centres]

        if band_names is None:
            band_names = selected_band_names
        else:
            if not set(band_names).issubset(set(selected_band_names)):
                raise ValueError("band names must be one of - " + str(selected_band_names))
            band_names = band_names

        return band_names

    def return_band_centres(
            self,
            min_wl: Optional[float] = None,
            max_wl: Optional[float] = None
    ) -> np.ndarray:
        """
        Returns band centres for specified sensor bands

        :param min_wl: minimum wavelength to include in range
        :param max_wl: maximum wavelength to include in range

        :return: band centres in nm
        """

        band_names = self.return_sensor_band_names()

        band_centres = [
            self.sensor.rsr[band_name][self.detector_name]["central_wavelength"] * self.sensor.si_scale / 1e-9
            for band_name in band_names
        ]

        if min_wl is not None:
            band_centres = [b for b in band_centres if (b > min_wl)]

        if max_wl is not None:
            band_centres = [b for b in band_centres if (b < max_wl)]

        band_centres = np.array(band_centres)

        return band_centres

    def return_sensor_band_names(self) -> List[str]:
        """
        Returns list of all sensor band names

        :return: sensor band names
        """

        return list(self.sensor.rsr.keys())

    def return_srf(self, band_name: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns srf data for specified sensor band

        :param band_name: sensor band name

        :return: band srf
        :return: band srf wavelength coordinates
        """

        srf = self.sensor.rsr[band_name][self.detector_name]["response"]  # gets rsr for given band
        wl_srf = 1000 * self.sensor.rsr[band_name][self.detector_name]["wavelength"]
        return srf, wl_srf

    def __iter__(self):

        # Define counter
        self.i = 0
        return self

    def __next__(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns ith function

        :return: band srf
        :return: band srf wavelength coordinates
        """

        # Iterate through bands
        if self.i < len(self.band_names):

            # Update counter
            self.i += 1

            return self.return_srf(self.band_names[self.i-1])

        else:
            raise StopIteration


if __name__ == "__main__":
    pass
