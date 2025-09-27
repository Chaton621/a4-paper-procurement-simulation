import os
import pandas as pd
import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output

# 文件路径设置
analysis_folder = r"D:\Pycharm\Python大作业\analysis"
summary_csv = os.path.join(analysis_folder, "summary_statistics.csv")
low_price_days_csv = os.path.join(analysis_folder, "overall_low_price_days.csv")

# 读取数据
summary_df = pd.read_csv(summary_csv)
low_price_df = pd.read_csv(low_price_days_csv)
product_names = summary_df['商品'].tolist()

# 启动 Dash 应用
app = dash.Dash(__name__)
app.title = "商品价格分析可视化"

app.layout = html.Div([
    html.H1("商品价格分析仪表盘", style={'textAlign': 'center'}),

    dcc.Tabs([
        dcc.Tab(label="整体价格分布分析", children=[
            html.Div([
                html.H3("商品价格统计指标对比", style={'marginTop': 20}),
                dcc.Dropdown(
                    id="metric-selector",
                    options=[
                        {"label": "均值价格", "value": "均值价格"},
                        {"label": "中位数价格", "value": "中位数价格"},
                        {"label": "价格标准差", "value": "价格标准差"}
                    ],
                    value="均值价格"
                ),
                dcc.Graph(id="overall-bar-chart"),

                html.H3("商品价格箱线图对比", style={'marginTop': 40}),
                dcc.Graph(id="boxplot-comparison")
            ])
        ]),

        dcc.Tab(label="商品个体趋势分析", children=[
            html.Div([
                html.H3("选择商品查看趋势："),
                dcc.Dropdown(
                    id="product-selector",
                    options=[{"label": name, "value": name} for name in product_names],
                    value=product_names[0]
                ),
                html.Img(id="trend-image", style={"width": "90%", "marginTop": 20}),
                html.Img(id="fft-image", style={"width": "90%", "marginTop": 20})
            ])
        ]),

        dcc.Tab(label="整体低价时间分析", children=[
            html.Div([
                html.H3("大多数商品价格低的日期"),
                dcc.Graph(
                    figure=px.bar(low_price_df, x='日期', y='出现次数',
                                  title="整体低价商品集中天数",
                                  labels={'日期': '日期', '出现次数': '低价商品数量'})

                )
            ])
        ])
    ])
])

# 柱状图更新
@app.callback(
    Output("overall-bar-chart", "figure"),
    Input("metric-selector", "value")
)
def update_bar_chart(selected_metric):
    fig = px.bar(summary_df, x='商品', y=selected_metric,
                 title=f"{selected_metric} 对比",
                 labels={'商品': '商品名称', selected_metric: selected_metric})
    fig.update_layout(xaxis_tickangle=-45)
    return fig

# 箱线图（假设你未来想拓展为价格分布原始数据合并，先做静态示例）
@app.callback(
    Output("boxplot-comparison", "figure"),
    Input("metric-selector", "value")  # 仅触发即可，不依赖 metric
)
def update_boxplot(_):
    # 模拟数据或从每个文件夹中取中位数生成箱型图
    fig = go.Figure()
    for name in product_names:
        # 尝试读取该商品的清洗文件
        csv_path = os.path.join(r"D:\Pycharm\Python大作业\cleaned", f"{name}_cleaned.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df['price_价格'] = pd.to_numeric(df['price_价格'], errors='coerce')
            fig.add_trace(go.Box(y=df['price_价格'], name=name, boxmean='sd'))
    fig.update_layout(title="各商品价格箱线图")
    return fig

# 图片展示（趋势图 + FFT图）
@app.callback(
    Output("trend-image", "src"),
    Output("fft-image", "src"),
    Input("product-selector", "value")
)
def update_images(product_name):
    trend_path = os.path.join(analysis_folder, product_name, "price_trend.png")
    fft_path = os.path.join(analysis_folder, product_name, "fourier_spectrum.png")

    trend_uri = f"data:image/png;base64,{base64_image(trend_path)}"
    fft_uri = f"data:image/png;base64,{base64_image(fft_path)}"
    return trend_uri, fft_uri

# 辅助函数：将图片转为 base64 显示
import base64
def base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# 启动服务
if __name__ == '__main__':
    app.run(debug=True)

