import numpy
import paho.mqtt.client as mqtt
import json
import database as db_admin


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
    db = db_admin.connect_db()
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
