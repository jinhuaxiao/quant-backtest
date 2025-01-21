import pandas as pd
import numpy as np

class TQQQStrategy:
    def __init__(self, data):
        self.data = data
        self.results = []
        
        # 计算均线
        self.data['ma_2'] = self.data['avg'].rolling(window=2).mean()
        self.data['ma_7'] = self.data['avg'].rolling(window=7).mean()
        
        # 设置买卖阈值
        self.buy_threshold = 0.0003  # 买入阈值
        self.sell_threshold = -0.0002  # 卖出阈值

    def generate_signals(self):
        """计算买入和卖出信号"""
        # 为了方便访问未来数据，我们使用shift来移动数据
        # avg[0]是当天，avg[1]是明天，avg[2]是后天
        self.data['avg_0'] = self.data['avg']  # 当天
        self.data['avg_1'] = self.data['avg'].shift(-1)  # 明天
        self.data['avg_2'] = self.data['avg'].shift(-2)  # 后天
        
        # ma_2[0]是当天的2日均线
        self.data['ma_2_0'] = self.data['ma_2']
        
        # ma_7[0]是当天的7日均线，ma_7[1]是明天的7日均线
        self.data['ma_7_0'] = self.data['ma_7']
        self.data['ma_7_1'] = self.data['ma_7'].shift(-1)
        
        # 买入条件：
        # 1. 明天的均价减去今天的2日均线大于阈值
        # 2. 后天的均价相对明天的7日均线涨幅大于卖出阈值
        self.data['buy_signal'] = (
            (self.data['avg_1'] - self.data['ma_2_0'] > self.buy_threshold) & 
            (self.data['avg_2'] / self.data['ma_7_1'] - 1 >= self.sell_threshold)
        )
        
        # 卖出条件：明天的均价相对今天的7日均线跌幅小于阈值
        self.data['sell_signal'] = (
            self.data['avg_1'] / self.data['ma_7_0'] - 1 < self.sell_threshold
        )

    def backtest(self, initial_cash=100000):
        """回测策略"""
        cash = initial_cash
        position = 0
        history = []

        # 从第7天开始回测，到倒数第3天结束（因为我们需要后天的数据）
        for i in range(7, len(self.data)-2):
            current_price = self.data['close'].iloc[i]
            next_open = self.data['open'].iloc[i+1]  # 明天的开盘价
            total_value = cash + position * current_price
            
            # 买入信号且没有持仓
            if self.data['buy_signal'].iloc[i] and position == 0:
                # 使用97%的资金买入，按明天开盘价计算
                position = int((total_value * 0.97) // next_open)
                cash -= position * next_open
            
            # 卖出信号且有持仓
            elif self.data['sell_signal'].iloc[i] and position > 0:
                # 按明天开盘价卖出
                cash += position * next_open
                position = 0

            portfolio_value = cash + position * current_price
            history.append({
                'date': self.data.index[i],
                'cash': cash,
                'position': position,
                'portfolio_value': portfolio_value,
                'close': current_price,
                'signal': 'buy' if self.data['buy_signal'].iloc[i] else ('sell' if self.data['sell_signal'].iloc[i] else 'hold')
            })

        return pd.DataFrame(history)
