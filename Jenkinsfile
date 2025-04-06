pipeline {
    agent any

    environment {
        APP_FILE = 'app.py'
        VENV_DIR = 'venv'
        PORT = '5000'
        PYTHON_VERSION = '3.10.13'
        PYENV_ROOT = "${HOME}/.pyenv"
    }

    stages {
        stage('拉取代码') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/jimmy-chen-1/ml_project.git'
            }
        }

        stage('初始化 pyenv 和 Python 环境') {
            steps {
                sh '''
                    export PYENV_ROOT="$PYENV_ROOT"
                    export PATH="$PYENV_ROOT/bin:$PATH"
                    eval "$(pyenv init --path)"
                    eval "$(pyenv init -)"

                    # 确保 Python 3.10.13 已安装
                    pyenv versions | grep $PYTHON_VERSION || pyenv install $PYTHON_VERSION

                    # 切换 Python 版本
                    pyenv global $PYTHON_VERSION

                    echo "✅ 当前 Python 版本："
                    python3 --version
                '''
            }
        }

        stage('创建虚拟环境 & 安装依赖') {
            steps {
                sh '''
                    export PYENV_ROOT="$PYENV_ROOT"
                    export PATH="$PYENV_ROOT/bin:$PATH"
                    eval "$(pyenv init --path)"
                    eval "$(pyenv init -)"
                    pyenv global $PYTHON_VERSION

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
                    echo "✅ Flask 已启动，监听端口 $PORT"
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
