# Forex_AlgoTrading
## Introduction
Forex_AlgoTrading is a Forex Strategy Backtest tools based on Event Drive Model。Comparing with MT4,which is the most popular used platform ,Forex_AlgoTrading has several advantages:
1.  It supports **multiple symbols backtest**.
2.  **Sharp ration** calculation supported.
3.  **Drawdown grap** supported.
4.  **Spread and commission** customization supported.  
5.  **Parameters optimization** is supported using multiprocessing.(Not finished yet)
6.  The Strategy API is open soured and you can use any tech you want like AI and so on.

## Environment Required:
Anaconda of python 2.7 version is recommended.
You can also use requirement file to install the packages required,but you need to install other packages when you use other tools like scikit-learn.

## QuickStart
### About Event Engine
There are several typed if event are defined as follow:
1.  **MarketEvent** should be put into queue when new bar data received.
2.  **OrderSendEvent**should be put into queue when new order created.
3.  **OrderCloseEvent**should be put into queue when the order is closed.
4.  **OrderModifyEvent**should be put into queue when the order is modified.\

You can define your own event types in Event.Event.py,after that you need to bound the callback function in Backtest.Backtest.py like this:
```angular2html
if event.type == EventType.MARKET:
    self.strategy.On_Bars(event)
    self.portfolio.update_balance(event)
    self.portfolio.order_check(event)
elif event.type == EventType.ORDER_SEND:
    self.portfolio.update_order(event)
elif event.type == EventType.ORDER_CLOSE:
    self.portfolio.update_order(event)
    self.portfolio.update_euity(event)
elif event.type == EventType.ORDER_MODIFY:
    self.portfolio.update_order(event)
```
### Demo code for startegy backtest
The following code implements a simple moving average cross startegy:
```angular2html
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
    symbol_list = ['EURUSD_15M']
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

```
The graph including the equity and drawdown curve is shown after the backtest is done.\
![Graph for MA Cross](https://github.com/JadenGu0/Forex_AlgoTrading/blob/master/MA_Cross.png)\
There is another graph from my own strategy.\
![Graph for Trend Strategy](https://github.com/JadenGu0/Forex_AlgoTrading/blob/master/Trend.png)

You need to define your startegy class inheriting from Strategy and rewrite the method **On_Bars** where you should implement you  logics for sending the order,modifying the order or closing the orders.
 ### Deme code for parameters optimization
```angular2html
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
```
Comparing to the demo code for strategy backtest,we create a instance of Grid_Search and do the iteration using the parameters groups created by product.The parameters list,sharp ration and equity will be stored in CSV file after optimization done.\
You can refer to the complete code in [poly.py](https://github.com/JadenGu0/Forex_AlgoTrading/blob/master/Strategy/poly.py)
## Things need to be done
1.  API for drawing the heatmap of optimization reaults.
2.  API for connecting to OANDA platform.
3.  API for dealing with tick data in DataHandler.
4.  API for calculating the label and features when using AI tools.

