from flask import Flask, request, jsonify
from flask_cors import CORS
from configparser import ConfigParser
import psutil
import os
import platform

DOCKER_INSTALLED = False
try:
    import docker
    DOCKER_INSTALLED = True
except ImportError:
    DOCKER_INSTALLED = False

if not os.path.exists("config.rcf"):
    with open("config.rcf", "w") as configFile:
        configFile.close()
config = ConfigParser()
with open("config.rcf") as stream:
    config.read_string("[base]\n" + stream.read())

app = Flask(__name__)
CORS(app)

# Secret API key for authentication
API_KEY = config.get("base", "api_key")
VERSION = "0.0.2-DEV"

if DOCKER_INSTALLED:
    client = docker.from_env()

    # Check if the network already exists
    network_names = [net.name for net in client.networks.list()]

    if "goblin0" in network_names:
        print("Network goblin0 already exists.")
        network = client.networks.get("goblin0")
    else:
        # Create a new Docker network if it doesn't exist
        print("Creating network goblin0...")
        network = client.networks.create(
            "goblin0",
            driver="bridge"  # Use the default driver
        )

def authenticate(request):
    # Check if the request contains the API key
    token = request.headers.get('Authorization')
    if token and token == f"Bearer {API_KEY}":
        return True
    return False

@app.route('/system-info', methods=['GET'])
def system_info():
    if not authenticate(request):
        return jsonify({'error': 'Unauthorized'}), 401

    # Fetch system information using psutil
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')

    # Fetch OS information using platform
    os_info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'architecture': platform.architecture()[0],
        'machine': platform.machine(),
        'node': platform.node()
    }

    # Prepare the system information
    system_info = {
        'daemon': {
            'version': VERSION
        },
        'os': os_info,
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


    dockerJson = {}
    dockerJson["INSTALLED"] = DOCKER_INSTALLED
    if DOCKER_INSTALLED:
        try:
            client = docker.from_env()
            info = client.info()
            dockerJson["docker"] = info
        except docker.errors.DockerException as e:
            dockerJson["INSTALLED"] = False
    system_info["docker"] = dockerJson

    return jsonify(system_info)

@app.route('/docker', methods=['GET'])
def docker_info():
    dockerJson = {}
    dockerJson["INSTALLED"] = DOCKER_INSTALLED
    if DOCKER_INSTALLED:
        try:
            client = docker.from_env()
            info = client.info()
            dockerJson["docker"] = info
        except docker.errors.DockerException as e:
            dockerJson["INSTALLED"] = False
    return jsonify(dockerJson)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
