# -*- coding: utf-8 -*-

### common imports
from flask import Blueprint, abort
from domogik.common.utils import get_packages_directory
from domogik.admin.application import render_template
from domogik.admin.views.clients import get_client_detail
from jinja2 import TemplateNotFound
import traceback
import sys

### package specific imports
import subprocess
import os
import datetime
import time
from flask_wtf import Form
from wtforms import StringField

from flask import request, flash

try:
    from flask.ext.babel import gettext, ngettext
except ImportError:
    from flask_babel import gettext, ngettext

    pass

### plugin specific imports
import socket

import json

from domogik.admin.application import app
from domogikmq.pubsub.publisher import MQPub
import zmq


### package specific functions

def list_sensors(device):
    """ Open (opens the device once)
    @param device : the device string url to open
    """
    try:
        data_json = []
        addr = device.split(':')
        addr = (addr[0], int(addr[1]))
        dev = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dev.connect(addr)
        dev.send("find -d -r \n")
        data = dev.recv(8192)
    except:
        flash(gettext(u"Error while opening ebusd socket, check your configuration"), "error")
        return ""
    for line in data.splitlines():
        if line:
            ebussensor_name = line.split("=")[0].strip()
            ebussensor_value = line.split("=")[1].strip()                         
            data_json.append({"name": ebussensor_name, "value": ebussensor_value, "type": ""})
    return data_json


def get_info_from_log(log):
    print("Log file = %s" % log)
    errorlog = subprocess.Popen(['/bin/egrep', 'ERROR|WARNING', log], stdout=subprocess.PIPE)
    output = errorlog.communicate()[0]
    if not output:
        output = "No ERROR or WARNING"
    if isinstance(output, str):
        output = unicode(output, 'utf-8')
    return output


### common tasks
package = "plugin_ebusd"
template_dir = "{0}/{1}/admin/templates".format(get_packages_directory(), package)
static_dir = "{0}/{1}/admin/static".format(get_packages_directory(), package)
logfile = "/var/log/domogik/{0}.log".format(package)

plugin_ebusd_adm = Blueprint(package, __name__,
                             template_folder=template_dir,
                             static_folder=static_dir)


@plugin_ebusd_adm.route('/<client_id>', methods=['GET'])
def index(client_id):
    detail = get_client_detail(client_id)
    try:
        ebusd_device = str(detail['data']['configuration'][1]['value'])
    except KeyError:
        ebusd_device = ''
    try:
        return render_template('plugin_ebusd.html',
                               clientid=client_id,
                               client_detail=detail,
                               mactive="clients",
                               active='advanced',
                               sensor_list=list_sensors(ebusd_device),
                               logfile = logfile,
                               errorlog=get_info_from_log(logfile))
    except TemplateNotFound:
        abort(404)


@plugin_ebusd_adm.route('/<client_id>/log')
def log(client_id):
    clientid = client_id
    detail = get_client_detail(client_id)
    with open(logfile, 'r') as contentLogFile:
        content_log = contentLogFile.read()
        if not content_log:
            content_log = "Empty log file"
        if isinstance(content_log, str):
            content_log = unicode(content_log, 'utf-8')
    try:
        return render_template('plugin_ebusd_log.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'advanced',
            logfile = logfile,
            contentLog = content_log)

    except TemplateNotFound:
        abort(404)
