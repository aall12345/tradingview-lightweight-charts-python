import pandas as pd
from lightweight_charts import Chart


def get_bar_data(symbol, timeframe):
    """获取股票数据并进行性能优化"""
    if symbol not in ('TSLA', 'AAPL', 'GOOGL'):
        print(f'No data for "{symbol}"')
        return pd.DataFrame()
    
    print(f"正在加载 {symbol} {timeframe} 数据...")
    
    # 读取数据
    df = pd.read_csv(f'bar_data/{symbol}_{timeframe}.csv')
    
    # 立即进行数据优化
    return optimize_data(df)


def optimize_data(df):
    """优化数据以提高性能"""
    if df.empty:
        return df
    
    # 限制数据量 - 根据数据大小动态调整
    max_records = 300  # 进一步减少数据量以提高性能
    if len(df) > max_records:
        df = df.tail(max_records).copy()
        print(f"数据已优化：保留最近{max_records}条记录（原始数据{len(df) + (len(df) - max_records)}条）")
    
    # 确保时间列格式正确
    if 'date' in df.columns:
        df = df.rename(columns={'date': 'time'})
    
    # 只保留必要的列，移除索引列
    required_cols = ['time', 'open', 'high', 'low', 'close']
    # 如果有volume列且需要，可以保留
    if 'volume' in df.columns:
        required_cols.append('volume')
    
    # 过滤列并重置索引
    df = df[[col for col in required_cols if col in df.columns]].reset_index(drop=True)
    
    # 移除可能的重复列（如Unnamed: 0）
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    return df


def on_search(chart, searched_string):
    """搜索回调函数"""
    print(f"搜索股票: {searched_string}")
    
    # 显示加载状态
    new_data = get_bar_data(searched_string, chart.topbar['timeframe'].value)
    if new_data.empty:
        print(f"未找到 {searched_string} 的数据")
        return
    
    chart.topbar['symbol'].set(searched_string)
    chart.set(new_data)
    print(f"已切换到 {searched_string}")


def on_timeframe_selection(chart):
    """时间框架切换回调函数"""
    symbol = chart.topbar['symbol'].value
    timeframe = chart.topbar['timeframe'].value
    print(f"切换时间框架: {symbol} -> {timeframe}")
    
    new_data = get_bar_data(symbol, timeframe)
    if new_data.empty:
        print(f"未找到 {symbol} {timeframe} 的数据")
        return
    
    chart.set(new_data, True)
    print(f"时间框架已切换到 {timeframe}")


def on_horizontal_line_move(chart, line):
    """水平线移动回调函数"""
    print(f'水平线移动到: {line.price}')


if __name__ == '__main__':
    print("=== 启动优化版本的TradingView图表 ===")
    print("正在初始化图表...")
    
    # 创建图表 - 移除所有可能影响性能的功能
    chart = Chart(
        toolbox=False,      # 禁用工具箱以提高性能
        width=1200,         # 设置合适的窗口大小
        height=800,
        title="优化版K线图"
    )
    
    # 禁用图例以进一步提高性能
    # chart.legend(False)  # 如果有这个方法的话
    
    print("正在配置图表样式...")


    
    # 设置空心K线样式
    chart.candle_style(
        up_color='rgba(0, 255, 85, 0)',      # 上涨K线填充透明
        down_color='rgba(255, 82, 82, 0)',   # 下跌K线填充透明
        border_enabled=True,                  # 启用边框
        border_up_color='#ED6160',           # 上涨边框颜色
        border_down_color='#888888',         # 下跌边框颜色
        wick_enabled=True,                   # 启用蜡烛芯
        wick_up_color='#ED6160',             # 上涨蜡烛芯颜色
        wick_down_color='#888888'            # 下跌蜡烛芯颜色
    )

    # 设置成交量颜色，与K线颜色保持一致
    chart.volume_config(
        up_color='#ED6160',                  # 上涨成交量颜色
        down_color='#888888'                 # 下跌成交量颜色
    )
    
    print("正在设置回调函数...")
    
    # 设置事件回调
    chart.events.search += on_search
    
    # 设置顶部工具栏
    chart.topbar.textbox('symbol', 'TSLA')
    chart.topbar.switcher('timeframe', ('1min', '5min', '30min'), 
                         default='5min', func=on_timeframe_selection)
    
    print("正在加载初始数据...")
    
    # 加载初始数据
    initial_data = get_bar_data('TSLA', '5min')
    if not initial_data.empty:
        print(f"初始数据加载完成，共 {len(initial_data)} 条记录")
        chart.set(initial_data)
    else:
        print("警告：初始数据加载失败")
    
    # 添加水平线
    chart.horizontal_line(200, func=on_horizontal_line_move)
    
    # 显示图表
    chart.show(block=True)
