""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Plugin for ebus throw ebusd

Implements
==========

class ebusd, ebusdException

@author: tikismoke
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import subprocess

import sys
import os
import locale
import time
import datetime
import calendar
import socket

class ebusdException(Exception):
    """
    ebusd exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class ebusdclass:
    """
    Get informations about ebus
    """

    # -------------------------------------------------------------------------------------------------
    def __init__(self, log, device):
        try:
            """
            Create an ebusd instance, allowing to listen the bus
            """
            self._log = log
            self.device= device
            self._sensors = []

        except ValueError:
            self._log.error(u"error reading Xee.")
            return

    def open(self, device):
        """ Open (opens the device once)
        @param device : the device string to open
        """
        try:
            self._log.info("Try to open Ebusd: %s" % device)
            addr = device.split(':')
            addr = (addr[0], int(addr[1]))
            self._dev = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._dev.connect( addr )
            self._log.info("EBUS opened")
        except:
            error = "Error while opening Ebus : %s. Check if it is the good device address." % device
            raise ebusdException(error)


    # -------------------------------------------------------------------------------------------------
    def add_sensor(self, device_id, device_name, device_type, sensor_address):
        """
        Add a sensor to sensors list.
        """
        self._sensors.append({'device_id': device_id, 'device_name': device_name, 'device_type': device_type,
                              'sensor_address': sensor_address})
        self._log.debug("add_sensor for ="+sensor_address)

    # -------------------------------------------------------------------------------------------------
    def loop_sensor(self, data, send_sensor):
        """
        look up for a sensor when data comes from the bus.
        """
        try:
	    self._log.debug(data)
	    temp_data = data.split ('=')
            data_name=temp_data[0]
            data_value=temp_data[1]
	    data_name=data_name[:-1]
	    data_value=data_value[1:]
	    for sensor in self._sensors:
		if sensor['sensor_address'] == data_name:
		    sensor_name = ""
                    if sensor['device_type'] == "ebusd.string":
	                sensor_name = "level_string"
    	            elif sensor['device_type'] == "ebusd.number":
        	        sensor_name = "level_number"
            	    elif sensor['device_type'] == "ebusd.onoff":
			sensor_name = "level_bin"
		    if sensor_name != "":
			send_sensor(sensor['device_id'], sensor_name, data_value)
	except:
            self._log.error("Error with loop_sensor for data=" + data)


    # -------------------------------------------------------------------------------------------------
    def read_bus_for_sensor(self, send, send_sensor, stop):
        """
        """
        while not stop.isSet():
            try:
                self._log.debug("sending find to remote  host")
                self._dev.send( "find\n" )
                data = self._dev.recv(8192)
                for str in data.splitlines():
                    self.loop_sensor(str, send_sensor)
                self._log.error("connection closed by remote host")
                self._log.debug("sending listen to remote  host")
                self._dev.send( "listen\n" )
                while 1:
                    data = self._dev.recv(4096)
                    for str in data.splitlines():
                        self.loop_sensor(str, send_sensor)
                self._log.error("connection closed by remote host")
            except:
                self._log.error(u"# Read bus for sensor EXCEPTION")
		pass