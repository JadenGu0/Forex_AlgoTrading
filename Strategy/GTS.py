# encoding=utf-8

from Strategy import Strategy
from BackTest.BackTest import Backtest
from DataHandler.DateHandler import HistoricCSVDataHandler
from Portfolio.Portfolio import Portfolio
from Event.EventEngine import OrderSendEvent, OrderCloseEvent, OrderModifyEvent
from Enums.Enum import OrderType, OrderStatus, EventType
from Plot.Plot import Plot
import datetime
class GTS(Strategy):

    def __init__(
            self, bars, events, portfolio,spread,commission
    ):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.long_period = 40
        self.short_period = 7
        self.mom = 350
        self.callback = 0.6
        self.portfolio = portfolio
        self.point = 0.00001
        self.spread=spread
        self.commission=commission

    def On_Bars(self, event):
        if event.type == EventType.MARKET.value:
            for s in self.symbol_list:
                big_high = self.bars.High(s, self.long_period, 1)
                big_low = self.bars.Low(s, self.long_period, 1)
                close_high = self.bars.High(s, self.short_period, 2)
                close_low = self.bars.Low(s, self.short_period, 2)
                last_close = self.bars.get_index_data(s, 'Close', 1)
                buy_number = self.portfolio.holding_order_count(OrderType.BUY.value)
                sell_number = self.portfolio.holding_order_count(OrderType.SELL.value)
                if buy_number == 0 and sell_number == 0:
                    if ((big_high - big_low) > self.mom * self.point and
                            last_close < close_low and
                            last_close > (big_low + (big_high - big_low) * self.callback)
                    ):
                        openprice = self.bars.get_latest_bar_value(s, 'Open')
                        stoploss = openprice - self.point * 500
                        takeprofit = openprice + self.point * 500
                        order = OrderSendEvent(s, OrderType.BUY.value, 1, stoploss, takeprofit,
                                               self.bars.get_latest_bar_datetime(s), OrderStatus.HOLDING.value,
                                               openprice,self.spread)
                        self.events.put(order)

                    if ((big_high - big_low) > self.mom * self.point and
                            last_close > close_high and
                            last_close < (big_high - (big_high - big_low) * self.callback)
                    ):
                        openprice = self.bars.get_latest_bar_value(s, 'Open')
                        stoploss = openprice + self.point * 500
                        takeprofit = openprice - self.point * 500
                        order = OrderSendEvent(s, OrderType.SELL.value, 1, stoploss, takeprofit,
                                               self.bars.get_latest_bar_datetime(s), OrderStatus.HOLDING.value,
                                               openprice,self.spread)
                        self.events.put(order)
                if buy_number != 0 and sell_number == 0:
                    if last_close > close_high:
                        closeprice = self.bars.get_latest_bar_value(s, 'Open')
                        index = self.portfolio.all_holding_buy_orders().index[-1]
                        order = OrderCloseEvent(s, OrderType.BUY.value, index, self.bars.get_latest_bar_datetime(s),
                                                closeprice)
                        self.events.put(order)

                if buy_number == 0 and sell_number != 0:
                    if last_close < close_low:
                        closeprice = self.bars.get_latest_bar_value(s, 'Open')+self.spread
                        index = self.portfolio.all_holding_sell_orders().index[-1]
                        order = OrderCloseEvent(s, OrderType.SELL.value, index, self.bars.get_latest_bar_datetime(s),
                                                closeprice)
                        self.events.put(order)


if __name__ == '__main__':
    csv_dir = 'D:\PythonCode\Forex_AlgoTrading\\'
    symbol_list = ['EURUSD_15M']
    init_captial = 10000.0
    heartbeat = 0
    start_time = '2010.01.01'
    end_time = '2017.10.31'
    backtest = Backtest(
        csv_dir=csv_dir, symbol_list=symbol_list, initial_capital=init_captial, heartbeat=heartbeat,
        start_date=start_time,
        end_date=end_time, data_handler=HistoricCSVDataHandler, portfolio=Portfolio, strategy=GTS,
        strategy_id=getattr(GTS, '__name__'),spread=0.00010,commission=0,plot=Plot
    )
    backtest.simulate_trading()
