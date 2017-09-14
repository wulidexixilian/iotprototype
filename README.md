# iotprototype
prototype project to verify feasibility of embed mqtt protocal (Mosquitto) to a web server (programmed in flask framework). 
### Installation
* Simply copy the directory.
* Start the web application by run simple_mqtt/simple_mqtt.py.
* Then it can be accessed by the browser https://127.0.0.1:5000
### Description
* When the server is started, a mqtt broker is also started in a parallel process.
* After login, a mqtt client for receiving can be started in a parallel process by click connect. The client subscribe topic 'msg_to_sever' by default. A callback would be triggered when a message received.
```python
# The callback for when a message is received from the server
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
```
