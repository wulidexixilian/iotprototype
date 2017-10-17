from celery import Celery
import mqtt_admin

# celery app initialization
def make_celery():
    ca = Celery(
        'simple_mqtt',
        broker='amqp://',
        backend='amqp://',
        include='flask_app'
    )

    # Optional configuration, see the application user guide.
    ca.conf.update(
        result_expires=3600,
        imports=['flask_app'],
    )
    ca.conf.update()
    return ca


app = make_celery()
# start worker by:
# simple_mqtt user$celery -A <file name for tasks definition>:<instance name of the celery app> worker --loglevel=info

# celery tasks
@app.task
def pub_a_msg(addr, port, topic, material):
    mqtt_admin.client_pub.connect(addr, int(port), 60)
    mqtt_admin.client_pub.publish(topic, payload=material)
    mqtt_admin.client_pub.disconnect()
    pass


@app.task
def sub_hold_on(addr, port):
    mqtt_admin.client_sub.connect(addr, int(port), 60)
    mqtt_admin.client_sub.loop_start()
    pass
