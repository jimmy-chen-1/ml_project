pipeline {
  agent any

  environment {
    PYTHON_VERSION = "python3"
    VENV_DIR = "venv"
    APP_PORT = "4090"
    GUNICORN_LOG = "gunicorn.log"
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

          echo "🧹 清理旧日志（如有）..."
          rm -f ${GUNICORN_LOG}

          echo "🎯 后台运行 Gunicorn（监听 ${APP_PORT}）..."
          nohup gunicorn -w 2 -b 0.0.0.0:${APP_PORT} app:app > ${GUNICORN_LOG} 2>&1 &

          echo "⏳ 等待 Gunicorn 初始化..."
          sleep 5

          echo "🌐 检查应用是否可访问..."
          if curl -s http://127.0.0.1:${APP_PORT}/ > /dev/null; then
            echo "✅ Gunicorn 应用已成功运行并监听端口 ${APP_PORT}"
          else
            echo "❌ Gunicorn 应用无法访问，打印日志内容："
            cat ${GUNICORN_LOG}
            exit 1
          fi
        '''
      }
    }
  }

  post {
    failure {
      echo '❌ 构建失败，请查看控制台日志及 gunicorn.log 内容'
    }
    success {
      echo "✅ 构建成功！你现在可以访问 → http://localhost:${APP_PORT} 或调用 /weather 接口"
    }
  }
}
