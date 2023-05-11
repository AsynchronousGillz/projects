#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
"""

import statistics
from threading import RLock
from typing import Union

from miniature.metric.metric import Metric


class HistogramBuffer:
    def __init__(self, size: int):
        """

        :param size: int
        """
        self._size = size
        self._array = []
        self._index = 0
        self._lock = RLock()

    def add(self, metric: Union[int, float]) -> None:
        """
        Add metric to the buffer

        :param metric: Union[int, float]
        :return:
        """
        with self._lock:
            try:
                self._array[self._index] = metric
            except IndexError:
                self._array.append(metric)
            self._index = self._index + 1 if self._index < self._size else 0

    def stats(self, percentiles: list = None) -> dict:
        """Get some stats

        :param percentiles: list of percentiles
        :return:
        """
        with self._lock:
            _perc = statistics.quantiles(self._array, n=100)
            stats = {f"p{perc}": _perc[perc] for perc in percentiles}
            stats.update({"sum": sum(self._array), "count": len(self._array)})
            return stats


class HistogramMetric(Metric):
    """A simple histogram metric class"""

    def __init__(self, metric_name: str, size: int = 100):
        """
        :param metric_name: str
        :param size: int
        """
        super().__init__(metric_name)
        self._size = size

    def add(self, label_values: dict, metric: Union[int, float]) -> None:
        """
        :param label_values: dict
        :param metric: Union[int, float]
        :return:
        """
        key = ".".join([f'{k}="{v}"' for k, v in label_values.items()])
        with self._lock:
            try:
                data = self._data[key]
            except KeyError:
                data = HistogramBuffer(self._size)
                self._data[key] = data
            data.add(metric)

    def export(self) -> str:
        """ """
        ret = [
            f"# HELP {self.metric_name} Autogenerated via {self.__class__.__name__}.",
            f"# TYPE {self.metric_name} histogram",
        ]
        with self._lock:
            for key, buffer in self._data:
                labels = ",".join(key.split("."))
                ret.append(f"{self.metric_name} {labels}")
        return "\n".join(ret)
