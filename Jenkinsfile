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
                git 'https://github.com/jimmy-chen-1/ml_project.git'
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
                    pkill -f $APP_FILE || true
                    nohup $VENV_DIR/bin/python $APP_FILE > flask.log 2>&1 &
                    sleep 3
                    echo "✅ Flask 已启动"
                '''
            }
        }
    }

    post {
        success {
            echo '✅ 构建完成，网站部署成功！'
        }
        failure {
            echo '❌ 构建失败，请检查日志'
        }
    }
}

