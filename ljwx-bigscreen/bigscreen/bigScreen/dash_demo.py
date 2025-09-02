import pymysql
import pandas as pd
from dash import Dash, dash_table, html
import dash_bootstrap_components as dbc

# 数据库连接配置

db_config = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'database': 'watch_admin',
    'port': 3306
}


# 查询 MySQL 数据
query = """
SELECT 
    id AS ID,
    alert_type AS AlertType,
    device_sn AS DeviceSN,
    alert_timestamp AS Timestamp,
    alert_desc AS Description,
    severity_level AS SeverityLevel,
    alert_status AS Status
FROM t_alert_info
"""

# 连接到数据库并读取数据
def fetch_data():
    conn = pymysql.connect(**db_config)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# 获取数据
df = fetch_data()

# 创建 Dash 应用
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# 定义表格组件
table = dash_table.DataTable(
    data=df.to_dict('records'),  # 将 DataFrame 转换为字典格式
    columns=[{"name": col, "id": col} for col in df.columns],  # 定义列
    style_table={'height': '500px', 'overflowY': 'auto'},  # 表格滚动
    style_header={
        'backgroundColor': '#1f1f1f',  # 表头背景色
        'color': 'white',
        'fontWeight': 'bold',
        'border': '1px solid #444'  # 表头边框
    },
    style_cell={
        'backgroundColor': '#2e2e2e',  # 单元格背景色
        'color': 'white',
        'textAlign': 'center',  # 居中显示
        'border': '1px solid #444',
        'padding': '10px'
    },
    style_data_conditional=[
        # 根据状态设置单元格颜色
        {
            'if': {'filter_query': '{Status} = "pending"'},
            'backgroundColor': '#FFBF00',
            'color': 'black'
        },
        {
            'if': {'filter_query': '{Status} = "active"'},
            'backgroundColor': '#00C851',
            'color': 'white'
        },
        {
            'if': {'filter_query': '{Status} = "danger"'},
            'backgroundColor': '#ff4444',
            'color': 'white'
        }
    ]
)

# 定义页面布局
app.layout = dbc.Container(
    [
        html.H1("Alert Information Table", className="text-center text-white mb-4"),
        table
    ],
    fluid=True
)

# 启动 Dash 服务
if __name__ == '__main__':
    app.run_server(debug=True)