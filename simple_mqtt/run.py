import subprocess
import flask_app


# entry
# Before run this, a RabbitMQ broker for celery app should be start in terminal by:
# $sudo rabbitmq-server
# Because it needs root access, there is no easy and safe way to do it in python
if __name__ == '__main__':
    # start mqtt broker in a new process, if the port is used, find the pid by: $sudo lsof -i :1883
    # and kill it by $ sudo kill -9 <pid>
    subprocess.Popen('mosquitto -v -p 1885', shell=True)
    subprocess.Popen('celery -A celery_app:app worker --loglevel=info', shell=True)
    # start celery beat service
    subprocess.Popen('celery -A celery_app:app beat', shell=True)
    # app.run(host='0.0.0.0', debug=0)
    flask_app.app.run()
