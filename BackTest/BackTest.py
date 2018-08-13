# -*- coding: utf-8 -*-

# backtest.py

from __future__ import print_function
from Queue import Queue, Empty
import time
from Enums.Enum import EventType
from Error.Error import EquityError

class Backtest(object):
    """
    Class used for strategy backtest
    """

    def __init__(
            self, csv_dir, symbol_list, initial_capital,
            heartbeat, start_date, end_date, data_handler,
            portfolio, strategy, strategy_id, spread, commission, plot
    ):
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.end_date = end_date
        self.data_handler_cls = data_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy
        self.strategy_id = strategy_id
        self.spread = spread
        self.commission = commission
        self.plot_cls = plot
        self.events = Queue()
        self.backtest=True
    def _generate_trading_instances(self):
        """
        Initialize the instance used for startegy backtest,including data_handler,portfolio and startegy
        """
        print(
            "Initizalization..."
        )

        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, self.symbol_list, self.start_date,
                                                  self.end_date)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.initial_capital, self.start_date,
                                            self.strategy_id, self.spread, self.commission,self.csv_dir)
        self.strategy = self.strategy_cls(self.data_handler, self.events, self.portfolio, self.spread, self.commission)
        self.plot = self.plot_cls(self.csv_dir, self.portfolio, self.strategy_id)

    def _run_backtest(self):
        """
        The execution of backtest.
        """
        i = 0
        while True:
            i += 1
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
                #print(self.data_handler.get_latest_bar_datetime(self.symbol_list[0]))
            else:
                break
            while self.backtest:
                try:
                    event = self.events.get(False)
                except Empty:
                    break
                else:
                    if event is not None:
                        if event.type == EventType.MARKET:
                            try:
                                self.strategy.On_Bars(event)
                                self.portfolio.update_balance(event)
                                self.portfolio.order_check(event)
                            except EquityError:
                                print('Not Engough Equity,Backtest Will be Stop...')
                                self.backtest=False
                                break
                        elif event.type == EventType.ORDER_SEND:
                            self.portfolio.update_order(event)
                        elif event.type == EventType.ORDER_CLOSE:
                            try:
                                self.portfolio.update_order(event)
                                self.portfolio.update_euity(event)
                            except EquityError:
                                print ('Not Engough Equity,Backtest Will be Stop...')
                                self.backtest=False
                                break
                        elif event.type == EventType.ORDER_MODIFY:
                            self.portfolio.update_order(event)
            time.sleep(self.heartbeat)

    def simulate_trading(self):
        """
        Simulate the operation of backtest.
        """
        self._generate_trading_instances()
        self._run_backtest()
        self.portfolio.output_equity()
        self.portfolio.get_statistics()
        self.plot.plot_equity()


class Grid_Search(object):
    """
    Class used for grid search of parameter optimazation.
    """

    def __init__(
            self, csv_dir, symbol_list, initial_capital,
            heartbeat, start_date, end_date, data_handler,
            portfolio, strategy, strategy_id, spread, commission, plot, para_list
    ):
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.end_date = end_date
        self.data_handler_cls = data_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy
        self.strategy_id = strategy_id
        self.spread = spread
        self.commission = commission
        self.plot_cls = plot
        self.para_list = para_list
        self.events = Queue()

    def _generate_trading_instances(self, sp):
        """
        Initialization of instance used for parameter optimization
        """
        print(
            "Initialization..."
        )
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, self.symbol_list, self.start_date,
                                                  self.end_date)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.initial_capital, self.start_date,
                                            self.strategy_id, self.spread, self.commission,self.csv_dir)
        self.strategy = self.strategy_cls(self.data_handler, self.events, self.portfolio, self.spread, self.commission,
                                          sp)
        self.plot = self.plot_cls(self.csv_dir, self.portfolio, self.strategy_id)

    def _run_backtest(self):
        """
        Backtest for every paramater group
        """
        i = 0
        while True:
            i += 1
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
                break
            while True:
                try:
                    event = self.events.get(False)
                except Empty:
                    break
                else:
                    if event is not None:
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
            time.sleep(self.heartbeat)

    def parameter_optimization(self):
        """
        Simulation backtest for every parameter group
        """
        out = open(self.csv_dir + self.strategy_id + '_gridsearch.csv', "w")
        spl = len(self.para_list)
        for i, sp in enumerate(self.para_list):
            print("Strategy %s out of %s..." % (i + 1, spl))
            self._generate_trading_instances(sp)
            self._run_backtest()
            stats = self.portfolio.get_statistics()
            tot_profit = float(stats[0][1])
            sharpe = float(stats[1][1])
            max_dd = float(stats[2][1])
            win_rate = float(stats[7][1].replace("%", ""))
            profit_factor = float(stats[8][1])

            out.write(
                "%s,%s,%s,%s,%s,%s,%s\n" %
                (sp["takeprofit"], sp["period"], tot_profit, sharpe, max_dd, win_rate, profit_factor)
            )
        out.close()
