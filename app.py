from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import joblib
import requests
import pandas as pd
import numpy as np
import os
from flask import Flask, render_template, request, jsonify
import json
import torch
import torch.nn as nn

# ===============================
# 定义 PyTorch 模型结构 LSTMModel
# ===============================
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size=50, num_layers=2, output_size=1):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 25)
        self.fc2 = nn.Linear(25, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc1(out)
        out = self.fc2(out)
        return out

# ===============================
# 初始化 Flask 应用
# ===============================
app = Flask(__name__)
API_KEY = "a9e680c901b64650acd211526250304"
LOCATION = "Illinois"
base_url = "http://api.weatherapi.com/v1/history.json"
weather_data = []

# ===============================
# 获取最近10小时天气数据
# ===============================
now = datetime.now()
dates_needed = list(set([
    now.strftime("%Y-%m-%d"),
    (now - timedelta(hours=10)).strftime("%Y-%m-%d")
]))

for date_str in dates_needed:
    url = f"{base_url}?key={API_KEY}&q={LOCATION}&dt={date_str}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        continue

    if "forecast" in data:
        try:
            hour_data_list = data["forecast"]["forecastday"][0]["hour"]
            for hour_data in hour_data_list:
                time_str = hour_data["time"]
                hour_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                if 0 <= (now - hour_dt).total_seconds() <= 3600 * 10:
                    weather_data.append({
                        "Temperature_C": hour_data["temp_c"],
                        "Humidity_%": hour_data["humidity"],
                        "Is_Snowing": 1 if "snow" in hour_data["condition"]["text"].lower() else 0,
                        "Pressure_mb": hour_data["pressure_mb"],
                        "Wind_Speed_kph": hour_data["wind_kph"],
                        "Visibility_km": hour_data["vis_km"],
                        "Wind_Bearing_deg": hour_data["wind_degree"]
                    })
        except KeyError:
            print(f"数据结构异常: {data}")
            continue

if not weather_data:
    print("未获取到天气数据")
    exit()

df = pd.DataFrame(weather_data)
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df)
df_reshaped = df_scaled.reshape((df_scaled.shape[0], 1, df_scaled.shape[1]))  # (10, 1, 7)

# ===============================
# 加载模型（本地 PyTorch pkl）
# ===============================
MODEL_PATH = os.path.join(os.path.dirname(__file__), "weather_lstm_torch.pkl")
try:
    mc = joblib.load(MODEL_PATH)
    mc.eval()
    print("✅ 模型加载成功")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    exit()

# ===============================
# 反归一化函数
# ===============================
def inverse_scale_temp(scaled_temp, scaler, feature_index=0):
    dummy = np.zeros((scaled_temp.shape[0], df.shape[1]))
    dummy[:, feature_index] = scaled_temp.flatten()
    return scaler.inverse_transform(dummy)[:, feature_index].reshape(-1, 1)

# ===============================
# 天气预测函数
# ===============================
def predict_weather(df):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input df must be a pandas DataFrame")
    df_scaled = scaler.fit_transform(df)
    df_reshaped = df_scaled.reshape((df_scaled.shape[0], 1, df_scaled.shape[1]))
    input_tensor = torch.tensor(df_reshaped).float()
    with torch.no_grad():
        dapre = mc(input_tensor).numpy()
    result = inverse_scale_temp(dapre, scaler, feature_index=0)
    return result

# ===============================
# 路由：主页
# ===============================
@app.route('/')
def home():
    return render_template('index.html')

# ===============================
# 路由：预测接口
# ===============================
@app.route('/weather', methods=['POST'])
def weather():
    try:
        data = request.get_json()
        location = data['location']

        global LOCATION, weather_data
        LOCATION = location
        weather_data.clear()

        now = datetime.now()
        dates_needed = list(set([
            now.strftime("%Y-%m-%d"),
            (now - timedelta(hours=10)).strftime("%Y-%m-%d")
        ]))

        for date_str in dates_needed:
            url = f"{base_url}?key={API_KEY}&q={LOCATION}&dt={date_str}"
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                api_data = response.json()
            except (requests.RequestException, json.JSONDecodeError) as e:
                print(f"API请求失败: {e}")
                continue

            if "forecast" in api_data:
                try:
                    forecast_day = api_data["forecast"]["forecastday"][0]
                    for hour_data in forecast_day["hour"]:
                        time_str = hour_data["time"]
                        hour_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                        if 0 <= (now - hour_dt).total_seconds() <= 3600 * 10:
                            weather_data.append({
                                "Temperature_C": hour_data["temp_c"],
                                "Humidity_%": hour_data["humidity"],
                                "Is_Snowing": 1 if "snow" in hour_data["condition"]["text"].lower() else 0,
                                "Pressure_mb": hour_data["pressure_mb"],
                                "Wind_Speed_kph": hour_data["wind_kph"],
                                "Visibility_km": hour_data["vis_km"],
                                "Wind_Bearing_deg": hour_data["wind_degree"]
                            })
                except KeyError as e:
                    print(f"数据解析失败，缺失字段: {e}")
                    continue

        if not weather_data:
            return jsonify({"error": "未获取到有效天气数据，请检查API密钥或城市名称"}), 400

        df = pd.DataFrame(weather_data)
        try:
            predicted = predict_weather(df).flatten().tolist()
        except Exception as e:
            print(f"模型预测失败: {e}")
            return jsonify({"error": "温度预测失败"}), 500

        time_labels = []
        for i in range(10):
            start_time = now + timedelta(hours=i)
            end_time = start_time + timedelta(hours=1)
            day_suffix = "(次日)" if start_time.day != end_time.day else ""
            label = f"{start_time.strftime('%H:%M')} → {end_time.strftime('%H:%M')} {day_suffix}".strip()
            time_labels.append(label)

        return jsonify({
            "predicted_temperatures": [round(temp, 1) for temp in predicted],
            "time_labels": time_labels
        })

    except KeyError as e:
        return jsonify({"error": f"请求参数错误: {str(e)}"}), 400
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500

# ===============================
# 启动服务
# ===============================
if __name__ == '__main__':
    app.run(debug=True)
