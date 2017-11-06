from celery import Celery
import mqtt_admin
from physics import model
import json
import database as db_admin


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
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10, periodic_model_update.s(), name='update hyd_sys every 2sec')


@app.task
def periodic_model_update():
    db = db_admin.connect_db()
    cu = db.cursor()
    package = cu.fetchone()
    db.close()
    model.hyd_sys.update(package)
    wish_list = model.hyd_sys.acquire(0.3)
    model.hyd_sys.update()
    if len(wish_list) > 0:
        mqtt_admin.client_beat.connect('127.0.0.1', 1885, 60)
        mqtt_admin.client_beat.publish('machine_data_request', payload=json.dumps({'wish_list': wish_list}))
        mqtt_admin.client_beat.disconnect()
    print('1 beat')


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
