import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from strategies.tqqq_strategy import TQQQStrategy

class Backtester:
    def __init__(self, data):
        self.data = data
        self.strategy = TQQQStrategy(data)
    
    def run_backtest(self):
        # 生成买卖信号
        self.strategy.generate_signals()
        
        # 执行回测
        results = self.strategy.backtest()
        
        # 计算绩效指标
        self.calculate_performance(results)
    
    def calculate_performance(self, results):
        """计算并输出绩效指标"""
        # 设置日期索引
        results.set_index('date', inplace=True)
        
        # 计算每日收益率
        results['daily_return'] = (results['portfolio_value'] - results['portfolio_value'].shift(1)) / results['portfolio_value'].shift(1)
        
        # 计算总收益率（使用初始值和最终值）
        initial_value = results['portfolio_value'].iloc[0]
        final_value = results['portfolio_value'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value
        
        # 计算年化收益率
        days = (results.index[-1] - results.index[0]).days
        trading_days = len(results)  # 实际交易天数
        annualized_return = ((1 + total_return) ** (252 / trading_days)) - 1
        
        # 计算夏普比率
        risk_free_rate = 0.02  # 假设无风险利率为2%
        excess_returns = results['daily_return'] - risk_free_rate/252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        
        # 计算最大回撤
        rolling_max = results['portfolio_value'].expanding().max()
        drawdown = (results['portfolio_value'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 计算胜率
        win_rate = (results['daily_return'] > 0).mean()
        
        # 计算交易次数和平均每笔收益
        buy_trades = len(results[results['signal'] == 'buy'])
        sell_trades = len(results[results['signal'] == 'sell'])
        total_trades = buy_trades + sell_trades
        avg_trade_return = total_return / (total_trades/2) if total_trades > 0 else 0
        
        # 输出绩效
        print("\n=== 策略绩效报告 ===")
        print(f"回测期间: {results.index[0].strftime('%Y-%m-%d')} 到 {results.index[-1].strftime('%Y-%m-%d')}")
        print(f"初始资金: ${initial_value:,.2f}")
        print(f"最终资金: ${final_value:,.2f}")
        print(f"总收益率: {total_return:.2%}")
        print(f"年化收益率: {annualized_return:.2%}")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"最大回撤: {max_drawdown:.2%}")
        print(f"胜率: {win_rate:.2%}")
        print(f"总交易次数: {total_trades}")
        print(f"买入交易: {buy_trades}")
        print(f"卖出交易: {sell_trades}")
        print(f"平均每笔交易收益: {avg_trade_return:.2%}")
        print("==================\n")
        
        # 计算月度统计
        monthly_returns = results['portfolio_value'].resample('ME').last().pct_change()
        print("月度统计:")
        print(f"最佳月度收益: {monthly_returns.max():.2%}")
        print(f"最差月度收益: {monthly_returns.min():.2%}")
        print(f"平均月度收益: {monthly_returns.mean():.2%}")
        print(f"月度收益标准差: {monthly_returns.std():.2%}")
        print("==================\n")
        
        # 绘制回测结果图表
        self.plot_results(results)
        
        # 保存结果
        results.to_csv('results/performance.csv')
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'avg_trade_return': avg_trade_return
        }
    
    def plot_results(self, results):
        """绘制回测结果图表"""
        plt.style.use('default')  # 使用默认样式
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 15))
        
        # 绘制资产净值曲线
        ax1.plot(results.index, results['portfolio_value'], label='Portfolio Value', color='blue')
        ax1.set_title('Portfolio Value Over Time')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.grid(True)
        ax1.legend()
        
        # 绘制每日收益率
        ax2.plot(results.index, results['daily_return'].rolling(window=20).mean(), label='20-day Moving Average Return', color='green')
        ax2.set_title('Daily Returns (20-day Moving Average)')
        ax2.set_ylabel('Daily Return')
        ax2.grid(True)
        ax2.legend()
        
        # 绘制回撤
        drawdown = (results['portfolio_value'] / results['portfolio_value'].expanding().max() - 1)
        ax3.fill_between(results.index, drawdown, 0, color='red', alpha=0.3, label='Drawdown')
        ax3.set_title('Drawdown Over Time')
        ax3.set_ylabel('Drawdown')
        ax3.grid(True)
        ax3.legend()
        
        plt.tight_layout()
        plt.savefig('results/backtest_results.png')
        plt.close()
        
        # 绘制月度收益热力图
        self.plot_monthly_returns(results)

    def plot_monthly_returns(self, results):
        """绘制月度收益热力图"""
        # 计算月度收益
        monthly_returns = results['portfolio_value'].resample('M').last().pct_change()
        monthly_returns_table = pd.DataFrame(monthly_returns)
        monthly_returns_table.index = pd.MultiIndex.from_arrays([
            monthly_returns_table.index.year,
            monthly_returns_table.index.month
        ])
        monthly_returns_pivot = monthly_returns_table.pivot_table(
            values='portfolio_value',
            index=monthly_returns_table.index.get_level_values(0),
            columns=monthly_returns_table.index.get_level_values(1)
        )

        # 绘制热力图
        plt.figure(figsize=(15, 8))
        sns.heatmap(
            monthly_returns_pivot,
            annot=True,
            fmt='.2%',
            center=0,
            cmap='RdYlGn',
            cbar_kws={'label': 'Monthly Return'}
        )
        plt.title('Monthly Returns Heatmap')
        plt.xlabel('Month')
        plt.ylabel('Year')
        plt.savefig('results/monthly_returns_heatmap.png')
        plt.close()
