import pandas as pd
from lightweight_charts import Chart


def get_bar_data(symbol, timeframe):
    if symbol not in ( 'TSLA'):
    #if symbol not in ('AAPL', 'GOOGL', 'TSLA'):
        print(f'No data for "{symbol}"')
        return pd.DataFrame()

    # 读取数据并优化性能
    df = pd.read_csv(f'bar_data/{symbol}_{timeframe}.csv')
    return optimize_data(df)


def on_search(chart, searched_string):  # Called when the user searches.
    print(f"搜索股票: {searched_string}")
    new_data = get_bar_data(searched_string, chart.topbar['timeframe'].value)
    if new_data.empty:
        return
    chart.topbar['symbol'].set(searched_string)
    chart.set(new_data)

    # 更新自定义成交量
    update_custom_volume(chart, new_data)


def on_timeframe_selection(chart):  # Called when the user changes the timeframe.
    print(f"切换时间框架: {chart.topbar['timeframe'].value}")
    new_data = get_bar_data(chart.topbar['symbol'].value, chart.topbar['timeframe'].value)
    if new_data.empty:
        return
    chart.set(new_data, True)

    # 更新自定义成交量
    update_custom_volume(chart, new_data)


def on_horizontal_line_move(chart, line):
    print(f'Horizontal line moved to: {line.price}')


def optimize_data(df):
    """优化数据以提高性能"""
    if df.empty:
        return df

    # 限制数据量，只保留最近50条记录
    if len(df) > 50:
        df = df.tail(50).copy()
        print(f"数据已优化：保留最近50条记录")

    # 确保时间列格式正确
    if 'date' in df.columns:
        df = df.rename(columns={'date': 'time'})

    # 移除不必要的列
    required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
    df = df[[col for col in required_cols if col in df.columns]]

    return df


def create_custom_volume_data(df):
    """创建自定义成交量数据，以万为单位，根据涨跌设置颜色"""
    if df.empty or 'volume' not in df.columns:
        return pd.DataFrame()

    # 重置索引以确保连续性
    df_reset = df.reset_index(drop=True)

    volume_data = []
    for i in range(len(df_reset)):
        row = df_reset.iloc[i]

        # 计算成交量（以万为单位）
        volume_in_wan = row['volume'] / 10000

        # 判断涨跌：当前收盘价与前一根K线收盘价比较
        if i > 0:
            prev_close = df_reset.iloc[i-1]['close']
            is_up = row['close'] > prev_close
        else:
            # 第一根K线，与开盘价比较
            is_up = row['close'] > row['open']

        # 根据涨跌设置颜色
        color = '#ED6160' if is_up else '#888888'

        volume_data.append({
            'time': row['time'],
            '成交量(万)': volume_in_wan,
            'color': color
        })

    return pd.DataFrame(volume_data)


def update_custom_volume(chart, df):
    """更新自定义成交量数据"""
    if hasattr(chart, '_custom_volume_histogram'):
        custom_volume_data = create_custom_volume_data(df)
        if not custom_volume_data.empty:
            chart._custom_volume_histogram.set(custom_volume_data)
            print("自定义成交量已更新")


if __name__ == '__main__':
    print("正在初始化图表...")

    # 优化：关闭调试模式和工具箱以提高性能
    chart = Chart(debug=False, toolbox=False)

    # 空心K线样式：透明填充，保留边框和蜡烛芯（在数据加载前设置）
    chart.candle_style(
        up_color='rgba(0, 255, 85, 0)',  # 上涨K线填充透明
        down_color='rgba(237, 72, 7, 0)',  # 下跌K线填充透明
        border_enabled=True,  # 启用边框
        border_up_color='#ED6160',  # 上涨边框颜色
        border_down_color='#888888',  # 下跌边框颜色
        wick_enabled=True,  # 启用蜡烛芯
        wick_up_color='#ED6160',  # 上涨蜡烛芯颜色
        wick_down_color='#888888'  # 下跌蜡烛芯颜色
    )

    # 设置成交量颜色，与K线颜色保持一致
    chart.volume_config(
        up_color='#ED6160',  # 上涨成交量颜色
        down_color='#888888'  # 下跌成交量颜色
    )

    # 启用图例以显示OHLC价格和涨幅信息
    chart.legend(
        visible=True,           # 显示图例
        ohlc=True,             # 显示开盘价、最高价、最低价、收盘价
        percent=True,          # 显示涨跌幅百分比
        lines=True,            # 显示线条信息
        color='#FFFFFF',       # 图例文字颜色（白色）
        font_size=12,          # 字体大小
        font_family='Arial',   # 字体
        color_based_on_candle=True  # 根据K线颜色显示涨跌幅
    )

    chart.events.search += on_search

    chart.topbar.textbox('symbol', 'TSLA')
    chart.topbar.switcher('timeframe', ('1min', '5min', '30min'), default='5min',
                          func=on_timeframe_selection)

    print("正在加载数据...")
    df = get_bar_data('TSLA', '5min')
    print(f"数据加载完成，共 {len(df)} 条记录")
    chart.set(df)

    # 创建自定义成交量直方图（以万为单位，动态颜色）
    print("正在创建自定义成交量...")
    volume_histogram = chart.create_histogram(
        name='成交量(万)',
        color='#ED6160',  # 默认颜色，实际颜色由数据中的color列决定
        price_line=False,
        price_label=False,
        scale_margin_top=0.8,
        scale_margin_bottom=0.0
    )

    # 保存引用以便在回调函数中使用
    chart._custom_volume_histogram = volume_histogram

    # 生成自定义成交量数据
    custom_volume_data = create_custom_volume_data(df)
    if not custom_volume_data.empty:
        volume_histogram.set(custom_volume_data)
        print("自定义成交量设置完成")

    chart.horizontal_line(200, func=on_horizontal_line_move)

    print("正在显示图表...")
    chart.show(block=True)
