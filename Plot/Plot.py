import pandas as pd
import matplotlib.pyplot as plt


class Plot(object):
    """
    Plot define the method of plot the equity graph of the given strategy_id
    """

    def __init__(self, csv_dir, portfolio, strategy_id):
        self.csv_dir = csv_dir
        self.portfolio = portfolio
        self.strategy_id = strategy_id

    def plot_equity(self):
        """
        Plot the graph of given strategy_id
        :return:
        """
        data = pd.read_csv(self.csv_dir + '\\Equity_' + self.strategy_id + '.csv', header=0, parse_dates=True,
                           index_col=0)
        fig = plt.figure()
        fig.patch.set_facecolor('white')

        ax1 = fig.add_subplot(211, ylabel='equity')
        data['equity'].plot(ax=ax1, color='blue', lw=2.)
        plt.grid(True)
        ax2 = fig.add_subplot(212, ylabel='Drawdowns')
        draw, draw_max, dur_max = self.portfolio.drawdown()
        draw.plot(ax=ax2, color='Red', lw=2.)
        plt.grid(True)
        plt.show()
        plt.show()

    def plot_candle(self):
        pass
