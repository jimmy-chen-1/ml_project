pipeline {
    agent any

    environment {
        APP_FILE = 'app.py'
        VENV_DIR = 'venv'
        PORT = '5000'
    }

    stages {
        stage('拉取代码') {
            steps {
                git 'https://github.com/你的用户名/你的仓库名.git'  // ⬅️ 请替换为你的 GitHub 地址
            }
        }

        stage('创建虚拟环境 & 安装依赖') {
            steps {
                sh '''
                    python3 -m venv $VENV_DIR
                    source $VENV_DIR/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('检查模型文件是否存在') {
            steps {
                sh '''
                    if [ ! -f weather_lstm.pkl ]; then
                        echo "❌ 模型文件未找到，构建终止"
                        exit 1
                    fi
                '''
            }
        }

        stage('启动 Flask 应用') {
            steps {
                sh '''
                    pkill -f $APP_FILE || true  # 先尝试关闭之前的 Flask 实例
                    nohup $VENV_DIR/bin/python $APP_FILE > flask.log 2>&1 &
                    sleep 3  # 给 Flask 一点时间启动
                    echo "✅ Flask 已启动，监听端口 $PORT"
                '''
            }
        }
    }

    post {
        success {
            echo '✅ 项目部署成功！访问地址：http://<服务器IP>:5000/'
        }
        failure {
            echo '❌ 构建失败，请查看日志'
        }
    }
}
