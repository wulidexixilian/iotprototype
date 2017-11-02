import numpy
import paho.mqtt.client as mqtt
import json
import database as db_admin


# The callback for when the client receives a CONNACK response from the server.
def on_connect_sub(client, userdata, flag, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe([("machine_data_feedback", 0), ("msg_from_god", 0)])


# The callback for when the client receives a CONNACK response from the server.
def on_connect_pub(client, userdata, flag, rc):
    print("Connected with result code "+str(rc))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + ':' + str(msg.payload))
    try:
        data = json.loads(msg.payload)
        if 'machine_data' in data:
            title = 'machine_data'
            text = msg.payload
    except ValueError:
        text = msg.payload
        title = 'invalid_feedback'
    else:
        pass
    db = db_admin.connect_db()
    db.execute('insert into entries (title, text) values (?, ?)',
               [title, text])
    db.commit()
    db.close()
    print('db updated')


client_sub = mqtt.Client()
client_sub.on_connect = on_connect_sub
client_sub.on_message = on_message
client_pub = mqtt.Client()
client_pub.on_connect = on_connect_pub
client_beat = mqtt.Client()

