import requests
import time
import os
import json
from uuid import uuid4

endpoint = 'https://api.banana.dev/'
# Endpoint override for development
if 'BANANA_URL' in os.environ:
    print("Dev Mode")
    if os.environ['BANANA_URL'] == 'local':
        endpoint = 'http://localhost/'
    else:
        endpoint = os.environ['BANANA_URL']
    print("Hitting endpoint:", endpoint)

# THE MAIN FUNCTIONS
# ___________________________________


def run_main(api_key, model_key, model_inputs):
    result = start_api(api_key, model_key, model_inputs)

    # likely we get results on first call
    if result["finished"]:
        dict_out = {
            "id": result["id"],
            "message": result["message"],
            "created": result["created"],
            "apiVersion": result["apiVersion"],
            "modelOutputs": result["modelOutputs"]
        }
        yield dict_out

    # else it's long running, so poll for result
    while True:
        dict_out = check_api(api_key, result["callID"])
        if dict_out['message'].lower() == "success":
            yield dict_out

def start_main(api_key, model_key, model_inputs):
    result = start_api(api_key, model_key, model_inputs, start_only=True)
    return result["callID"]

def check_main(api_key, call_id):
    dict_out = check_api(api_key, call_id)
    return dict_out


# THE API CALLING FUNCTIONS
# ________________________

# Takes in start params and returns the full server json response
def start_api(api_key, model_key, model_inputs, start_only=False):
    global endpoint
    route_start = "start/v4/"
    url_start = endpoint + route_start

    payload = {
        "id": str(uuid4()),
        "created": int(time.time()),
        "apiKey" : api_key,
        "modelKey" : model_key,
        "modelInputs" : model_inputs,
        "startOnly": start_only
    }

    response = requests.post(url_start, json=payload)

    if response.status_code != 200:
        raise Exception("server error: status code {}".format(response.status_code))

    try:
        out = response.json()
    except:
        raise Exception("server error: returned invalid json")

    if "error" in out['message'].lower():
        raise Exception(out['message'])

    return out

# Takes in call_id to return the server response
def check_api(api_key, call_id):
    global endpoint
    route_check = "check/v4/"
    url_check = endpoint + route_check
    # Poll server for completed task

    payload = {
        "id": str(uuid4()),
        "created": int(time.time()),
        "longPoll": True,
        "callID": call_id, 
        "apiKey": api_key
    }
    response = requests.post(url_check, json=payload)

    if response.status_code != 200:
        raise Exception("server error: status code {}".format(response.status_code))

    try:
        out = response.json()
    except:
        raise Exception("server error: returned invalid json")

    try:
        if "error" in out['message'].lower():
            raise Exception(out['message'])
        return out
    except Exception as e:
        raise e
