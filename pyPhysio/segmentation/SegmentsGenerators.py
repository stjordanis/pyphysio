# coding=utf-8
from ..PhUI import PhUI
from ..BaseSegmentation import SegmentsGenerator, Segment
from ..Signal import EvenlySignal as _EvenlySignal

__author__ = 'AleB'


class LengthSegments(SegmentsGenerator):
    """
    Constant length (samples number) segments
    __init__(self, step, width=0, start=0)
    """

    def __init__(self, params=None, **kwargs):
        super(LengthSegments, self).__init__(params, kwargs)
        assert "step" in self._params, "Need the parameter 'step' for the segmentation."
        self._step = None
        self._width = None
        self._i = None

    def init_segmentation(self):
        if self._signal is None:
            raise ValueError("Can't preview the segments without a signal here. Use the syntax "
                             + LengthSegments.__name__ + "(p[params])(signal)")
        self._step = self._params["step"]
        self._width =\
            self._params["step"] if "width" not in self._params or self._params["width"] == 0 else self._params["width"]
        self._i = self._params["start"] if "start" in self._params else 0
        self._signal = self._signal

    def next_segment(self):
        o = self._i
        self._i += self._step
        s = Segment(o, o + self._width, '', self._signal)
        if s.is_empty():
            raise StopIteration()
        return s


class TimeSegments(SegmentsGenerator):
    """
    Constant length (time) segments
    __init__(self, step, width=0, start=0)
    """
    def __init__(self, params=None, **kwargs):
        super(TimeSegments, self).__init__(params, kwargs)
        assert "step" in self._params, "Need the parameter 'step' for the segmentation."
        self._step = None
        self._width = None
        self._i = None
        self._c_times = None

    def init_segmentation(self):
        self._step = self._params["step"]
        self._width =\
            self._params["step"] if "width" not in self._params or self._params["width"] == 0 else self._params["width"]
        self._i = self._params["start"] if "start" in self._params else 0
        self._signal = self._signal

    def next_segment(self):
        if self._signal is None:
            PhUI.w("Can't preview the segments without a signal here. Use the syntax "
                   + TimeSegments.__name__ + "(p[params])(signal)")
            raise StopIteration()
        b = e = self._i
        l = len(self._signal)
        while self._i < l and self._signal.get_times(self._i) <= self._signal.get_times(b) + self._step:
            self._i += 1
        while e < l and self._signal.get_times(e) <= self._signal.get_times(b) + self._width:
            e += 1
        s = Segment(b, e, '', self._signal)
        if s.is_empty():
            raise StopIteration()
        return s


class ExistingSegments(SegmentsGenerator):
    """
    Wraps a list of windows from an existing collection.
    """

    def __init__(self, params=None, **kwargs):
        super(ExistingSegments, self).__init__(params, kwargs)
        assert "segments" in self._params, "Need the parameter 'segments' (array of Segment) for the segmentation."
        self._wins = None
        self._ind = None

    def init_segmentation(self):
        self._wins = self._params["segments"]
        self._ind = 0

    def next_segment(self):
        if self._ind < len(self._wins):
            w = self._wins[self._ind]
            if self._signal is not None:
                assert isinstance(w, Segment), "%s is not a Segment" % str(w)
                w = Segment(w.begin, w.end, w.label, self._signal)
                if w.is_empty():
                    self._ind = 0
                    raise StopIteration()
            self._ind += 1
            return w
        else:
            self._ind = 0
            raise StopIteration()


class FromEventsSegments(SegmentsGenerator):
    """
    Generates a list of windows from a labels list.
    """

    def __init__(self, params=None, **kwargs):
        super(FromEventsSegments, self).__init__(params, kwargs)
        assert "events" in self._params, "Need the parameter 'events' (EventSignal) for this segmentation."
        self._i = None
        self._t = None
        self._s = None
        self._ibn = None
        self._events = None
        self._c_times = None

    def init_segmentation(self):
        self._ibn = self._params["include_baseline_name"] if "include_baseline_name" in self._params else None
        self._events = self._params["events"]
        self._s = 0
        self._i = 0
        self._t = self._events.get_times(0)

    def next_segment(self):
        if self._signal is None:
            PhUI.w("Can't preview the segments without a signal here. Use the syntax "
                   + LengthSegments.__name__ + "(p[params])(signal)")
            raise StopIteration()
        else:
            l = len(self._signal)
            if self._i < l:
                if self._s < len(self._events) - 1:
                    o = self._i
                    self._t = self._events.get_times(self._s + 1)
                    while self._i < l and self._signal.get_times(self._i) <= self._t:
                        self._i += 1
                    w = Segment(o, self._i, self._events[self._s], self._signal)
                elif self._s < len(self._events):
                    w = Segment(self._i, len(self._signal), self._events[self._s], self._signal)
                else:
                    raise StopIteration()
            else:
                raise StopIteration()
        self._s += 1
        return w