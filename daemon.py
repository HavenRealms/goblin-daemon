from flask import Flask, request, jsonify
from configparser import ConfigParser
import psutil, os

if not os.path.exists("config.rcf"):
    with open("config.rcf", "w") as configFile:
        configFile.close()
config = ConfigParser()
with open("config.rcf") as stream:
    config.read_string("[base]\n" + stream.read())

app = Flask(__name__)

# Secret API key for authentication
API_KEY = config.get("base", "api_key")
print(API_KEY)
VERSION = "0.0.1-DEV"

def authenticate(request):
    # Check if the request contains the API key
    token = request.headers.get('Authorization')
    if token and token == f"Bearer {API_KEY}":
        return True
    return False

@app.route('/system-info', methods=['GET'])
def system_info():
    #if not authenticate(request):
    #    return jsonify({'error': 'Unauthorized'}), 401

    # Fetch system information using psutil
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')

    # Prepare the system information
    system_info = {
        'daemon': {
            'version': VERSION
        },
        'cpu_usage': cpu_usage,
        'memory': {
            'total': memory_info.total,
            'available': memory_info.available,
            'percent': memory_info.percent,
            'used': memory_info.used,
            'free': memory_info.free
        },
        'disk': {
            'total': disk_usage.total,
            'used': disk_usage.used,
            'free': disk_usage.free,
            'percent': disk_usage.percent
        }
    }

    return jsonify(system_info)

if __name__ == '__main__':
    app.run(debug=True)
