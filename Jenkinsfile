pipeline {
  agent any

  environment {
    PYENV_ROOT = "${HOME}/.pyenv"
    PYTHON_VERSION = "3.10.13"
  }

  stages {

    stage('拉取代码') {
      steps {
        git 'https://github.com/jimmy-chen-1/ml_project.git'
      }
    }

    stage('初始化 pyenv 和 Python 3.10.13') {
      steps {
        sh '''
          echo "👉 初始化 pyenv..."
          export PATH="$PYENV_ROOT/bin:$PATH"
          eval "$(pyenv init --path)"
          eval "$(pyenv init -)"
          pyenv global ${PYTHON_VERSION}
          echo "✅ 当前 Python 路径: $(which python3)"
          python3 --version
        '''
      }
    }

    stage('创建虚拟环境 & 安装依赖') {
      steps {
        sh '''
          echo "🐍 创建虚拟环境..."
          ${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin/python -m venv venv
          source venv/bin/activate

          echo "⚙️ 升级 pip..."
          pip install --upgrade pip

          echo "📦 安装 tensorflow-macos（M 芯片专用）..."
          pip install tensorflow-macos==2.12.0 --extra-index-url https://pypi.apple.com/simple

          echo "📦 安装其他依赖..."
          pip install -r requirements.txt
        '''
      }
    }

    stage('检查模型文件是否存在') {
      steps {
        sh '''
          echo "🔍 检查模型文件是否存在..."
          if [ ! -f "models/lstm_model.pkl" ]; then
            echo "❌ 模型文件不存在"
            exit 1
          else
            echo "✅ 模型文件已找到"
          fi
        '''
      }
    }

    stage('启动 Flask 应用') {
      steps {
        sh '''
          echo "🚀 启动 Flask 应用..."
          source venv/bin/activate
          python app.py
        '''
      }
    }
  }

  post {
    failure {
      echo '❌ 构建失败，请查看控制台输出日志'
    }
  }
}
