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

SOCKETTIMEOUT = 300

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
    def __init__(self, log, send, stop, leave):
        """
        Create an ebusd instance, allowing to listen the bus
        """
        self.log = log
        self.send = send
        self.stop = stop
        self.leave = leave
        
        self.ebusdevices = {}


    # -------------------------------------------------------------------------------------------------
    def ebusdopen(self, device):
        """ Open (opens the device once)
        @param device : the device string to open
        """
        try:
            self.log.info("Try to open connexion to ebusd: '%s'" % device)
            addr = device.split(':')
            addr = (addr[0], int(addr[1]))
            self.ebusctldev = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ebusctldev.connect(addr)
            self.ebusctldev.settimeout(SOCKETTIMEOUT)       # Add timeout for no blocking connexion.
            self.log.info("EBUS opened")
        except:
            error = "Error while opening Ebus : %s. Check if it is the good device address." % device
            raise ebusdException(error)


    # -------------------------------------------------------------------------------------------------
    def ebusdlisten(self):
        """
        """
        # Request find sensors to ebusd
        self.log.debug("==> Sending 'find' command to remote ebusd host")
        try:
            self.ebusctldev.send("find\n")
            data = self.ebusctldev.recv(8192)
        except socket.error, e:
            self.log.error("### Error socket for 'find' command: '%s'" % e)

        if data:
            for findline in data.splitlines():
                self.loop_sensor(findline)
        else:
            self.log.error("### No data received for 'find' command")
                    
        # Request listen sensors to ebusd
        self.log.debug("==> Sending 'listen' command to remote ebusd host")
        try:
            self.ebusctldev.send("listen\n")
        except socket.error, e:
            self.log.error("### Error socket for 'listen' command: '%s', Quitt program  !" % e)
            self.ebusctldev.close()
            self.leave()
            return
                
        while not self.stop.isSet():
            try:
                data = self.ebusctldev.recv(4096)
            except socket.error, e:
                self.log.error("### Error read socket for 'listen' command: '%s', Quitt program  !" % e)
                self.ebusctldev.close()
                self.leave()
                return

            if data:
                for listenline in data.splitlines():
                    self.loop_sensor(listenline)
            else:
                self.log.error("### No data received for 'listen' command, connexion closed")
                self.ebusctldev.close()
                self.leave()
                return


    # -------------------------------------------------------------------------------------------------
    def loop_sensor(self, line):
        """
        look up for a sensor when data comes from the bus.
        """
        self.log.info("Listen line received = '%s'" % line)                 # Ex.: 'bai PumpState = off'
        try:
            ebussensor_name = line.split("=")[0].strip()
            ebussensor_value = line.split("=")[1].strip()          
        except (ValueError, IndexError):
            #self.log.error(u"### No correct value in received line")
            pass
        else:
            for ebusdevice in self.ebusdevices:
                if self.ebusdevices[ebusdevice]['sensor_address'] == ebussensor_name:
                    self.send(ebusdevice, self.ebusdevices[ebusdevice]['device_type'][6:], ebussensor_value)       # Ex.: devicetype = "ebusd.state"  => sensor_name = "state"
               




 

