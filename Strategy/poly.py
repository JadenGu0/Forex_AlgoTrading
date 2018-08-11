# encoding=utf-8

from Strategy import Strategy
from BackTest.BackTest import Backtest, Grid_Search
from DataHandler.DateHandler import HistoricCSVDataHandler
from Portfolio.Portfolio import Portfolio
from Event.EventEngine import OrderSendEvent, OrderCloseEvent, OrderModifyEvent
from Enums.Enum import OrderType, OrderStatus, EventType
from Plot.Plot import Plot
import numpy as np
from itertools import product
import datetime


class Poly(Strategy):

    def __init__(
            self, bars, events, portfolio, spread, commission, para_dict
    ):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.stoploss = 1000
        self.portfolio = portfolio
        self.point = 0.00001
        self.spread = spread
        self.para_dict = para_dict
        self.commission = commission

    def On_Bars(self, event):
        if event.type == EventType.MARKET:
            for s in self.symbol_list:
                buy_number = self.portfolio.holding_order_count(OrderType.BUY)
                sell_number = self.portfolio.holding_order_count(OrderType.SELL)
                close = self.bars.get_latest_bars_values(s, 'Close', self.para_dict['period'] + 1)[0:-1]
                if (len(close) == self.para_dict['period']):
                    index = np.arange(len(close))
                    poly1 = np.polyfit(index, close, 1)
                    poly2 = np.polyfit(index, close, 2)
                    poly1_div = poly1[0]
                    poly2_div = (self.para_dict['period'] + 1) * 2 * poly2[0] + poly2[1]
                else:
                    continue
                if (buy_number == 0):
                    if (poly1_div > 0 and poly2_div > 0):
                        openprice = self.bars.get_latest_bar_value(s, 'Open')
                        stoploss = openprice - self.stoploss * self.point
                        takeprofit = openprice + self.para_dict['takeprofit'] * self.point
                        order = OrderSendEvent(s, OrderType.BUY, 1, stoploss, takeprofit,
                                               self.bars.get_latest_bar_datetime(s), OrderStatus.HOLDING,
                                               openprice, self.spread)
                        self.events.put(order)

                if (sell_number == 0):
                    if (poly1_div < 0 and poly2_div < 0):
                        openprice = self.bars.get_latest_bar_value(s, 'Open')
                        stoploss = openprice + self.stoploss * self.point
                        takeprofit = openprice - self.para_dict['takeprofit'] * self.point
                        order = OrderSendEvent(s, OrderType.SELL, 1, stoploss, takeprofit,
                                               self.bars.get_latest_bar_datetime(s), OrderStatus.HOLDING,
                                               openprice, self.spread)
                        self.events.put(order)

                if buy_number != 0 and sell_number == 0:
                    if poly1_div > 0 and poly2_div < 0:
                        closeprice = self.bars.get_latest_bar_value(s, 'Open')
                        index = self.portfolio.all_holding_buy_orders().index[-1]
                        order = OrderCloseEvent(s, OrderType.BUY, index, self.bars.get_latest_bar_datetime(s),
                                                closeprice)
                        self.events.put(order)

                if buy_number == 0 and sell_number != 0:
                    if poly1_div < 0 and poly2_div > 0:
                        closeprice = self.bars.get_latest_bar_value(s, 'Open') + self.spread
                        index = self.portfolio.all_holding_sell_orders().index[-1]
                        order = OrderCloseEvent(s, OrderType.SELL, index, self.bars.get_latest_bar_datetime(s),
                                                closeprice)
                        self.events.put(order)


if __name__ == '__main__':
    csv_dir = 'D:\PythonCode\Forex_AlgoTrading\\'
    symbol_list = ['EURUSD_1D']
    init_captial = 10000.0
    heartbeat = 0
    start_time = '2018.01.01'
    end_time = '2018.08.01'
    #define the parameters used for optimization
    takeprofit = [1000, 1500, 2000]
    period = [15, 20, 25, 35, 40]
    strat_params_list = list(product(
        takeprofit, period
    ))
    strat_params_dict_list = [
        dict(takeprofit=sp[0], period=sp[1])
        for sp in strat_params_list
    ]
    optimization = Grid_Search(
        csv_dir=csv_dir, symbol_list=symbol_list, initial_capital=init_captial, heartbeat=heartbeat,
        start_date=start_time,
        end_date=end_time, data_handler=HistoricCSVDataHandler, portfolio=Portfolio, strategy=Poly,
        strategy_id=getattr(Poly, '__name__'), spread=0.00010, commission=0, plot=Plot, para_list=strat_params_dict_list
    )
    optimization.parameter_optimization()
