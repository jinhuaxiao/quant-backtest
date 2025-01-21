import pandas as pd
import numpy as np
from backtester.backtest import Backtester
from strategies.tqqq_strategy import TQQQStrategy
from strategies.tqqq_strategy_v2 import TQQQStrategyV2
from strategies.tqqq_strategy_v3 import TQQQStrategyV3
from data.data_fetcher import fetch_tqqq_data

def calculate_performance_metrics(results):
    """计算详细的性能指标"""
    # 基础计算
    initial_value = results['portfolio_value'].iloc[0]
    final_value = results['portfolio_value'].iloc[-1]
    total_return = (final_value - initial_value) / initial_value
    
    # 计算交易统计
    trades = results[results['signal'].isin(['buy', 'sell'])]
    total_trades = len(trades)
    buy_trades = len(trades[trades['signal'] == 'buy'])
    sell_trades = len(trades[trades['signal'] == 'sell'])
    
    # 计算收益率统计
    daily_returns = results['portfolio_value'].pct_change()
    annual_return = (1 + total_return) ** (252 / len(results)) - 1
    
    # 计算风险指标
    risk_free_rate = 0.02  # 假设无风险利率为2%
    excess_returns = daily_returns - risk_free_rate/252
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    # 计算最大回撤
    rolling_max = results['portfolio_value'].expanding().max()
    drawdowns = results['portfolio_value'] / rolling_max - 1
    max_drawdown = drawdowns.min()
    
    # 计算胜率
    trade_returns = results['portfolio_value'].pct_change()
    winning_trades = len(trade_returns[trade_returns > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # 计算月度统计 - 使用'ME'替代'M'
    monthly_returns = results.set_index('date')['portfolio_value'].resample('ME').last().pct_change()
    best_month = monthly_returns.max()
    worst_month = monthly_returns.min()
    avg_month = monthly_returns.mean()
    monthly_std = monthly_returns.std()
    
    return {
        'initial_value': initial_value,
        'final_value': final_value,
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'buy_trades': buy_trades,
        'sell_trades': sell_trades,
        'best_month': best_month,
        'worst_month': worst_month,
        'avg_month': avg_month,
        'monthly_std': monthly_std
    }

def print_performance_report(metrics, strategy_name):
    """打印详细的性能报告"""
    print(f"\n=== {strategy_name} 策略绩效报告 ===")
    print(f"回测期间: {metrics['start_date']} 到 {metrics['end_date']}")
    print(f"初始资金: ${metrics['initial_value']:,.2f}")
    print(f"最终资金: ${metrics['final_value']:,.2f}")
    print(f"总收益率: {metrics['total_return']:.2%}")
    print(f"年化收益率: {metrics['annual_return']:.2%}")
    print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"胜率: {metrics['win_rate']:.2%}")
    print(f"总交易次数: {metrics['total_trades']}")
    print(f"买入交易: {metrics['buy_trades']}")
    print(f"卖出交易: {metrics['sell_trades']}")
    print("==================\n")
    print("月度统计:")
    print(f"最佳月度收益: {metrics['best_month']:.2%}")
    print(f"最差月度收益: {metrics['worst_month']:.2%}")
    print(f"平均月度收益: {metrics['avg_month']:.2%}")
    print(f"月度收益标准差: {metrics['monthly_std']:.2%}")
    print("==================")

def run_strategy(data, strategy_class, strategy_name):
    """运行单个策略的回测"""
    strategy = strategy_class(data)
    strategy.generate_signals()
    results = strategy.backtest()
    
    # 添加日期范围
    metrics = calculate_performance_metrics(results)
    metrics['start_date'] = results['date'].iloc[0].strftime('%Y-%m-%d')
    metrics['end_date'] = results['date'].iloc[-1].strftime('%Y-%m-%d')
    
    # 打印详细报告
    print_performance_report(metrics, strategy_name)
    
    return results, metrics

def main():
    # 获取数据
    data = fetch_tqqq_data()
    print(f"数据范围: {data.index[0]} 到 {data.index[-1]}")
    
    # 运行原始策略
    results_v1, metrics_v1 = run_strategy(data, TQQQStrategy, "原始")
    
    # 运行改进策略V2
    results_v2, metrics_v2 = run_strategy(data, TQQQStrategyV2, "改进V2")
    
    # 运行改进策略V3
    results_v3, metrics_v3 = run_strategy(data, TQQQStrategyV3, "改进V3")
    
    # 保存结果
    results_v1.to_csv('results/strategy_v1_results.csv')
    results_v2.to_csv('results/strategy_v2_results.csv')
    results_v3.to_csv('results/strategy_v3_results.csv')
    
    # 保存性能指标
    pd.DataFrame([metrics_v1, metrics_v2, metrics_v3], 
                index=['原始策略', '改进V2', '改进V3']).to_csv('results/performance_comparison.csv')

if __name__ == '__main__':
    main()
