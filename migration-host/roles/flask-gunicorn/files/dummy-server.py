from flask import Flask, redirect
from pymemcache.client.base import Client
import time
import requests
import subprocess

app = Flask(__name__)
app.config['DEBUG'] = True
state_server = Client(('localhost', 11211))
TIME_LIMIT = 300

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def delayed_redirect(path):
    default_timer = time.time()
    while True:
        if time.time() - default_timer >= TIME_LIMIT:
            return 'Target is still offline after 5 minutes. Check the migration log and try again.'
        else:
            if monitor_target():
                return redirect('http://35.243.95.199', code=302)
            else:
                print time.time() - default_timer
                continue

def monitor_target():
    state = state_server.get('status')
    if state == 'online':
        print 'memcached returns online!'
        return True
    time.sleep(1)
    try:
        req = requests.get('http://10.0.1.5')
        if req.status_code == 200:
            # Target is ready :)
            # Update the cache
            if not state or state != 'online':
                state_server.set('status', 'online')
            return True
        else:
            return False
    except:
        return False

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=12345, debug=True)
    app.run()
