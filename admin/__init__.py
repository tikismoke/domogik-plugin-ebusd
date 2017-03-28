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
            if is_number(ebussensor_value): 
                device_type = "ebusd.value"
            elif ebussensor_value.lower() in ['on', 'off']:
                device_type = "ebusd.state"
            else:
                device_type = "ebusd.info"
                
            data_json.append({"name": ebussensor_name, "value": ebussensor_value, "type": device_type})
    return data_json


def get_info_from_log(cmd):
    print("Command = %s" % cmd)
    error_log_process = subprocess.Popen([cmd], stdout=subprocess.PIPE)
    output = error_log_process.communicate()[0]
    if isinstance(output, str):
        output = unicode(output, 'utf-8')
    return output

def is_number(s):
    ''' Return 'True' if s is a number
    '''
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

### common tasks
package = "plugin_ebusd"
template_dir = "{0}/{1}/admin/templates".format(get_packages_directory(), package)
static_dir = "{0}/{1}/admin/static".format(get_packages_directory(), package)
geterrorlogcmd = "{0}/{1}/admin/geterrorlog.sh".format(get_packages_directory(), package)

plugin_ebusd_adm = Blueprint(package, __name__,
                             template_folder=template_dir,
                             static_folder=static_dir)


@plugin_ebusd_adm.route('/<client_id>', methods=['GET'])
def index(client_id):
    detail = get_client_detail(client_id)
    ebusd_device = str(detail['data']['configuration'][1]['value'])
    information = ''

    try:
        return render_template('plugin_ebusd.html',
                               clientid=client_id,
                               client_detail=detail,
                               mactive="clients",
                               active='advanced',
                               sensor_list=list_sensors(ebusd_device),
                               errorlog=get_info_from_log(geterrorlogcmd),
                               information=information)

    except TemplateNotFound:
        abort(404)
