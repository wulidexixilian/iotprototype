# -*- coding: utf-8 -*-
"""
the whole app
"""

import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import paho.mqtt.client as mqtt
import subprocess
import json
import numpy
import time

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'simple_mqtt.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('SIMPLEMQTT_SETTINGS', silent=True)


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


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


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
    client_pub.connect(addr, int(port), 60)
    client_pub.publish(request.form['Topic'], payload=request.form['Message'])
    client_pub.disconnect()
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
    client_sub.connect(addr, int(port), 60)
    client_sub.loop_start()
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


if __name__ == '__main__':
    # start mqtt broker in a new process
    subprocess.Popen('mosquitto -v', shell=True)
    # define mqtt clients
    client_sub = mqtt.Client()
    client_sub.on_connect = on_connect_receive
    client_sub.on_message = on_message
    client_pub = mqtt.Client()
    client_pub.on_connect = on_connect_pub
    app.run(host='0.0.0.0', debug=0)
    # app.run()