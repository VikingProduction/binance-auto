import backtrader as bt
from utils import load_config

class Strategy(bt.Strategy):
    def __init__(self):
        cfg = load_config()
        self.cfg = cfg
        self.rsi = bt.indicators.RSI(self.data.close, period=cfg['indicators']['rsi_window'])
        self.sma_short = bt.indicators.SMA(self.data.close, period=cfg['indicators']['sma_short_window'])
        self.sma_long = bt.indicators.SMA(self.data.close, period=cfg['indicators']['sma_long_window'])

    def next(self):
        if not self.position:
            if self.rsi < self.cfg['indicators']['rsi_buy'] and self.sma_short > self.sma_long:
                size = self.broker.getcash() * self.cfg['position_size_pct'] / self.data.close[0]
                self.buy(size=size)
        else:
            change = (self.data.close[0] / self.position.price) - 1
            if change >= self.cfg['take_profit_pct'] or change <= -self.cfg['trailing_stop_pct']:
                self.close()

if __name__=='__main__':
    cerebro = bt.Cerebro()
    cfg = load_config()
    data = bt.feeds.GenericCSVData(
        dataname='historical.csv',
        dtformat='%Y-%m-%d %H:%M:%S',
        datetime=0, open=1, high=2, low=3, close=4, volume=5,
        openinterest=-1
    )
    cerebro.adddata(data)
    cerebro.addstrategy(Strategy)
    cerebro.run()
    cerebro.plot()
