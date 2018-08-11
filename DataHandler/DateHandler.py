# encoding=utf8

from abc import ABCMeta, abstractmethod
import pandas as pd
import numpy as np
import os
from Event.EventEngine import MarketEvent
from collections import defaultdict
from Queue import Queue, Empty


class DataHandler(object):
    """
    DahaHandler is a abstract class used for defining the follow API,
    including historical data and real tick data.
    The goal id to output the bar data of a defined symbol.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        Return the latest bar data of the given symbol
        :param symbol:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Return the N bars data of the given symbol
        :param symbol:
        :param N:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Return the latest bar datetime of given symbol
        :param symbol:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        Return the latest bar data type of given symbol.
        :param symbol:
        :param val_type:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Return the latest bars data type of given symbol
        :param symbol:
        :param val_type:
        :param N:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bars_values()")

    @abstractmethod
    def update_bars(self):
        """
        Store the latest bar data in variable
        :return:
        """
        raise NotImplementedError("Should implement update_bars()")


class HistoricCSVDataHandler(DataHandler):
    """
    Class used for handler the data which stored in CSV file.
    """

    def __init__(self, events, csv_dir, symbol_list, start_time, end_time):
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.start_time = start_time
        self.end_time = end_time
        self.symbol_data = {}
        self.latest_symbol_data = defaultdict(list)
        self.continue_backtest = True
        self._open_csv_file()

    def _open_csv_file(self):
        """
        Slice the data from csv file using the given start time and end time
        :return:
        """
        for s in self.symbol_list:
            self.symbol_data[s] = pd.read_csv(
                os.path.join(self.csv_dir, '%s.csv' % s),
                header=0, parse_dates=True,

            )
            self.symbol_data[s] = self.symbol_data[s][self.symbol_data[s]['Time'] >= self.start_time]
            self.symbol_data[s] = self.symbol_data[s][self.symbol_data[s]['Time'] <= self.end_time]
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].iterrows()

    def _get_new_bar(self, symbol):
        """
        Return the latest bar data of given symbol
        :param symbol:
        :return:
        """
        for b in self.symbol_data[symbol]:
            yield b

    def get_latest_bar(self, symbol):
        """
        Return the latest bar data of the given symbol
        :param symbol:
        :return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Return the N bars data of the given symbol
        :param symbol:
        :param N:
        :return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Return the latest bar datetime of given symbol
        :param symbol:
        :return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data")
            raise
        else:
            return getattr(bars_list[-1][1], 'Time')

    def get_latest_bar_close(self, symbol):
        """
        Return the close price of latest bar.(Close price is most frequently used data)
        :param symbol:
        :return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data")
            raise
        else:
            return getattr(bars_list[-1][1], 'Close')

    def get_latest_bar_value(self, symbol, val_type):
        """
        Return the latest bar data type of given symbol.
        :param symbol:
        :param val_type:
        :return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That Symbol is not available in the historical data")
            raise
        else:
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Return the latest bars data type of given symbol
        :param symbol:
        :param val_type:
        :param N:
        :return:
        """
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("That Symbol is not available in the historical data")
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    def get_index_data(self, symbol, val_type, N):
        """
        Return the defined type value of symbol using the given shift of N.
        Which if actually the Open[N],Close[N] if MT4.
        :param symbol:
        :param val_type:
        :param N:
        :return:
        """
        return self.get_latest_bars_values(symbol, val_type, N + 1)[0]

    def update_bars(self):
        """
        Store the latest bar data in variable and put the event in quene.
        :return:
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())

    def MA(self, symbol, period, shift):
        """
        Return the moveing average using given symbol,period and shift.
        the calculation is based on close price.
        :param symbol:
        :param period:
        :param shift:
        :return:
        """
        data = self.get_latest_bars_values(symbol, 'Close', period + shift)
        return np.mean(data[0:-shift])

    def High(self, symbol, period, shift):
        """
        Return the Maximum price value using the given symbol,period and shift.
        :param symbol:
        :param period:
        :param shift:
        :return:
        """
        data = self.get_latest_bars_values(symbol, 'Close', period + shift)
        if data.__len__() >= period + 1:
            return np.max(data[0:-shift])
        else:
            return 0

    def Low(self, symbol, period, shift):
        """
        Return the Minimum price value using the given symbol,period and shift.
        :param symbol:
        :param period:
        :param shift:
        :return:
        """
        data = self.get_latest_bars_values(symbol, 'Close', period + shift)
        if data.__len__() >= period + 1:
            return np.min(data[0:-shift])
        else:
            return 0
