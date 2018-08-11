# encoding=utf8
from __future__ import print_function

from abc import ABCMeta, abstractmethod


class Strategy(object):
    """
    Stargegy is a abstract class uesd for define the API if every custom
    strategy created by users.You shoud write your strategy and complete the
    method of OnBars.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def On_Bars(self):
        """
        Do it yourself
        """
        raise NotImplementedError("Should implement calculate_signals()")
