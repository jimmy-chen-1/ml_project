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

        stage('初始化 pyenv 和 Python 3.10.13') {
            steps {
                sh '''
                    export PYENV_ROOT="$PYENV_ROOT"
                    export PATH="$PYENV_ROOT/bin:$PATH"
                    eval "$(pyenv init --path)"
                    eval "$(pyenv init -)"

                    echo "👉 检查是否安装 Python $PYTHON_VERSION..."
                    pyenv versions | grep $PYTHON_VERSION || pyenv install $PYTHON_VERSION
                    pyenv global $PYTHON_VERSION

                    echo "✅ 当前 Python 路径:"
                    which python3
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

                    PY310_BIN="$PYENV_ROOT/versions/$PYTHON_VERSION/bin"

                    echo "✅ 使用 Python 路径: $PY310_BIN/python"
                    $PY310_BIN/python -m venv $VENV_DIR

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
                    echo "✅ Flask 已启动，请访问： http://localhost:$PORT/"
                '''
            }
        }
    }

    post {
        success {
            echo '🎉 构建成功！你的网站已经部署完成啦~'
            sh 'open http://localhost:5000 || true' // 可选：Mac 自动打开页面
        }
        failure {
            echo '❌ 构建失败，请查看控制台输出日志'
        }
    }
}

