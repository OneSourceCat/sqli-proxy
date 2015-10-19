#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Start sql injection detect based on proxy.py and autosqli.py.
"""
import time
import json
import requests

server = "http://127.0.0.1:8775/"

def task_new():
    taskid = json.loads(
        requests.get(server + 'task/new').text)['taskid']
    return taskid

def option_set(taskid):
    headers = {'Content-Type': 'application/json'}
    option = {"options": {
                "smart": True,
                'rFile': "post.txt"
                }
             }
    url = server + 'option/' + taskid + '/set'
    t = json.loads(
        requests.post(url, data=json.dumps(option), headers=headers).text)
    print t

def scan_start(taskid):
    headers = {'Content-Type': 'application/json'}
    payload = {'url': "http://127.0.0.1/sqli.php", "data": "id=1"}
    url = server + 'scan/' + taskid + '/start'
    t = json.loads(
        requests.post(url, data=json.dumps(payload), headers=headers).text)
    print t

def task_delete(taskid):
    if json.loads(requests.get(server + 'task/' + taskid + '/delete').text)['success']:
        print '[%s] Deleted task' % (taskid)
        return True
    return False

def scan_data(taskid):
    data = json.loads(
        requests.get(server + 'scan/' + taskid + '/data').text)['data']
    print data

taskid = task_new()
option_set(taskid)
scan_start(taskid)
time.sleep(6)
scan_data(taskid)
task_delete(taskid)
