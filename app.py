"""
Weather Prediction Web Service with LSTM Model
Version: 2.0
Author: Your Name
"""

# ============================== 导入依赖 ==============================
from datetime import datetime, timedelta
import os
import json
import numpy as np
import pandas as pd
import requests
import joblib
from flask import Flask, render_template, request, jsonify
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

# ============================== 应用初始化 ==============================
app = Flask(__name__)

# ============================== 全局配置 ==============================
API_KEY = os.environ.get("WEATHER_API_KEY", "your_default_api_key")  # 从环境变量获取
BASE_API_URL = "http://api.weatherapi.com/v1/history.json"
MODEL_PATH = "weather_lstm.keras"
SCALER_PATH = "scaler.save"
FEATURE_COLS = [
    "Temperature_C", 
    "Humidity_%", 
    "Is_Snowing",
    "Pressure_mb",
    "Wind_Speed_kph",
    "Visibility_km",
    "Wind_Bearing_deg"
]

# ============================== 模型和预处理加载 ==============================
def load_keras_model_with_fallback():
    """加载Keras模型并处理版本兼容性"""
    try:
        # 处理旧版batch_shape参数问题
        def _fix_input_layer(config):
            if "batch_shape" in config:
                config["input_shape"] = config["batch_shape"][1:]
                del config["batch_shape"]
            return type('InputLayer', (), {'from_config': lambda _, cfg: None})
        
        return load_model(
            MODEL_PATH,
            custom_objects={'InputLayer': _fix_input_layer},
            compile=False
        )
    except Exception as e:
        app.logger.error(f"模型加载失败: {str(e)}")
        raise

try:
    # 加载预处理工具
    scaler = joblib.load(SCALER_PATH)
    
    # 加载深度学习模型
    model = load_keras_model_with_fallback()
    
    # 验证模型输入形状
    expected_shape = (1, len(FEATURE_COLS))
    if model.input_shape[1:] != expected_shape:
        raise ValueError(
            f"模型输入形状不匹配！预期: {expected_shape}, 实际: {model.input_shape[1:]}"
        )
        
except Exception as e:
    print(f"❌ 系统初始化失败: {str(e)}")
    exit(1)

# ============================== 核心逻辑 ==============================
class WeatherDataFetcher:
    """天气数据获取与处理类"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        
    def _parse_hour_data(self, hour_data, current_time):
        """解析单小时数据"""
        try:
            time_str = hour_data["time"]
            hour_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            
            # 仅保留最近10小时数据
            if (current_time - hour_dt).total_seconds() > 3600 * 10:
                return None
                
            return {
                "Temperature_C": hour_data["temp_c"],
                "Humidity_%": hour_data["humidity"],
                "Is_Snowing": 1 if "snow" in hour_data["condition"]["text"].lower() else 0,
                "Pressure_mb": hour_data["pressure_mb"],
                "Wind_Speed_kph": hour_data["wind_kph"],
                "Visibility_km": hour_data["vis_km"],
                "Wind_Bearing_deg": hour_data["wind_degree"]
            }
        except KeyError as e:
            app.logger.warning(f"数据字段缺失: {str(e)}")
            return None
    
    def fetch(self, location):
        """获取指定位置的天气数据"""
        current_time = datetime.utcnow()
        weather_data = []
        
        # 计算需要请求的日期范围
        date_set = {
            (current_time - timedelta(hours=h)).strftime("%Y-%m-%d")
            for h in range(14)  # 覆盖14小时防止UTC日期变更
        }
        
        for date_str in date_set:
            try:
                response = requests.get(
                    f"{BASE_API_URL}?key={self.api_key}&q={location}&dt={date_str}",
                    timeout=15
                )
                response.raise_for_status()
                
                forecast_day = response.json()["forecast"]["forecastday"][0]
                for hour_data in forecast_day["hour"]:
                    parsed = self._parse_hour_data(hour_data, current_time)
                    if parsed:
                        weather_data.append(parsed)
                        
            except requests.exceptions.RequestException as e:
                app.logger.error(f"API请求失败: {str(e)}")
            except (KeyError, IndexError) as e:
                app.logger.error(f"数据解析失败: {str(e)}")
                
        return pd.DataFrame(weather_data)

class TemperaturePredictor:
    """温度预测引擎"""
    
    def __init__(self, model, scaler):
        self.model = model
        self.scaler = scaler
        
    def _validate_input(self, df):
        """验证输入数据有效性"""
        if df.empty:
            raise ValueError("输入数据为空")
        if len(df) < 5:
            raise ValueError("至少需要5个数据点")
        if not set(FEATURE_COLS).issubset(df.columns):
            missing = set(FEATURE_COLS) - set(df.columns)
            raise ValueError(f"缺失特征列: {missing}")
            
    def predict(self, df):
        """执行温度预测"""
        self._validate_input(df)
        
        # 数据预处理
        scaled = self.scaler.transform(df[FEATURE_COLS])
        reshaped = scaled.reshape((-1, 1, len(FEATURE_COLS)))
        
        # 模型预测
        predictions = self.model.predict(reshaped)
        
        # 反归一化（温度是第一列）
        dummy = np.zeros((len(predictions), scaled.shape[1]))
        dummy[:, 0] = predictions.flatten()
        return self.scaler.inverse_transform(dummy)[:, 0]

# ============================== 路由处理 ==============================
@app.route('/')
def home():
    """主页面"""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """预测接口"""
    try:
        # 参数解析
        data = request.get_json()
        if not data or 'location' not in data:
            return jsonify({"error": "缺少location参数"}), 400
            
        location = data['location'].strip()
        if not location:
            return jsonify({"error": "location不能为空"}), 400
            
        # 获取数据
        fetcher = WeatherDataFetcher(API_KEY)
        df = fetcher.fetch(location)
        
        # 执行预测
        predictor = TemperaturePredictor(model, scaler)
        temperatures = predictor.predict(df.tail(10))  # 使用最近10个点
        
        # 生成时间标签
        now = datetime.utcnow()
        time_labels = [
            (now + timedelta(hours=i+1)).strftime("%H:%M UTC")
            for i in range(len(temperatures))
        ]
        
        return jsonify({
            "location": location,
            "predictions": [round(t, 1) for t in temperatures],
            "timestamps": time_labels,
            "model_info": {
                "input_shape": model.input_shape,
                "features": FEATURE_COLS
            }
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"预测失败: {str(e)}", exc_info=True)
        return jsonify({"error": "内部服务器错误"}), 500

# ============================== 启动应用 ==============================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', False))