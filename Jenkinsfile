pipeline {
    agent any

    environment {
        FLASK_APP = "app.py"
    }

    stages {
        stage('拉取代码') {
            steps {
                git 'https://github.com/jimmy-chen-1/ml_project.git'
            }
        }

        stage('安装依赖') {
            steps {
                sh 'python3 -m venv venv'
                sh './venv/bin/pip install -r requirements.txt'
            }
        }

        stage('启动服务') {
            steps {
                sh 'nohup ./venv/bin/python app.py &'
            }
        }
    }
}
