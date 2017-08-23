from flask import Flask, render_template, request, redirect, Response
import psycopg2
import psycopg2.extras
import datetime
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import ssl

from functools import wraps

app = Flask(__name__)

connection_string = os.environ['DATABASE_URL']

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == os.environ['USERNAME'] and password == os.environ['PASSWORD']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def hello_world():
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM temperature ORDER BY reading_date DESC LIMIT 4')
    records = cursor.fetchall()

    cursor.execute('SELECT * FROM temperature ORDER BY temperature DESC LIMIT 1 ')
    highest = cursor.fetchall()
    max = highest[0]

    cursor.execute('SELECT * FROM temperature ORDER BY temperature ASC LIMIT 1 ')
    lowest = cursor.fetchall()
    min = lowest[0]

    #TODO read the lowest temperature

    return render_template('index.html', my_name='Thomas', highest=max, lowest=min, records=records, )


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/form')
@requires_auth
def form():
    return render_template('form.html')

@app.route('/led', methods=['POST'])
def led():

    DEVICE_ID = os.environ['DEVICE_ID']
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']

    url = "https://api.particle.io/v1/devices/%s/led?access_token=%s" % (DEVICE_ID, ACCESS_TOKEN)
    arg = request.form['arg']
    post_fields = {arg : arg}

    gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    req = Request(url, urlencode(post_fields).encode())
    urlopen(req, context=gcontext)

    return arg

@app.route('/ledstate')
def ledstate():

    DEVICE_ID = os.environ['DEVICE_ID']
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']

    url = "https://api.particle.io/v1/devices/%s/ledstate?access_token=%s" % (DEVICE_ID, ACCESS_TOKEN)

    gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return urlopen(url, context=gcontext).read()


@app.route('/me')
def me():
    return render_template('Me.html')

@app.route('/handle', methods=['POST'])
def handle():
    temperature = request.form['temperature']
    current_date = datetime.date.today().isoformat()
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = "INSERT INTO temperature (temperature, reading_date) values (%s,'%s')" % (temperature, current_date)
    cursor.execute(query)



    conn.commit()
    conn.close()

    return redirect("/")
    query

if __name__ == '__main__':
    app.run()


