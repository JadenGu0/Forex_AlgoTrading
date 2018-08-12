# -*- coding: utf-8 -*-
from __future__ import division
import pandas as pd
import numpy as np
from Enums.Enum import OrderStatus, OrderType
from Enums.Enum import EventType
from Event.EventEngine import OrderSendEvent, OrderModifyEvent, OrderCloseEvent
import pprint


class Portfolio(object):
    """
    The class is used for record the equity ,drawdown,update order info during the backtest operation.
    """

    def __init__(self, bars, event, init_captical, startdate, strategy_id, spread, commission, csv_dir):
        self.csv_dir = csv_dir
        self.startdate = startdate
        self.bars = bars
        self.symbol_list = bars.symbol_list
        self.event = event
        self.commission = commission
        self.init_captical = init_captical
        self.equity_list = ['time', 'equity', 'balance']
        self.order_list = ['symbol', 'lot', 'type', 'opentime', 'closetime', 'openprice', 'closeprice', 'stoploss',
                           'takeprofit', 'status', 'mount']
        self.equity = pd.DataFrame(columns=self.equity_list)
        self.order = pd.DataFrame(columns=self.order_list)
        self.strategy_id = strategy_id
        self.spread = spread
        self._init_captical()

    def _init_captical(self):
        """
        Get the init_captical and append to equity variable
        :return:
        """
        new_data = pd.DataFrame([[self.startdate, self.init_captical, self.init_captical]],
                                columns=self.equity_list)
        self.equity = self.equity.append(new_data, ignore_index=True)

    def update_euity(self, event):
        """
        Update the equity of every MarketEvent
        :return:
        """
        last_equity = self.equity.iloc[-1, :]['equity']
        mount = 0.0
        for s in self.symbol_list:
            new_price = self.bars.get_latest_bar_value(s, 'Open')
            mount += \
                self.order[(self.order['status'] == OrderStatus.CLOSED) & (self.order['symbol'] == s)].iloc[-1:][
                    'mount'].values[0]
        new_data = pd.DataFrame(
            [[self.bars.get_latest_bar_datetime(self.symbol_list[0]), last_equity + mount, last_equity + mount]],
            columns=self.equity_list)
        self.equity = self.equity.append(new_data, ignore_index=True)

    def update_balance(self, event):
        """
        Update the balance of every MarketEvent
        :return:
        """
        mount = 0.0
        for s in self.symbol_list:
            new_price = self.bars.get_latest_bar_value(s, 'Open')
            for index in self.order[
                (self.order['symbol'] == s) & (self.order['status'] == OrderStatus.HOLDING)].iterrows():
                if (index[-1]['type'] == OrderType.BUY):
                    mount += ((new_price - index[-1]['openprice']) * index[-1]['lot'] * 100000 - index[-1][
                        'lot'] * self.commission)
                if (index[-1]['type'] == OrderType.SELL):
                    mount += ((index[-1]['openprice'] - new_price - self.spread) * index[-1]['lot'] * 100000 -
                              index[-1]['lot'] * self.commission)
        if len(self.equity.index != 0):
            old_equity = self.equity.iloc[-1, :]['equity']
            self.equity = self.equity.append(
                pd.DataFrame(
                    [[self.bars.get_latest_bar_datetime(self.symbol_list[0]), old_equity, old_equity + mount]],
                    columns=self.equity_list),
                ignore_index=True
            )
        else:
            self.equity = self.equity.append(
                pd.DataFrame(
                    [[self.bars.get_latest_bar_datetime(self.symbol_list[0]), self.init_captical, self.init_captical]],
                    columns=self.equity_list),
                ignore_index=True
            )

    def update_order(self, event):
        """
        Update the order info.
        If it's a Order_Send event,append the new order info into order variable.
        If it's a Order_Close event,update the order info and calculate the mount of this closed order.
        :return:
        """
        if (event.type == EventType.ORDER_SEND):
            order_info = event
            openprice = order_info.openprice
            if (order_info.order_type == OrderType.BUY):
                order_info.openprice = openprice + self.spread

            new_order = pd.DataFrame([[order_info.symbol, order_info.lot, order_info.order_type, order_info.opentime, 0,
                                       order_info.openprice, 0, order_info.stoploss, order_info.takeprofit,
                                       OrderStatus.HOLDING, 0]], columns=self.order_list)

            self.order = self.order.append(new_order, ignore_index=True)
        if (event.type == EventType.ORDER_CLOSE):
            old_order = self.order.ix[event.index]
            if (old_order['type'] == OrderType.BUY):
                mount = ((event.closeprice - old_order['openprice']) * old_order['lot'] * 100000 - old_order[
                    'lot'] * self.commission)
                self.order.loc[event.index, 'mount'] = mount
                self.order.loc[event.index, 'closeprice'] = event.closeprice
                self.order.loc[event.index, 'closetime'] = event.closetime
                self.order.loc[event.index, 'status'] = OrderStatus.CLOSED

            if (old_order['type'] == OrderType.SELL):
                mount = ((old_order['openprice'] - event.closeprice) * old_order['lot'] * 100000 - old_order[
                    'lot'] * self.commission)
                self.order.loc[event.index, 'mount'] = mount
                self.order.loc[event.index, 'closeprice'] = event.closeprice
                self.order.loc[event.index, 'closetime'] = event.closetime
                self.order.loc[event.index, 'status'] = OrderStatus.CLOSED

    def all_holding_orders(self, event, type):
        """
        Return all the holding orders info
        :return:
        """
        return self.order[self.order['status'] == OrderStatus.HOLDING]

    def all_holding_buy_orders(self):
        """
        Return all the long orders info
        :return:
        """
        return self.order[
            (self.order['status'] == OrderStatus.HOLDING) & (self.order['type'] == OrderType.BUY)]

    def all_holding_sell_orders(self):
        """
        Return all the short orders info
        :return:
        """
        return self.order[
            (self.order['status'] == OrderStatus.HOLDING) & (self.order['type'] == OrderType.SELL)]

    def last_order(self, type):
        """
        Return the last order info of given order type.
        :param type:
        :return: pd.Series数据类型
        """
        return self.order[(self.order['status'] == OrderStatus.HOLDING) & (self.order['type'] == type)].iloc[-1,
               :]

    def all_orders(self, event):
        """
        Return all the order info including holding orders and closed orders.
        :return:
        """
        return self.order_list

    def holding_order_count(self, type):
        """
        Return the order count of the given order type.
        :param type:
        :return:
        """
        order = self.order[(self.order['status'] == OrderStatus.HOLDING) & (self.order['type'] == type)]
        res = len(order.index)
        return res

    def order_check(self, event):
        """
        Check if the order is closed by takeprofit or stoploss of every MarketEvent.
        :param event:
        :return:
        """
        for s in self.symbol_list:
            low = self.bars.get_latest_bar_value(s, 'Low')
            high = self.bars.get_latest_bar_value(s, 'High')
            for order in self.order[
                (self.order['status'] == OrderStatus.HOLDING) & (
                        self.order['type'] == OrderType.BUY)].iterrows():
                stoploss = order[-1]['stoploss']
                profit = order[-1]['takeprofit']
                if (low <= stoploss):
                    order_close = OrderCloseEvent(s, OrderType.BUY, order[0],
                                                  self.bars.get_latest_bar_datetime(s), stoploss)
                    self.event.put(order_close)
                if (high >= profit):
                    order_close = OrderCloseEvent(s, OrderType.BUY, order[0],
                                                  self.bars.get_latest_bar_datetime(s), profit)
                    self.event.put(order_close)
            for order in self.order[(self.order['status'] == OrderStatus.HOLDING) & (
                    self.order['type'] == OrderType.SELL)].iterrows():
                stoploss = order[-1]['stoploss']
                profit = order[-1]['takeprofit']
                if (high - self.spread >= stoploss):
                    order_close = OrderCloseEvent(s, OrderType.SELL, order[0],
                                                  self.bars.get_latest_bar_datetime(s), stoploss - self.spread)
                    self.event.put(order_close)
                if (low <= profit - self.spread):
                    order_close = OrderCloseEvent(s, OrderType.SELL, order[0],
                                                  self.bars.get_latest_bar_datetime(s), profit)
                    self.event.put(order_close)

    def output_equity(self):
        """
        Output the equity and order variables to CSV file.
        :return:
        """
        self.equity.to_csv(self.csv_dir + 'Equity_%s.csv' % (self.strategy_id))
        self.order.to_csv(self.csv_dir + 'Order_%s.csv' % (self.strategy_id))

    def sharp(self):
        """
        Return the sharp ratio.
        :return:
        """
        return np.sqrt(252) * (np.mean(self.order['mount']) / np.std(self.order['mount']))

    def drawdown(self):
        """
        Return the drawdown,maximum drawdown and maximum drawdown duration.
        :return:
        """
        data = self.equity['equity']
        hwm = [0]
        idx = data.index
        drawdown = pd.Series(index=idx)
        duration = pd.Series(index=idx)

        for t in range(1, len(idx)):
            hwm.append(max(hwm[t - 1], data[t]))
            drawdown[t] = (hwm[t] - data[t])
            duration[t] = (0 if drawdown[t] == 0 else duration[t - 1] + 1)

        return drawdown, drawdown.max(), duration.max()

    def get_statistics(self):
        """
        Calculate the statistics info based on backtest restule.
        :return:
        """
        all_profit = self.equity.iloc[-1]['equity'] - self.init_captical
        total_return = (all_profit / self.init_captical - 1) * 100
        drawdown, max_dd, dd_duration = self.drawdown()
        max_drawdown = max_dd
        buy_order_number = len(self.order[self.order['type'] == OrderType.BUY].index)
        sell_order_number = len(self.order[self.order['type'] == OrderType.SELL].index)
        buy_order_profit = self.order[self.order['type'] == OrderType.BUY]['mount'].sum()
        sell_order_profit = self.order[self.order['type'] == OrderType.SELL]['mount'].sum()
        proporty = (
                           len(self.order[self.order['mount'] >= 0].index)
                           / len(self.order.index)
                   ) * 100
        mean = self.order['mount'].mean()
        std = self.order['mount'].std()
        profit_factor = abs(
            self.order[self.order['mount'] >= 0]['mount'].sum() / self.order[self.order['mount'] < 0]['mount'].sum())

        stats = [
            ('Total Profit', '%0.2f' % (all_profit)),
            ('Sharp Ration', '%0.2f' % self.sharp()),
            ('Max Drawdown', '%d' % (max_drawdown)),
            ('Buy Number', '%d' % (buy_order_number)),
            ('Buy Order Profit', '%d' % (buy_order_profit)),
            ('Sell Number', '%d' % (sell_order_number)),
            ('Sell Order Profit', '%d' % (sell_order_profit)),
            ('Win Rate', '%0.2f%%' % (proporty)),
            ('profit_factor', '%0.2f' % (round(profit_factor, 2))),
            ('Std of Order Profit', '%0.2f' % (std)),
            ('Mean of Order Profit', '%0.2f' % (mean))
        ]
        pprint.pprint(stats)
        return stats
