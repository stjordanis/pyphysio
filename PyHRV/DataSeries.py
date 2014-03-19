# coding=utf-8
# Classes for cached data elaborations
#

import numpy as np
from scipy import signal
import pandas as pd
from PyHRV.Indexes.TDIndexes import RRMean
from utility import interpolate_rr
from PyHRV.PyHRVSettings import PyHRVDefaultSettings as Sett


class DataSeries(pd.TimeSeries):
    """ Pandas' DataFrame class. Gives a cache support through CacheableDataCalc subclasses. """

    def __init__(self, data=None, copy=False, metatag=None):
        """ Default constructor.
        @param data: Data to insert in the DataFrame
        @param copy: see Pandas doc
        """
        super(DataSeries, self).__init__(data=data, copy=copy)
        self._cache = {}
        if metatag is None:
            self.metatag = {}
        else:
            self.metatag = metatag
        mean = RRMean(self).value
        assert (not Sett.TimeUnitCheck.time_unit_check_ibi_mean_max < Sett.TimeUnitCheck.time_unit_check_ibi
                | mean < Sett.TimeUnitCheck.time_unit_check_ibi_mean_min),\
            Sett.TimeUnitCheck.time_unit_check_ibi_warn % mean

    def cache_clear(self):
        """ Clears the cache and frees memory (GC?)
        """
        self._cache = {}

    def cache_check(self, calculator):
        """ Check if the cache contains valid calculator's data
        :type calculator: CacheableDataCalc
        :param calculator: CacheableDataCalc
        :return: If the cache is valid
        """
        return calculator.cid() in self._cache

    def cache_invalidate(self, calculator):
        """
        :type calculator: CacheableDataCalc
        :param calculator: CacheableDataCalc
        """
        if self.cache_check(calculator):
            del self._cache[calculator.cid()]

    def cache_pre_calc_data(self, calculator, params):
        """ Precalculates data and caches it
        :type calculator: CacheableDataCalc
        :param calculator: CacheableDataCalc
        """
        self._cache[calculator.cid()] = calculator.get(self, params, use_cache=False)
        return self._cache[calculator.cid()]

    def cache_get_data(self, calculator):
        """ Gets data from the cache if valid
        :type calculator: CacheableDataCalc
        :param calculator: CacheableDataCalc subclass
        :return: The data or None
        """
        if self.cache_check(calculator):
            return self._cache[calculator.cid()]
        else:
            return None


class CacheableDataCalc(object):
    """ Static class that calculates cacheable data (like FFT etc.) """

    def __init__(self):
        pass

    @classmethod
    def get(cls, data, params=None, use_cache=True):
        if use_cache and isinstance(data, DataSeries):
            if not data.cache_check(cls):
                data.cache_pre_calc_data(cls, params)
        else:
            return cls._calculate_data(data, params)
        return data.cache_get_data(cls)

    @classmethod
    def _calculate_data(cls, data, params):
        raise NotImplementedError("Only on " + cls.__name__ + " sub-classes")

    @classmethod
    def cid(cls):
        """ Gets an identifier for the class
        :rtype : str
        """
        return cls.__name__ + "_cn"


class FFTCalc(CacheableDataCalc):
    @classmethod
    def _calculate_data(cls, data, params=None):
        """ Calculates the intermediate data
        :type data: DataSeries
        :param data: RRSeries object
        :param params: Params object
        :return: Data to cache
        """
        # calcolo FFT
        rr_interp, bt_interp = interpolate_rr(data.series, params)
        interp_freq = params
        hw = np.hamming(len(rr_interp))

        frame = rr_interp * hw
        frame = frame - np.mean(frame)

        spec_tmp = np.absolute(np.fft.fft(frame)) ** 2  # calcolo FFT
        powers = spec_tmp[0:(np.ceil(len(spec_tmp) / 2))]  # Only positive half of spectrum
        bands = np.linspace(start=0, stop=interp_freq / 2, num=len(powers), endpoint=True)  # vettore delle frequenze
        return bands, powers


class PSDWelchCalc(CacheableDataCalc):
    @classmethod
    def _calculate_data(cls, data, to_freq):
        """ Calculates the intermediate data
        :type data: DataSeries
        :param data: RRSeries object
        :param to_freq: Sampling frequency
        :return: Data to cache
        """
        if to_freq is None:
            to_freq = Sett.interpolation_freq_default
        rr_interp, bt_interp = interpolate_rr(data, to_freq)
        freqs, spect = signal.welch(rr_interp, to_freq)
        spect = np.sqrt(spect)
        return freqs, spect / np.max(spect), sum(spect) / len(spect)


class RRDiff(CacheableDataCalc):
    @classmethod
    def _calculate_data(cls, data, params=None):
        """ Calculates the intermediate data
        :type data: DataSeries
        :param data: RRSeries object
        :param params: Params object
        :return: Data to cache
        """
        return np.diff(np.array(data))
