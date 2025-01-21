import pandas as pd
from datetime import datetime, timedelta

def fetch_tqqq_data():
    """
    从本地tqqq.csv文件读取TQQQ的数据
    Returns:
        pd.DataFrame: TQQQ的历史数据，包含开高低收成交量等信息
    """
    try:
        # 从本地CSV文件读取数据，指定日期格式
        data = pd.read_csv('data/tqqq.csv', parse_dates=['dt'])
        
        # 设置日期索引
        data.set_index('dt', inplace=True)
        
        # 删除symbol列，因为都是TQQQ
        if 'symbol' in data.columns:
            data = data.drop('symbol', axis=1)
        
        # 确保所有必需的列都存在
        required_columns = ['open', 'high', 'low', 'close', 'avg']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise Exception(f"数据缺少必需的列: {missing_columns}")
        
        # 按日期排序
        data = data.sort_index()
        
        print("数据读取成功，列名:", list(data.columns))
        print(f"数据范围: {data.index.min()} 到 {data.index.max()}")
        
    except Exception as e:
        print(f"读取本地数据失败: {e}")
        raise Exception("无法读取TQQQ数据")
    
    return data

if __name__ == "__main__":
    # 测试数据获取
    data = fetch_tqqq_data()
    print("\n数据前5行:")
    print(data.head()) 