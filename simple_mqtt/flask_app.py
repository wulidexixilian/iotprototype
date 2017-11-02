import os
from flask import Flask, g, request, session, redirect, url_for, abort, \
    render_template, flash
import celery_app
import database as db_admin

# define a flask app
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'simple_mqtt.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('SIMPLE_MQTT_SETTINGS', silent=True)


# db operation for web
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
        g.sqlite_db = db_admin.connect_db()
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


# web control
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
    mqtt_result = celery_app.pub_a_msg.delay(addr, port, topic, material)
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
    result_mqtt = celery_app.sub_hold_on.delay(addr, port)
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

