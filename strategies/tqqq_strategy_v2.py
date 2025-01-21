import pandas as pd
import numpy as np

class TQQQStrategyV2:
    def __init__(self, data):
        self.data = data
        self.results = []
        
        # 计算均线
        self.data['ma_2'] = self.data['avg'].rolling(window=2).mean()
        self.data['ma_7'] = self.data['avg'].rolling(window=7).mean()
        self.data['ma_20'] = self.data['avg'].rolling(window=20).mean()  # 添加20日均线
        
        # 计算波动率
        self.data['volatility'] = self.data['avg'].pct_change().rolling(window=20).std()
        
        # 优化后的参数设置
        self.buy_threshold = 0.005    # 买入阈值0.5%
        self.sell_threshold = -0.008  # 卖出阈值-0.8%
        self.max_position = 0.7       # 最大仓位70%
        self.stop_loss = -0.05        # 止损线5%
        self.trailing_stop = 0.08     # 追踪止损8%
        self.commission = 0.0003      # 手续费0.03%
        self.slippage = 0.0002        # 滑点0.02%
        self.vol_threshold = 0.025    # 波动率阈值2.5%

    def generate_signals(self):
        """计算买入和卖出信号"""
        # 计算技术指标
        self.data['ma_cross'] = (self.data['ma_2'] > self.data['ma_7']).astype(int)  # 均线金叉
        self.data['ma_trend'] = (self.data['ma_7'] > self.data['ma_20']).astype(int) # 中期趋势
        
        # 计算价格动量
        self.data['momentum'] = self.data['avg'].pct_change(periods=5)  # 5日动量
        
        # 优化后的买入条件：
        # 1. 短期均线上穿长期均线（金叉）
        # 2. 中期趋势向上或强动量
        # 3. 波动率在可接受范围内
        self.data['buy_signal'] = (
            (self.data['ma_cross'] > self.data['ma_cross'].shift(1)) & 
            (
                (self.data['ma_trend'] == 1) |  # 中期趋势向上
                (self.data['momentum'] > 0.01)   # 或者强动量
            ) &
            (self.data['volatility'] < self.vol_threshold * 1.2)  # 放宽波动率限制
        )
        
        # 优化后的卖出条件：
        # 1. 短期均线下穿长期均线（死叉）且
        # 2. 中期趋势向下或波动率极高
        self.data['sell_signal'] = (
            (self.data['ma_cross'] < self.data['ma_cross'].shift(1)) &  # 需要死叉
            (
                (self.data['ma_trend'] == 0) |   # 且趋势向下
                (self.data['volatility'] > self.vol_threshold * 2)  # 或者波动率极高
            )
        )

    def calculate_transaction_costs(self, price, shares):
        """计算交易成本"""
        commission = price * shares * self.commission
        slippage = price * shares * self.slippage
        return commission + slippage

    def calculate_position_size(self, cash, price, volatility):
        """根据波动率动态调整仓位"""
        base_position = self.max_position
        # 优化波动率调整的影响
        vol_adj = max(0.3, 1 - volatility/(self.vol_threshold * 1.5))  # 确保至少保持30%的基础仓位
        adjusted_position = base_position * vol_adj
        return adjusted_position

    def backtest(self, initial_cash=100000):
        """回测策略"""
        cash = initial_cash
        position = 0
        history = []
        highest_price = 0  # 用于追踪止损

        # 从第20天开始回测（等待所有技术指标就绪）
        for i in range(20, len(self.data)):
            current_price = self.data['close'].iloc[i]
            current_volatility = self.data['volatility'].iloc[i]
            total_value = cash + position * current_price
            
            # 更新最高价
            if position > 0:
                highest_price = max(highest_price, current_price)
                
                # 计算止损
                position_return = current_price / self.data['close'].iloc[i-1] - 1
                trailing_stop_price = highest_price * (1 - self.trailing_stop)
                
                # 触发止损（固定止损或追踪止损）
                if position_return < self.stop_loss or current_price < trailing_stop_price:
                    sell_value = position * current_price
                    transaction_costs = self.calculate_transaction_costs(current_price, position)
                    cash += sell_value - transaction_costs
                    position = 0
                    highest_price = 0
            
            # 买入信号且没有持仓
            if self.data['buy_signal'].iloc[i] and position == 0:
                # 计算动态仓位
                position_size = self.calculate_position_size(cash, current_price, current_volatility)
                max_buy_value = total_value * position_size
                
                # 计算可买入股数
                shares_to_buy = int(max_buy_value // current_price)
                if shares_to_buy > 0:
                    transaction_costs = self.calculate_transaction_costs(current_price, shares_to_buy)
                    total_cost = shares_to_buy * current_price + transaction_costs
                    if total_cost <= cash:
                        position = shares_to_buy
                        cash -= total_cost
                        highest_price = current_price
            
            # 卖出信号且有持仓
            elif self.data['sell_signal'].iloc[i] and position > 0:
                sell_value = position * current_price
                transaction_costs = self.calculate_transaction_costs(current_price, position)
                cash += sell_value - transaction_costs
                position = 0
                highest_price = 0

            portfolio_value = cash + position * current_price
            history.append({
                'date': self.data.index[i],
                'cash': cash,
                'position': position,
                'portfolio_value': portfolio_value,
                'close': current_price,
                'volatility': current_volatility,
                'signal': 'buy' if self.data['buy_signal'].iloc[i] else ('sell' if self.data['sell_signal'].iloc[i] else 'hold')
            })

        return pd.DataFrame(history) 