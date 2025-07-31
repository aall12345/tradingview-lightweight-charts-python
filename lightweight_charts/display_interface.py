import pandas as pd
from lightweight_charts import Chart
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

# 数据库连接配置
def get_mysql_connection_string():
    """获取MySQL连接字符串"""
    # 请根据您的实际数据库配置修改以下参数
    driver = 'pymysql'
    username = 'root'
    password = 'Yjeeqg.0'
    host = 'localhost'
    port = 3390
    dbname = 'analysis_system'
    charset = 'utf8mb4'

    return f"mysql+{driver}://{username}:{password}@{host}:{port}/{dbname}?charset={charset}"

def resample_data_to_timeframe(df, timeframe):
    """
    将数据重采样到指定的时间周期

    参数:
    df: 原始数据DataFrame
    timeframe: 目标时间周期 ('day', 'week', 'month')

    返回:
    DataFrame: 重采样后的数据
    """
    if df.empty:
        return df

    # 时间周期映射
    period_map = {
        '1hour':'H', #1小时
        'day': 'D',      # 日线
        'week': 'W',     # 周线
        'month': 'ME'    # 月线
    }

    if timeframe not in period_map:
        print(f"不支持的时间周期: {timeframe}")
        return df

    # 如果是日线，直接返回原数据（假设原数据就是日线）
    if timeframe == 'day':
        return df

    # 创建副本并设置时间索引
    df_copy = df.copy()
    df_copy['time'] = pd.to_datetime(df_copy['time'])
    df_copy.set_index('time', inplace=True)

    # 聚合规则
    agg_dict = {
        'open': 'first',    # 开盘价：第一个值
        'high': 'max',      # 最高价：最大值
        'low': 'min',       # 最低价：最小值
        'close': 'last',    # 收盘价：最后一个值
        'volume': 'sum'     # 成交量：总和
    }

    # 执行重采样
    resampled = df_copy.resample(period_map[timeframe]).agg(agg_dict)

    # 移除空值行
    resampled = resampled.dropna()

    # 重置索引
    resampled.reset_index(inplace=True)

    # 添加symbol列（如果原数据有的话）
    if 'symbol' in df.columns:
        resampled['symbol'] = df['symbol'].iloc[0]

    print(f"数据重采样完成: {len(df)} 条 -> {len(resampled)} 条 ({timeframe})")
    return resampled

def get_available_symbols(local_session):
    """获取数据库中所有可用的symbol列表"""
    try:
        query = text("SELECT DISTINCT symbol FROM market_data WHERE symbol IS NOT NULL ORDER BY symbol")
        result = local_session.execute(query)
        symbols = [row[0] for row in result.fetchall()]
        return symbols
    except Exception as e:
        print(f"获取symbol列表失败: {e}")
        return ['btcusdt', 'ethusdt']  # 返回默认列表


def search_symbols(search_text, available_symbols):
    """根据搜索文本匹配symbol"""
    if not search_text:
        return available_symbols[:10]  # 返回前10个

    search_text = search_text.lower()
    # 精确匹配优先
    exact_matches = [s for s in available_symbols if s.lower() == search_text]
    # 前缀匹配
    prefix_matches = [s for s in available_symbols if s.lower().startswith(search_text) and s.lower() != search_text]
    # 包含匹配
    contains_matches = [s for s in available_symbols if search_text in s.lower() and not s.lower().startswith(search_text)]

    # 合并结果，限制返回数量
    matches = exact_matches + prefix_matches + contains_matches
    return matches[:20]  # 最多返回20个匹配结果


def get_bar_data(symbol, timeframe, local_session=None):
    """获取指定symbol的K线数据"""
    # 获取可用symbol列表
    available_symbols = get_available_symbols(local_session)

    # 检查symbol是否存在
    if symbol not in available_symbols:
        print(f'数据库中没有找到symbol: "{symbol}"')
        # 尝试模糊匹配
        matches = search_symbols(symbol, available_symbols)
        if matches:
            print(f'建议的symbol: {matches[:5]}')
        return pd.DataFrame()

    try:
        query = text(
            f"select *from (select  symbol,time,open,high,low,close,vol from market_data where symbol= '{symbol}' order by time desc  ) a order by time asc")
        result = local_session.execute(query)

        # 转换为DataFrame
        market_data = pd.DataFrame(result.fetchall())
        if not market_data.empty:
            market_data.columns = result.keys()

        # 检查数据是否为空
        if market_data is None or market_data.empty:
            print(f"获取股票数据为空: {symbol}")
            return pd.DataFrame()  # 返回空的DataFrame

        # 优化数据
        df = optimize_data(market_data)

        # 根据时间周期进行重采样
        resampled_df = resample_data_to_timeframe(df, timeframe)

        return resampled_df

    except Exception as e:
        print(f"获取数据时出错: {e}")
        return pd.DataFrame()


def on_search(chart, searched_string):  # Called when the user searches.
    """处理用户搜索请求"""
    print(f"🔍 搜索symbol: {searched_string}")

    # 获取可用symbol列表
    available_symbols = get_available_symbols(chart._db_session)

    # 如果搜索字符串为空，显示可用symbol提示
    if not searched_string.strip():
        print("📋 可用的symbol示例:")
        for i, symbol in enumerate(available_symbols[:10]):
            print(f"  {i+1}. {symbol}")
        return

    # 尝试精确匹配
    searched_string = searched_string.strip()
    if searched_string in available_symbols:
        # 找到精确匹配: {searched_string}
        new_data = get_bar_data(searched_string, chart.topbar['timeframe'].value, chart._db_session)
        if not new_data.empty:
            chart.topbar['symbol'].set(searched_string)
            chart.set(new_data)
            update_custom_volume(chart, new_data)
        else:
            print(f"❌ {searched_string} 没有可用数据")
        return

    # 模糊匹配
    matches = search_symbols(searched_string, available_symbols)
    if matches:
        print(f"🔍 找到 {len(matches)} 个匹配的symbol:")
        for i, match in enumerate(matches[:10]):  # 只显示前10个
            print(f"  {i+1}. {match}")

        # 自动选择第一个匹配项
        best_match = matches[0]
        print(f"🎯 自动选择最佳匹配: {best_match}")
        new_data = get_bar_data(best_match, chart.topbar['timeframe'].value, chart._db_session)
        if not new_data.empty:
            chart.topbar['symbol'].set(best_match)
            chart.set(new_data)
            update_custom_volume(chart, new_data)
            print(f"📊 已加载 {best_match} 的数据，共 {len(new_data)} 条记录")
        else:
            print(f"❌ {best_match} 没有可用数据")
    else:
        print(f"❌ 没有找到匹配 '{searched_string}' 的symbol")
        print("💡 提示: 请尝试输入完整的symbol名称，例如: btcusdt, ethusdt")


def on_timeframe_selection(chart):  # Called when the user changes the timeframe.
    timeframe = chart.topbar['timeframe'].value
    symbol = chart.topbar['symbol'].value

    # 获取重采样后的数据
    new_data = get_bar_data(symbol, timeframe, chart._db_session)

    if new_data.empty:
        print(f"❌ 没有获取到 {timeframe} 数据")
        return

    print(f"✅ 成功获取 {timeframe} 数据: {len(new_data)} 条记录")

    # 显示数据范围信息
    if not new_data.empty:
        start_date = new_data['time'].min()
        end_date = new_data['time'].max()
        print(f"📅 数据时间范围: {start_date} 到 {end_date}")

    # 更新图表数据
    chart.set(new_data, True)

    # 更新自定义成交量
    update_custom_volume(chart, new_data)


def on_horizontal_line_move(chart, line):
    print(f'Horizontal line moved to: {line.price}')


def on_show_symbols_hotkey(chart):
    """快捷键回调：显示可用symbol列表"""
    print("\n" + "🔥 快捷键触发 - 显示symbol列表")
    show_available_symbols(chart._db_session)


def optimize_data(df):
    """优化数据以提高性能"""
    if df.empty:
        return df

    # 确保时间列格式正确
    if 'date' in df.columns:
        df = df.rename(columns={'date': 'time'})

    # 确保时间列是datetime类型（让图表库自动处理格式化）
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])

    # 将vol列重命名为volume，以便与图表库兼容
    if 'vol' in df.columns:
        df = df.rename(columns={'vol': 'volume'})

    # 确保数值列的数据类型正确
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

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


def show_available_symbols(session):
    """显示可用的symbol列表"""
    print("\n" + "="*50)
    available_symbols = get_available_symbols(session)

    # 按类型分组显示
    crypto_symbols = [s for s in available_symbols if 'usdt' in s.lower() or 'btc' in s.lower() or 'eth' in s.lower()]
    stock_symbols = [s for s in available_symbols if s not in crypto_symbols]


    print(f"\n\n💡 使用方法:")
    print("  🔍 搜索功能:")
    print("    1. 在图表界面按任意字母或数字键打开搜索框")
    print("    2. 输入symbol名称（支持模糊搜索）")
    print("    3. 按回车键确认搜索")
    print("    4. 按ESC键取消搜索")
    print("  ⌨️  快捷键:")
    print("    • Ctrl+L: 重新显示symbol列表")
    print("="*50)


if __name__ == '__main__':
    print("正在初始化图表...")

    # 创建数据库连接
    print("正在连接数据库...")
    engine = create_engine(get_mysql_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    # 显示可用的symbol列表
    show_available_symbols(session)

    # 优化：关闭调试模式和工具箱以提高性能
    chart = Chart(debug=False, toolbox=False)

    # 将数据库会话保存到chart对象中，供回调函数使用
    chart._db_session = session

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

    # 配置时间轴和十字线的时间显示格式为年月日
    chart.run_script(f'''
    {chart.id}.chart.applyOptions({{
        localization: {{
            timeFormatter: (time) => {{
                const date = new Date(time * 1000);
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${{year}}-${{month}}-${{day}}`;
            }}
        }},
        timeScale: {{
            timeVisible: true,
            secondsVisible: false,
            borderVisible: true,
            tickMarkFormatter: (time) => {{
                const date = new Date(time * 1000);
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${{year}}-${{month}}-${{day}}`;
            }}
        }},
        crosshair: {{
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: {{
                labelBackgroundColor: 'rgb(46, 46, 46)'
            }},
            horzLine: {{
                labelBackgroundColor: 'rgb(55, 55, 55)'
            }}
        }}
    }});
    ''')

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

    chart.topbar.textbox('symbol', 'btcusdt' )
    chart.topbar.switcher('timeframe', ( '1hour' ,'day','week','month'), default='day',
                          func=on_timeframe_selection)

    print("正在加载数据...")
    df = get_bar_data('btcusdt', 'day', session)
    print(f"数据加载完成，共 {len(df)} 条记录")
    chart.set(df)

    print("使用内置成交量显示")

    chart.horizontal_line(200, func=on_horizontal_line_move)

    print("正在显示图表...")
    try:
        chart.show(block=True)
        print("图表已关闭")
    except KeyboardInterrupt:
        print("用户中断程序")
    except Exception as e:
        print(f"显示图表时出错: {e}")
    finally:
        # 确保数据库会话被正确关闭
        print("正在关闭数据库连接...")
        session.close()
