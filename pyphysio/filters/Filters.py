# coding=utf-8
from __future__ import division
import numpy as _np
from scipy.signal import gaussian as _gaussian, filtfilt as _filtfilt, filter_design as _filter_design, \
    deconvolve as _deconvolve
from matplotlib.pyplot import plot as _plot
from ..BaseFilter import Filter as _Filter
from ..Signal import EvenlySignal as _EvenlySignal, UnevenlySignal as _UnevenlySignal
from ..Utility import abstractmethod as _abstract

__author__ = 'AleB'


class Normalize(_Filter):
    """
    Normalized the input signal using the general formula: ( signal - BIAS ) / RANGE

    Parameters
    -------------------
    norm_method : 
        Method for the normalization. Available methods are:
    * 'mean' - remove the mean [ BIAS = mean(signal); RANGE = 1 ]
    * 'standard' - standardization [ BIAS = mean(signal); RANGE = std(signal) ]
    * 'min' - remove the minimum [ BIAS = min(signal); RANGE = 1 ]
    * 'maxmin' - maxmin normalization [ BIAS = min(signal); RANGE = ( max(signal) - min(signal ) ]
    * 'custom' - custom, bias and range are manually defined [ BIAS = bias, RANGE = range ]
    
    norm_bias : float, default = 0
        Bias for custom normalization
    norm_range : float, !=0, default = 1
        Range for custom normalization

    Returns
    -------
    signal: 
        The normalized signal. 

    """

    def __init__(self, norm_method='standard', norm_bias=0, norm_range=1):
        assert norm_method in ['mean', 'standard', 'min', 'maxmin', 'custom'],\
            "norm_method must be one of 'mean', 'standard', 'min', 'maxmin', 'custom'"
        if norm_method == "custom":
            assert norm_range != 0, "norm_range must not be zero"
        _Filter.__init__(self, norm_method=norm_method, norm_bias=norm_bias, norm_range=norm_range)

    @classmethod
    def algorithm(cls, signal, params):
        from ..indicators.TimeDomain import Mean as _Mean, StDev as _StDev

        method = params['norm_method']
        if method == "mean":
            return signal - _Mean()(signal)
        elif method == "standard":
            return (signal - _Mean()(signal)) / _StDev()(signal)
        elif method == "min":
            return signal - _np.min(signal)
        elif method == "maxmin":
            return (signal - _np.min(signal)) / (_np.max(signal) - _np.min(signal))
        elif method == "custom":
            return (signal - params['norm_bias']) / params['norm_range']


class Diff(_Filter):
    """
    Computes the differences between adjacent samples.

    Optional parameters
    -------------------
    degree : int, >0, default = 1
        Sample interval to compute the differences
    
    Returns
    -------
    signal : 
        Differences signal. 

    """

    def __init__(self, degree=1):
        assert degree > 0, "The degree value should be positive"
        _Filter.__init__(self, degree=degree)

    @classmethod
    def algorithm(cls, signal, params):
        """
        Calculates the differences between consecutive values
        """
        degree = params['degree']

        sig_1 = signal[:-degree]
        sig_2 = signal[degree:]

        out = _EvenlySignal(values=sig_2 - sig_1,
                            sampling_freq=signal.get_sampling_freq(),
                            signal_nature=signal.get_signal_nature(),
                            start_time=signal.get_start_time() + degree / signal.get_sampling_freq())

        return out


class IIRFilter(_Filter):
    """
    Filter the input signal using an Infinite Impulse Response filter.

    Parameters
    ----------
    fp : list or float
        The pass frequencies
    fs : list or float
        The stop frequencies
    
    Optional parameters
    -------------------
    loss : float, >0, default = 0.1
        Loss tolerance in the pass band
    att : float, >0, default = 40
        Minimum attenuation required in the stop band.
    ftype : str, default = 'butter'
        Type of filter. Available types: 'butter', 'cheby1', 'cheby2', 'ellip', 'bessel'

    Returns
    -------
    signal : EvenlySignal
        Filtered signal

    Notes
    -----
    This is a wrapper of *scipy.signal.filter_design.iirdesign*. Refer to `scipy.signal.filter_design.iirdesign`
    for additional information
    """

    def __init__(self, fp, fs, loss=.1, att=40, ftype='butter'):
        assert loss > 0, "Loss value should be positive"
        assert att > 0, "Attenuation value should be positive"
        assert att > loss, "Attenuation value should be greater than loss value"
        assert ftype in ['butter', 'cheby1', 'cheby2', 'ellip', 'bessel'],\
            "Filter type must be in ['butter', 'cheby1', 'cheby2', 'ellip', 'bessel']"
        _Filter.__init__(self, fp=fp, fs=fs, loss=loss, att=att, ftype=ftype)

    @classmethod
    def algorithm(cls, signal, params):
        fsamp = signal.get_sampling_freq()
        fp, fs, loss, att, ftype = params["fp"], params["fs"], params["loss"], params["att"], params["ftype"]

        if isinstance(signal, _UnevenlySignal):
            cls.warn('Filtering Unevenly signal is undefined. Returning original signal.')
            return signal

        nyq = 0.5 * fsamp
        fp = _np.array(fp)
        fs = _np.array(fs)

        wp = fp / nyq
        ws = fs / nyq
        # noinspection PyTupleAssignmentBalance
        b, a = _filter_design.iirdesign(wp, ws, loss, att, ftype=ftype, output="ba")

        sig_filtered = _EvenlySignal(_filtfilt(b, a, signal.get_values()), sampling_freq=signal.get_sampling_freq(),
                                     signal_nature=signal.get_signal_nature(), start_time=signal.get_start_time())

        if _np.isnan(sig_filtered[0]):
            cls.warn('Filter parameters allow no solution. Returning original signal.')
            return signal
        else:
            return sig_filtered

    @_abstract
    def plot(self):
        pass


class DenoiseEDA(_Filter):
    """
    Remove noise due to sensor displacement from the EDA signal.
    
    Parameters
    ----------
    threshold : float, >0
        Threshold to detect the noise
        
    Optional parameters
    -------------------
    
    win_len : float, >0, default = 2
        Length of the window
   
    Returns
    -------
    signal : EvenlySignal
        De-noised signal
            
    """

    def __init__(self, threshold, win_len=2):
        assert threshold > 0, "Threshold value should be positive"
        assert win_len > 0, "Window length value should be positive"
        _Filter.__init__(self, threshold=threshold, win_len=win_len)

    @classmethod
    def algorithm(cls, signal, params):
        threshold = params['threshold']
        win_len = params['win_len']

        # remove fluctiations
        noise = ConvolutionalFilter(irftype='triang', win_len=win_len, normalize=True)(abs(_np.diff(signal)))

        # identify noisy portions
        idx_ok = _np.where(noise <= threshold)[0]

        # fix start and stop of the signal for the following interpolation
        if idx_ok[0] != 0:
            idx_ok = _np.r_[0, idx_ok].astype(int)

        if idx_ok[-1] != len(signal) - 1:
            idx_ok = _np.r_[idx_ok, len(signal) - 1].astype(int)

        denoised = _UnevenlySignal(signal[idx_ok], signal.get_sampling_freq(), x_values=idx_ok, x_type='indices',
                                   duration=signal.get_duration())

        # interpolation
        signal_out = denoised.to_evenly('linear')
        return signal_out


class ConvolutionalFilter(_Filter):
    """
    Filter a signal by convolution with a given impulse response function (IRF).

    Parameters
    ----------
    irftype : str
        Type of IRF to be generated. 'gauss', 'rect', 'triang', 'dgauss', 'custom'.
    win_len : float, >0 (> 8/fsamp for 'gaussian')
        Duration of the generated IRF in seconds (if irftype is not 'custom')
    
    Optional parameters
    -------------------
    irf : numpy.array
        IRF to be used if irftype is 'custom'
    normalize : boolean, default = True
        Whether to normalizes the IRF to have unitary area
    
    Returns
    -------
    signal : EvenlySignal
        Filtered signal

    """

    def __init__(self, irftype, win_len=0, irf=None, normalize=True):
        assert irftype in ['gauss', 'rect', 'triang', 'dgauss', 'custom'],\
            "IRF type must be in ['gauss', 'rect', 'triang', 'dgauss', 'custom']"
        assert irftype == 'custom' or win_len > 0, "Window length value should be positive"
        _Filter.__init__(self, irftype=irftype, win_len=win_len, irf=irf, normalize=normalize)

    # TODO: TEST normalization and results
    @classmethod
    def algorithm(cls, signal, params):
        irftype = params["irftype"]
        normalize = params["normalize"]

        fsamp = signal.get_sampling_freq()
        irf = None

        if irftype == 'custom':
            if 'irf' not in params:
                cls.error("'irf' parameter missing.")
                return signal
            else:
                irf = _np.array(params["irf"])
                n = len(irf)
        else:
            if 'win_len' not in params:
                cls.error("'win_len' parameter missing.")
                return signal
            else:
                n = int(params['win_len'] * fsamp)

                if irftype == 'gauss':
                    if n < 8:
                        # TODO: test, sometimes it returns nan
                        cls.error(
                            "'win_len' too short to generate a gaussian IRF, expected > " + str(_np.ceil(8 / fsamp)))
                    std = _np.floor(n / 8)
                    irf = _gaussian(n, std)
                elif irftype == 'rect':
                    irf = _np.ones(n)
                elif irftype == 'triang':
                    irf_1 = _np.arange(n // 2)
                    irf_2 = irf_1[-1] - _np.arange(n // 2)
                    if n % 2 == 0:
                        irf = _np.r_[irf_1, irf_2]
                    else:
                        irf = _np.r_[irf_1, irf_1[-1] + 1, irf_2]
                elif irftype == 'dgauss':
                    std = _np.round(n / 8)
                    g = _gaussian(n, std)
                    irf = _np.diff(g)

        # NORMALIZE
        if normalize:
            irf = irf / _np.sum(irf)

        signal_ = _np.r_[_np.ones(n) * signal[0], signal, _np.ones(n) * signal[-1]]  # TESTME

        signal_f = _np.convolve(signal_, irf, mode='same')

        signal_out = _EvenlySignal(signal_f[n:-n], sampling_freq=signal.get_sampling_freq(),
                                   signal_nature=signal.get_signal_nature(), start_time=signal.get_start_time())
        return signal_out

    @classmethod
    def plot(cls):
        pass


class DeConvolutionalFilter(_Filter):
    """
    Filter a signal by deconvolution with a given impulse response function (IRF).

    Parameters
    ----------
    irf : numpy.array
        IRF used to deconvolve the signal
    
    Optional parameters
    -------------------
    
    normalize : boolean, default = True
        Whether to normalize the IRF to have unitary area
    deconv_method : str, default = 'sps'
        Available methods: 'fft', 'sps'. 'fft' uses the fourier transform, 'sps' uses the scipy.signal.deconvolve
         function
        
    Returns
    -------
    signal : EvenlySignal
        Filtered signal

    """

    def __init__(self, irf, normalize=True, deconv_method='sps'):
        # TODO Andrea: "check that irf[0]>0 to avoid scipy BUG" I tried but some of your tests fail
        assert deconv_method in ['fft', 'sps'], "Deconvolution method not valid"
        _Filter.__init__(self, irf=irf, normalize=normalize, deconv_method=deconv_method)

    @classmethod
    def algorithm(cls, signal, params):
        irf = params["irf"]
        normalize = params["normalize"]
        deconvolution_method = params["deconv_method"]

        if normalize:
            irf = irf / _np.sum(irf)
        if deconvolution_method == 'fft':
            l = len(signal)
            fft_signal = _np.fft.fft(signal, n=l)
            fft_irf = _np.fft.fft(irf, n=l)
            out = _np.fft.ifft(fft_signal / fft_irf)
        elif deconvolution_method == 'sps':
            cls.warn('sps based deconvolution needs to be tested. Use carefully.')
            out, _ = _deconvolve(signal, irf)
        else:
            cls.error('Deconvolution method not implemented. Returning original signal.')
            out = signal.get_values()

        out_signal = _EvenlySignal(abs(out), sampling_freq=signal.get_sampling_freq(),
                                   signal_nature=signal.get_signal_nature(), start_time=signal.get_start_time())

        return out_signal

    def plot(self):
        _plot(self._params['irf'])
