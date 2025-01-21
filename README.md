# Quant Backtest

A sophisticated quantitative trading backtesting framework focused on TQQQ trading strategies.

## 项目概述 (Project Overview)

这个项目是一个量化交易回测系统，专门用于测试和评估 TQQQ (3x leveraged Nasdaq-100 ETF) 的交易策略。系统包含多个交易策略版本，并提供详细的性能分析和可视化结果。

The project is a quantitative trading backtesting system specifically designed for testing and evaluating trading strategies for TQQQ (3x leveraged Nasdaq-100 ETF). It includes multiple strategy versions and provides detailed performance analysis with visualization.

## 功能特点 (Features)

- 多个 TQQQ 交易策略实现
- 完整的回测框架
- 详细的性能指标计算
  - 总收益率和年化收益率
  - 夏普比率
  - 最大回撤
  - 交易胜率
  - 月度统计数据
- 结果可视化
  - 回测结果图表
  - 月度收益热力图
  - 性能对比分析

## 项目结构 (Project Structure)

```
quant-backtest/
├── backtester/         # 回测引擎核心代码
├── data/               # 数据获取和处理模块
├── strategies/         # 交易策略实现
├── results/           # 回测结果和图表
├── main.py            # 主程序入口
└── requirements.txt   # 项目依赖
```

## 环境要求 (Requirements)

- Python 3.8+
- 依赖包：
  - pandas
  - numpy
  - matplotlib
  - yfinance
  - statsmodels
  - scipy
  - beautifulsoup4

## 安装步骤 (Installation)

1. 克隆项目仓库：
```bash
git clone https://github.com/yourusername/quant-backtest.git
cd quant-backtest
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法 (Usage)

1. 运行回测：
```bash
python main.py
```

2. 查看结果：
回测结果将保存在 `results` 目录下，包括：
- 回测性能图表
- 月度收益热力图
- 性能指标CSV文件

## 许可证 (License)

MIT License

## 免责声明 (Disclaimer)

本项目仅供学习和研究使用，不构成投资建议。使用本系统进行实际交易需自行承担风险。
