# -*- coding: utf-8 -*-
"""
the whole app
"""

import json
import os
import sqlite3
import subprocess
import numpy
import paho.mqtt.client as mqtt
from flask import Flask, g, request, session, redirect, url_for, abort, \
    render_template, flash
from celery import Celery


app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'simple_mqtt.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('SIMPLEMQTT_SETTINGS', silent=True)


def make_celery():
    celery_app = Celery(app.name,
                        broker='amqp://',
                        backend='amqp://',
                        include='simple_mqtt')

    # Optional configuration, see the application user guide.
    celery_app.conf.update(
        result_expires=3600,
        imports=['simple_mqtt'],
    )
    celery_app.conf.update()
    return celery_app


celery_app = make_celery()
# start worker by: simple_mqtt user$celery -A simple_mqtt:celery_app worker --loglevel=info


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def pub_entry():
    if not session.get('logged_in'):
        abort(401)
    # db = get_db()
    # db.execute('insert into entries (title, text) values (?, ?)',
    #              [request.form['title'], request.form['text']])
    # db.commit()
    addr = request.form['Mqtt_Server']
    port = request.form['Port']
    topic = request.form['Topic']
    material = request.form['Message']
    mqtt_result = pub_a_msg.delay(addr, port, topic, material)
    flash('New Publish')
    return redirect(url_for('show_entries'))


@app.route('/delete', methods=['POST'])
def delete_all():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from entries')
    db.commit()
    flash('DB cleared')
    return redirect(url_for('show_entries'))


@app.route('/connect', methods=['POST'])
def connect_mqtt():
    if not session.get('logged_in'):
        abort(401)
    addr = request.form['Mqtt_Server']
    port = request.form['Port']
    result_mqtt = sub_holdon.delay(addr, port)
    flash('Mqtt listener online')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


# The callback for when the client receives a CONNACK response from the server.
def on_connect_receive(client, userdata, flag, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("msg_to_server")


# The callback for when the client receives a CONNACK response from the server.
def on_connect_pub(client, userdata, flag, rc):
    print("Connected with result code "+str(rc))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + ':' + str(msg.payload))
    try:
        data = json.loads(msg.payload)
        arr = numpy.array(data['array'])
        result = 'the sum of your array is {}'.format(str(arr.sum()))
        topic = 'json data'
    except ValueError:
        result = msg.payload
        topic = msg.topic
    else:
        pass
    db = connect_db()
    db.execute('insert into entries (title, text) values (?, ?)',
               [topic, result])
    db.commit()
    db.close()
    print('db updated')


client_sub = mqtt.Client()
client_sub.on_connect = on_connect_receive
client_sub.on_message = on_message
client_pub = mqtt.Client()
client_pub.on_connect = on_connect_pub


@celery_app.task
def pub_a_msg(addr, port, topic, material):
    client_pub.connect(addr, int(port), 60)
    client_pub.publish(topic, payload=material)
    client_pub.disconnect()
    pass


@celery_app.task
def sub_holdon(addr, port):
    client_sub.connect(addr, int(port), 60)
    client_sub.loop_start()
    pass


if __name__ == '__main__':
    # start mqtt broker in a new process, if the port is used, find the pid by: $sudo lsof -i :1883
    # and kill it by $ sudo kill -9 <pid>
    subprocess.Popen('mosquitto -v -p 1885', shell=True)
    subprocess.Popen('celery -A simple_mqtt:celery_app worker --loglevel=info  ', shell=True)
    # app.run(host='0.0.0.0', debug=0)
    app.run()
