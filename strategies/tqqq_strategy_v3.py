import pandas as pd
import numpy as np


def calculate_atr(data, period=14):
    """计算 Average True Range (ATR)"""
    data['H-L'] = data['high'] - data['low']
    data['H-PC'] = abs(data['high'] - data['close'].shift(1))
    data['L-PC'] = abs(data['low'] - data['close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR'] = data['TR'].rolling(period).mean()
    data.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
    return data


def calculate_rsi(series, period=14):
    """计算 RSI 指标"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace({0:1e-10})  # 防止除以0
    rsi = 100 - 100/(1+rs)
    return rsi


class TQQQStrategyV3:
    def __init__(
        self,
        data,
        buy_threshold=0.005,       # 买入阈值0.5%
        sell_threshold=-0.008,     # 卖出阈值-0.8%
        max_position=0.8,          # 最大仓位提高到80%
        stop_loss=0.07,            # 放宽固定止损到7%
        trailing_stop=0.10,        # 放宽追踪止损到10%
        commission=0.0003,         # 佣金0.03%
        slippage=0.0002,           # 滑点0.02%
        vol_threshold=0.03,        # 提高波动率阈值到3%
        partial_sell_ratio=0.4,    # 分批卖出时，一次卖出40%
        partial_sell_gain=0.03,    # 当浮盈达到3%时先卖出部分仓位
        atr_period=14,             # ATR计算周期
        atr_multiplier=3.5         # 提高ATR止损倍数到3.5
    ):
        self.data = data.copy()
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.max_position = max_position
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        self.commission = commission
        self.slippage = slippage
        self.vol_threshold = vol_threshold
        self.partial_sell_ratio = partial_sell_ratio
        self.partial_sell_gain = partial_sell_gain
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

        # 计算基础指标
        self.prepare_data()
        
    def prepare_data(self):
        """计算所需的所有技术指标"""
        # 均线
        self.data['ma_2'] = self.data['avg'].rolling(window=2).mean()
        self.data['ma_7'] = self.data['avg'].rolling(window=7).mean()
        self.data['ma_20'] = self.data['avg'].rolling(window=20).mean()
        self.data['ma_50'] = self.data['avg'].rolling(window=50).mean()  # 添加50日均线
        
        # 波动率
        self.data['volatility'] = self.data['avg'].pct_change().rolling(window=20).std()
        
        # 动量
        self.data['momentum'] = self.data['avg'].pct_change(periods=5)
        self.data['momentum_20'] = self.data['avg'].pct_change(periods=20)  # 添加20日动量
        
        # ATR
        self.data = calculate_atr(self.data, period=self.atr_period)
        
        # RSI
        self.data['rsi'] = calculate_rsi(self.data['close'], period=14)
        
        # 均线金叉/死叉
        self.data['ma_cross'] = (self.data['ma_2'] > self.data['ma_7']).astype(int)
        self.data['ma_trend'] = (self.data['ma_7'] > self.data['ma_20']).astype(int)
        self.data['ma_long_trend'] = (self.data['ma_20'] > self.data['ma_50']).astype(int)  # 长期趋势

    def generate_signals(self):
        """根据技术指标生成交易信号"""
        # 买入信号：放宽条件，使用评分系统
        buy_conditions = pd.DataFrame({
            'ma_cross': (self.data['ma_cross'] > self.data['ma_cross'].shift(1)).astype(int),  # 金叉 +1
            'ma_trend': (self.data['ma_trend'] == 1).astype(int),  # 中期趋势向上 +1
            'ma_long_trend': (self.data['ma_long_trend'] == 1).astype(int),  # 长期趋势向上 +1
            'rsi_good': ((self.data['rsi'] > 45) & (self.data['rsi'] < 75)).astype(int),  # RSI在良好区间 +1
            'vol_good': (self.data['volatility'] < self.vol_threshold * 1.2).astype(int),  # 波动率可接受 +1
            'momentum_good': ((self.data['momentum'] > -0.01) & (self.data['momentum_20'] > 0)).astype(int)  # 动量良好 +1
        })
        
        # 计算买入评分（满分6分）
        buy_score = buy_conditions.sum(axis=1)
        self.data['buy_signal'] = (buy_score >= 4)  # 得分>=4分时产生买入信号
        
        # 卖出信号：收紧条件，需要同时满足多个条件
        self.data['sell_signal'] = (
            (self.data['ma_cross'] < self.data['ma_cross'].shift(1)) &  # 需要死叉
            (
                (
                    (self.data['rsi'] < 35) |  # RSI过低
                    (self.data['rsi'] > 85)    # 或RSI过高
                ) |
                (
                    (self.data['volatility'] > self.vol_threshold * 2.5) &  # 波动率过高且
                    (self.data['momentum'] < 0)  # 动量转负
                )
            )
        )

    def calculate_transaction_costs(self, price, shares):
        """计算交易成本"""
        commission = price * shares * self.commission
        slippage = price * shares * self.slippage
        return commission + slippage

    def calculate_position_size(self, cash, price, volatility):
        """根据波动率和趋势强度动态调整仓位大小"""
        base_position = self.max_position
        
        # 波动率调整：波动率越大，仓位越小
        vol_adj = max(0.4, 1 - volatility / (self.vol_threshold * 1.5))
        
        # RSI调整：RSI在中间区域时仓位最大
        rsi = self.data['rsi'].iloc[-1]
        if rsi < 30 or rsi > 70:
            rsi_adj = 0.6
        elif 45 <= rsi <= 65:
            rsi_adj = 1.0
        else:
            rsi_adj = 0.8
            
        # 趋势强度调整
        trend_adj = 1.0
        if self.data['ma_long_trend'].iloc[-1] == 1:  # 长期趋势向上
            if self.data['ma_trend'].iloc[-1] == 1:  # 中期趋势也向上
                trend_adj = 1.2  # 加仓20%
            
        adjusted_position = base_position * vol_adj * rsi_adj * trend_adj
        max_buy_value = cash * adjusted_position
        shares = int(max_buy_value // price)
        return shares

    def backtest(self, initial_cash=100000):
        """回测策略"""
        self.generate_signals()
        
        cash = initial_cash
        position = 0
        avg_cost = 0.0
        highest_price = 0.0
        atr_stop_price = 0.0
        history = []

        start_idx = max(50, self.atr_period)  # 考虑到新增的50日均线
        for i in range(start_idx, len(self.data)):
            current_price = self.data['close'].iloc[i]
            current_volatility = self.data['volatility'].iloc[i]
            current_atr = self.data['ATR'].iloc[i]

            total_value = cash + position * current_price
            
            if position > 0:
                highest_price = max(highest_price, current_price)
                atr_stop_price = current_price - self.atr_multiplier * current_atr
                unrealized_pnl = (current_price - avg_cost) / avg_cost
                trailing_stop_price = highest_price * (1 - self.trailing_stop)
                
                # 止损检查
                should_stop_loss = False
                
                # 1. 固定止损
                if (current_price / avg_cost - 1) < -self.stop_loss:
                    should_stop_loss = True
                # 2. 追踪止损
                elif current_price < trailing_stop_price:
                    should_stop_loss = True
                # 3. ATR止损
                elif current_price < atr_stop_price:
                    should_stop_loss = True
                
                if should_stop_loss:
                    sell_value = position * current_price
                    transaction_costs = self.calculate_transaction_costs(current_price, position)
                    cash += sell_value - transaction_costs
                    position = 0
                    highest_price = 0
                    atr_stop_price = 0
                    continue

                # 4. 分批止盈：根据盈利幅度调整卖出比例
                elif unrealized_pnl >= self.partial_sell_gain:
                    sell_ratio = min(0.8, self.partial_sell_ratio * (1 + unrealized_pnl))  # 随盈利增加卖出比例
                    shares_to_sell = int(position * sell_ratio)
                    if shares_to_sell > 0:
                        sell_value = shares_to_sell * current_price
                        transaction_costs = self.calculate_transaction_costs(current_price, shares_to_sell)
                        cash += sell_value - transaction_costs
                        position -= shares_to_sell
            
            # 买入信号
            if self.data['buy_signal'].iloc[i] and position == 0:
                shares_to_buy = self.calculate_position_size(cash, current_price, current_volatility)
                if shares_to_buy > 0:
                    transaction_costs = self.calculate_transaction_costs(current_price, shares_to_buy)
                    total_cost = shares_to_buy * current_price + transaction_costs
                    if total_cost <= cash:
                        position = shares_to_buy
                        avg_cost = current_price
                        cash -= total_cost
                        highest_price = current_price
                        atr_stop_price = current_price - self.atr_multiplier * current_atr
            
            # 卖出信号
            elif self.data['sell_signal'].iloc[i] and position > 0:
                sell_value = position * current_price
                transaction_costs = self.calculate_transaction_costs(current_price, position)
                cash += sell_value - transaction_costs
                position = 0
                highest_price = 0
                atr_stop_price = 0

            portfolio_value = cash + position * current_price
            history.append({
                'date': self.data.index[i],
                'cash': cash,
                'position': position,
                'portfolio_value': portfolio_value,
                'close': current_price,
                'volatility': current_volatility,
                'ATR': current_atr,
                'rsi': self.data['rsi'].iloc[i],
                'signal': 'buy' if self.data['buy_signal'].iloc[i] else ('sell' if self.data['sell_signal'].iloc[i] else 'hold')
            })

        return pd.DataFrame(history) 