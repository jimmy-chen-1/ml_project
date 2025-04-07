pipeline {
  agent any

  environment {
    PYTHON_VERSION = "python3"
    VENV_DIR = "venv"
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
          ${PYTHON_VERSION} -m venv ${VENV_DIR}
          source ${VENV_DIR}/bin/activate

          echo "⚙️ 升级 pip..."
          pip install --upgrade pip

          echo "📦 安装依赖（包含 PyTorch、Flask、Gunicorn 和通用工具包）..."
          pip install -r requirements.txt
        '''
      }
    }

    stage('启动 Flask 应用（Gunicorn）') {
      steps {
        sh '''
          echo "🚀 使用 Gunicorn 启动 Flask 应用..."
          source ${VENV_DIR}/bin/activate

          # 后台运行 Gunicorn，监听所有地址端口 5000
          nohup gunicorn -w 2 -b 0.0.0.0:5000 app:app > gunicorn.log 2>&1 &

          echo "✅ Gunicorn 启动成功，Jenkins Pipeline 可继续完成"
        '''
      }
    }
  }

  post {
    failure {
      echo '❌ 构建失败，请查看控制台输出日志'
    }
    success {
      echo '✅ 构建完成，应用正在运行中！'
    }
  }
}

