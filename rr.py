# coding=utf-8
from DataSeries import *
import numpy as np
from utility import power
from Indexes import *

#TODO: passando i parametri data: ref o depp-copy?


class RRmean(TDIndex):
    def __init__(self, data=None):
        super(TDIndex, self).__init__(data)

    # il valore dell'indice se calcolato è in self._value
    def calculate(self):
        self._value = np.mean(self._data)
        return self._value


class HRmean(TDIndex):
    def __init__(self, data=None):
        super(TDIndex, self).__init__(data)

    def calculate(self):
        pass    #TODO: see cache w. and implement
                # è semplicemente 60/RRmean


class RRSTD(TDIndex):
    def __init__(self, data=None):
        super(TDIndex, self).__init__(data)

    def calculate(self):
        self._value = np.std(self._data)
        return self._value


class HRSTD(TDIndex):
    def __init__(self, data=None):
        super(TDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass    #TODO: see cache w. and implement
                #calcolabile da RRSTD


class pNNx(TDIndex):
    def __init__(self, xthreshold, data=None):
        super(TDIndex, self).__init__(data)
        self._xth = xthreshold

    def calculate(self):
        diff = RRDiff.get(self._data)
        self._value = 100.0 * sum(1 for x in diff if x > self._xth) / len(diff)
        return self._value


class NNx(TDIndex):
    def __init__(self, xthreshold, data=None):
        super(TDIndex, self).__init__(data)
        self._xth = xthreshold

    def calculate(self):
        diff = RRDiff.get(self._data)
        self._value = 100.0 * sum(1 for x in diff if x > self._xth)
        return self._value


class RMSSD(TDIndex):
    def __init__(self, data=None):
        super(TDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


class SDSD(TDIndex):
    def __init__(self, data=None):
        super(TDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


class VLF(FDIndex):
    def __init__(self, data=None):
        super(FDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


class LF(FDIndex):
    def __init__(self, data=None):
        super(FDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


# calculate absolute, peak, %1, %2 (4 indexes)
# uses FFTCalc
# should be Cacheable? need its value to calculate other indexes
class HF(FDIndex):
    def __init__(self, data=None):
        super(FDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


# uses FFTCalc
# should be Cacheable? need its value to calculate other indexes
class Total(FDIndex):
    def __init__(self, data=None):
        super(FDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


# uses FFTCalc
# should be Cacheable? need its value to calculate other indexes
class LFHF(FDIndex):
    def __init__(self, data=None):
        super(FDIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


# calculate poincare' index
class PoinIndex(Index):
    def __init__(self, data=None):
        super(PoinIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


class NLIndex(Index):
    def __init__(self, data=None):
        super(NLIndex, self).__init__(data)

    # sovrascrivere il metodo calculate
    def calculate(self):
        pass


class RRAnalysis(DataAnalysis):
    """ Static class containing methods for analyzing RR intervals data. """

    def __init__(self):
        raise NotImplementedError("RRAnalysis is a static class")

    @staticmethod
    def get_example_index(series):
        """ Example index method, returns the length
        :param series: DataSeries object to filter
        :return: DataSeries object filtered
        """
        assert type(series) is DataSeries
        return len(series.get_series)

    @staticmethod
    def TD_indexes(series):
        """ Returns TD indexes """
        RR = series
        RRmean = np.mean(RR)
        RRSTD = np.std(RR)

        RRDiffs = np.diff(RR)

        RRDiffs50 = [x for x in np.abs(RRDiffs) if x > 50]
        pNN50 = 100.0 * len(RRDiffs50) / len(RRDiffs)
        RRDiffs25 = [x for x in np.abs(RRDiffs) if x > 25]
        pNN25 = 100.0 * len(RRDiffs25) / len(RRDiffs)
        RRDiffs10 = [x for x in np.abs(RRDiffs) if x > 10]
        pNN10 = 100.0 * len(RRDiffs10) / len(RRDiffs)

        RMSSD = np.sqrt(sum(RRDiffs ** 2) / (len(RRDiffs) - 1))
        SDSD = np.std(RRDiffs)

        labels = np.array(['RRmean', 'RRSTD', 'pNN50', 'pNN25', 'pNN10', 'RMSSD', 'SDSD'], dtype='S10')

        return [RRmean, RRSTD, pNN50, pNN25, pNN10, RMSSD, SDSD], labels

    @staticmethod
    def poin_indexes(series):
        """ Returns Poincare' indexes """
        RR = series
        # calculates Poincare' indexes
        xdata, ydata = RR[:-1], RR[1:]
        sd1 = np.std((xdata - ydata) / np.sqrt(2.0), ddof=1)
        sd2 = np.std((xdata + ydata) / np.sqrt(2.0), ddof=1)
        sd12 = sd1 / sd2
        sEll = sd1 * sd2 * np.pi
        labels = ['sd1', 'sd2', 'sd12', 'sEll']

        return [sd1, sd2, sd12, sEll], labels

    @staticmethod
    def FD_indexes(series, Finterp):


        # freqs=np.arange(0, 2, 0.0001)
        #
        # # calculates AR coefficients
        # AR, P, k = spct.arburg(RR_interp*1000, 16) #burg
        #
        # # estimates PSD from AR coefficients
        # spec = spct.arma2psd(AR, T=0.25, NFFT=2*len(freqs))
        freqs, spec = FFTCalc.get(series, Finterp, use_cache=True)

        # calculates power in different bands
        VLF = power(spec, freqs, 0, 0.04)
        LF = power(spec, freqs, 0.04, 0.15)
        HF = power(spec, freqs, 0.15, 0.4)
        Total = power(spec, freqs, 0, 2)
        LFHF = LF / HF
        nVLF = VLF / Total
        nLF = LF / Total
        nHF = HF / Total

        LFn = LF / (HF + LF)
        HFn = HF / (HF + LF)
        Power = [VLF, HF, LF]

        Power_Ratio = Power / sum(Power)
        # Power_Ratio=spec/sum(spec) # uncomment to calculate Spectral Entropy using all frequencies
        Spectral_Entropy = 0
        lenPower = 0 # tengo conto delle bande che ho utilizzato
        for i in xrange(0, len(Power_Ratio)):
            if Power_Ratio[i] > 0: # potrei avere VLF=0
                Spectral_Entropy += Power_Ratio[i] * np.log(Power_Ratio[i])
                lenPower += 1
        Spectral_Entropy /= np.log(lenPower) #al posto di len(Power_Ratio) perche' magari non ho usato VLF

        labels = np.array(['VLF', 'LF', 'HF', 'Total', 'nVLF', 'nLF', 'nHF', 'LFn', 'HFn', 'LFHF', 'SpecEn'],
                          dtype='S10')

        return [VLF, LF, HF, Total, nVLF, nLF, nHF, LFn, HFn, LFHF, Spectral_Entropy], labels


class RRFilters(DataAnalysis):
    """ Static class containing methods for filtering RR intervals data. """

    def __init__(self):
        raise NotImplementedError("RRFilters is a static class")

    @staticmethod
    def example_filter(series):
        """ Example filter method, does nothing
        :param series: DataSeries object to filter
        :return: DataSeries object filtered
        """
        assert type(series) is DataSeries
        return series

        # TODO: add analysis scripts like in the example

