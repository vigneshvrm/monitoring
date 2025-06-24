from flask import Flask, Response
from prometheus_client import Gauge, generate_latest
import requests
from urllib.parse import quote_plus
import json
import time

API_URL = "https://control.elasticspace.io/client/api"
USERNAME = "monitor@assistanz.com"
PASSWORD = "5BT2h14K1zdH"

app = Flask(__name__)

api_success = Gauge('cloudstack_api_success', 'CloudStack API login + query success (1=OK, 0=Fail)')
api_latency = Gauge('cloudstack_api_latency_seconds', 'Latency for the CloudStack API check')

def cloudstack_login(session):
    payload = {
        "command": "login",
        "username": USERNAME,
        "password": PASSWORD,
        "response": "json",
    }
    r = session.post(API_URL, data=payload)
    r.raise_for_status()
    data = r.json()['loginresponse']
    sessionkey = data['sessionkey']
    return sessionkey

def cloudstack_api_call(session, command, sessionkey, **params):
    params.update({
        "command": command,
        "sessionkey": quote_plus(sessionkey),
        "response": "json",
    })
    r = session.get(API_URL, params=params)
    r.raise_for_status()
    return r.json()

def cloudstack_logout(session, sessionkey):
    try:
        cloudstack_api_call(session, 'logout', sessionkey)
    except Exception as e:
        print("Logout failed:", e)

@app.route('/metrics')
def metrics():
    t0 = time.time()
    with requests.Session() as session:
        try:
            sessionkey = cloudstack_login(session)
            # Run a simple health query (e.g. listZones)
            zones = cloudstack_api_call(session, "listZones", sessionkey, available='true')
            # If we made it here, everything is healthy!
            api_success.set(1)
        except Exception as e:
            print("Exporter error:", e)
            api_success.set(0)
        finally:
            # Always try to logout, but don’t fail exporter if logout fails
            try:
                if 'sessionkey' in locals():
                    cloudstack_logout(session, sessionkey)
            except Exception:
                pass
            api_latency.set(time.time() - t0)
    return Response(generate_latest(), mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9116)
