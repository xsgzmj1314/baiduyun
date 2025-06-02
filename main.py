from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# 设置数据文件夹路径
DATA_FOLDER = 'data'
os.makedirs(DATA_FOLDER, exist_ok=True)


# 初始化示例数据
def init_sample_data():
    # 创建GDP预测数据
    gdp_data = {
        'date': ['2025-01-11', '2025-01-18', '2025-01-25', '2025-02-01', '2025-02-08',
                 '2025-02-15', '2025-02-22', '2025-03-01', '2025-03-08', '2025-03-15',
                 '2025-03-22', '2025-03-29', '2025-04-05', '2025-04-12', '2025-04-19',
                 '2025-04-26', '2025-05-03', '2025-05-10', '2025-05-17', '2025-05-24', '2025-05-25'],
        'forecast': [5.4, 5.4, 5.4, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.6, 5.6, 5.6, 5.5, 5.4, 5.3, 5.2,
                     5.2]
    }
    gdp_df = pd.DataFrame(gdp_data)
    gdp_df.to_excel(os.path.join(DATA_FOLDER, 'gdp_forecast.xlsx'), index=False)

    # 创建GDP分解数据
    decomposition_data = {
        'date': ['2025-01-11', '2025-01-25', '2025-02-08', '2025-02-22', '2025-03-08',
                 '2025-03-22', '2025-04-05', '2025-04-19', '2025-05-03', '2025-05-17', '2025-05-24'],
        'production': [2.2, 2.2, 2.2, 2.3, 2.3, 2.3, 2.4, 2.4, 2.4, 2.2, 2.1],
        'consumption': [1.8, 1.8, 1.8, 1.8, 1.8, 1.7, 1.7, 1.7, 1.7, 1.7, 1.8],
        'export': [0.7, 0.7, 0.7, 0.7, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7],
        'finance': [0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.7, 0.6]
    }
    decomposition_df = pd.DataFrame(decomposition_data)
    decomposition_df.to_excel(os.path.join(DATA_FOLDER, 'gdp_decomposition.xlsx'), index=False)

    # 创建季度实际GDP数据
    quarterly_data = {
        'date': ['2024Q4', '2025Q1'],
        'actual': [5.3, 5.4]
    }
    quarterly_df = pd.DataFrame(quarterly_data)
    quarterly_df.to_excel(os.path.join(DATA_FOLDER, 'quarterly_gdp.xlsx'), index=False)


# 确保示例数据存在
if not os.path.exists(os.path.join(DATA_FOLDER, 'gdp_forecast.xlsx')):
    init_sample_data()


# 读取数据文件
def read_data():
    try:
        gdp_df = pd.read_excel(os.path.join(DATA_FOLDER, 'gdp_forecast.xlsx'))
        decomposition_df = pd.read_excel(os.path.join(DATA_FOLDER, 'gdp_decomposition.xlsx'))
        quarterly_df = pd.read_excel(os.path.join(DATA_FOLDER, 'quarterly_gdp.xlsx'))

        # 转换日期格式
        gdp_df['date'] = gdp_df['date'].astype(str)
        decomposition_df['date'] = decomposition_df['date'].astype(str)
        quarterly_df['date'] = quarterly_df['date'].astype(str)

        return gdp_df, decomposition_df, quarterly_df
    except Exception as e:
        print(f"读取数据出错: {e}")
        # 返回空数据框
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# 首页路由
@app.route('/')
def index():
    gdp_df, decomposition_df, quarterly_df = read_data()

    # 获取最新预测值
    latest_forecast = gdp_df['forecast'].iloc[-1] if not gdp_df.empty else 0

    # 获取最后更新日期
    last_update = datetime.now().strftime('%Y-%m-%d')

    return render_template('index.html', latest_forecast=latest_forecast, last_update=last_update)


# API路由 - 获取GDP预测数据
@app.route('/api/gdp_forecast')
def get_gdp_forecast():
    gdp_df, decomposition_df, quarterly_df = read_data()

    # 准备折线图数据
    line_labels = []
    line_forecast = []
    line_actual = []

    # 添加季度实际数据
    for _, row in quarterly_df.iterrows():
        line_labels.append(row['date'])
        line_forecast.append(None)  # 季度时间点不显示预测值
        line_actual.append(row['actual'])

    # 添加预测数据
    for _, row in gdp_df.iterrows():
        # 检查是否已存在该日期（避免与季度数据重复）
        if row['date'] not in line_labels:
            line_labels.append(row['date'])
            line_forecast.append(row['forecast'])
            line_actual.append(None)  # 预测时间点不显示实际值

    # 准备堆叠柱状图数据
    bar_labels = decomposition_df['date'].tolist()
    bar_production = decomposition_df['production'].tolist()
    bar_consumption = decomposition_df['consumption'].tolist()
    bar_export = decomposition_df['export'].tolist()
    bar_finance = decomposition_df['finance'].tolist()

    return jsonify({
        'line': {
            'labels': line_labels,
            'forecast': line_forecast,
            'actual': line_actual
        },
        'bar': {
            'labels': bar_labels,
            'production': bar_production,
            'consumption': bar_consumption,
            'export': bar_export,
            'finance': bar_finance
        }
    })


# API路由 - 上传新数据
@app.route('/api/upload', methods=['POST'])
def upload_data():
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '未找到上传的文件'}), 400

        file = request.files['file']

        # 检查文件是否有名称
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': '请上传Excel文件'}), 400

        # 保存文件
        file_path = os.path.join(DATA_FOLDER, 'new_data.xlsx')
        file.save(file_path)

        # 这里可以添加数据处理逻辑
        # 例如，读取上传的Excel文件，处理数据，然后更新现有数据文件

        return jsonify({'message': '数据上传成功'}), 200

    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=80)