pipeline {
  agent any

  environment {
    PYTHON_VERSION = "python3"
  }

  stages {

    stage('拉取代码') {
      steps {
        git branch: 'main', url: 'https://github.com/jimmy-chen-1/ml_project.git'
      }
    }

    stage('创建虚拟环境 & 安装依赖') {
      steps {
        sh '''
          echo "🐍 使用系统 Python 创建虚拟环境..."
          ${PYTHON_VERSION} -m venv venv
          source venv/bin/activate

          echo "⚙️ 升级 pip..."
          pip install --upgrade pip

          echo "📦 安装依赖（包含 PyTorch 和通用工具包）..."
          pip install -r requirements.txt
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
