import paho.mqtt.client as mqtt
import json

client_sub = mqtt.Client()
client_pub = mqtt.Client()


def on_connect_sub(client, userdata, flag, rc):
    print('plc: online')
    client.subscribe('machine_data_request')


def on_message_sub(client, userdata, msg):
    print('plc: get message: {}'.format(msg.payload))
    try:
        message = json.loads(msg.payload)
        if 'machine_data_request' in message:
            feedback = {}
            for key in message['machine_data_request']:
                feedback['key'] = 1
            client_pub.connect('127.0.0.1', 1885, 60)
            client_pub.publish('machine_data_feedback', json.dumps({'machine_data': feedback}))
            client_pub.disconnect()
    except ValueError:
        pass
    else:
        pass


client_sub.on_connect = on_connect_sub
client_sub.on_message = on_message_sub

client_sub.connect('127.0.0.1', 1885, 60)
client_sub.loop_start()