# encoding=utf-8

from Strategy import Strategy
from BackTest.BackTest import Backtest
from DataHandler.DateHandler import HistoricCSVDataHandler
from Portfolio.Portfolio import Portfolio
from Event.EventEngine import OrderSendEvent, OrderCloseEvent, OrderModifyEvent
from Enums.Enum import OrderType, OrderStatus, EventType
import pandas as pd
from Plot.Plot import Plot


class MA_Cross(Strategy):
    """
    A Simple MA Cross Strategy.
    """
    def __init__(
            self, bars, events, portfolio, spread, commission
    ):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.long_period = 100
        self.short_period = 50
        self.portfolio = portfolio
        self.spread = spread
        self.commission = commission

    def On_Bars(self, event):
        if event.type == EventType.MARKET: #receive the new bar data
            for s in self.symbol_list:
                long_ma = self.bars.MA(s, self.long_period, 1) # calculate the ma valued of the symbols in symbol list.
                short_ma = self.bars.MA(s, self.short_period, 1)
                if (short_ma > long_ma) and self.portfolio.holding_order_count(OrderType.BUY) == 0:
                    openprice = self.bars.get_latest_bar_value(s, 'Open')
                    stoploss = openprice - 0.00001 * 200
                    takeprofit = openprice + 0.00001 * 200
                    #define the buy order event instance
                    order = OrderSendEvent(s, OrderType.BUY, 1, stoploss, takeprofit,
                                           self.bars.get_latest_bar_datetime(s), OrderStatus.HOLDING, openprice,
                                           self.spread)
                    #put the buy order event into the queue
                    self.events.put(order)
                if (short_ma < long_ma) and self.portfolio.holding_order_count(OrderType.SELL) == 0:
                    openprice = self.bars.get_latest_bar_value(s, 'Open')
                    stoploss = openprice + 0.00001 * 200
                    takeprofit = openprice - 0.00001 * 200
                    order = OrderSendEvent(s, OrderType.SELL, 1, stoploss, takeprofit,
                                           self.bars.get_latest_bar_datetime(s), OrderStatus.HOLDING, openprice,
                                           self.spread)
                    self.events.put(order)


if __name__ == '__main__':
    csv_dir = 'D:\Github\Forex_AlgoTrading\\'
    symbol_list = ['EURUSD_15M','USDCAD_15M']
    init_captial = 10000.0
    heartbeat = 0
    start_time = '2017.10.01'
    end_time = '2017.10.31'
    backtest = Backtest(
        csv_dir=csv_dir, symbol_list=symbol_list, initial_capital=init_captial, heartbeat=heartbeat,
        start_date=start_time,
        end_date=end_time, data_handler=HistoricCSVDataHandler, portfolio=Portfolio, strategy=MA_Cross,
        strategy_id=getattr(MA_Cross, '__name__'), spread=0.00010, commission=0, plot=Plot
    )
    backtest.simulate_trading()
