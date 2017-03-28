#!/usr/bin/python
# -*- coding: utf-8 -*-


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

Plugin for ebus protocole throw ebusd

Implements
==========


@author: tikismoke  (new dt domodroid at gmail dt com)
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage

from domogik_packages.plugin_ebusd.lib.ebusd import ebusdException
from domogik_packages.plugin_ebusd.lib.ebusd import ebusdclass

import threading
import time
import json


class ebusdManager(Plugin):
    # -------------------------------------------------------------------------------------------------
    def __init__(self):
        """
            Init plugin
        """
        Plugin.__init__(self, name='ebusd')

        # Check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return

        # Get the devices list, for this plugin, if no devices are created we won't be able to use devices.
        self.devices = self.get_device_list(quit_if_no_device=True)
        ###self.log.info(u"==> device:   %s" % format(self.devices))

        # get the sensors id per device :
        self.sensors = self.get_sensors(self.devices)
        ###self.log.info(u"==> sensors:   %s" % format(self.sensors))

        # Open the ebus manager
        self.ebusdclass = ebusdclass(self.log, self.send_data, self.get_stop(), self.force_leave)

        # Open socket connexion to ebusd
        ebusctldevice = self.get_config("ebusctldevice")    # Get config key
        try:
            self.ebusdclass.ebusdopen(ebusctldevice)
        except ebusdException as ex:
            self.log.error(ex.value)
            self.force_leave()
            return

        # Set ebussensors list
        self.setEbusDevicessList(self.devices)

        # Run Ebus listen thread
        self.log.info(u"==> Launch 'ebus listen' thread") 
        thr_name = "thr_EbusCtlListen"
        self.thread_EbusCtlListen = threading.Thread(None,
                                          self.ebusdclass.ebusdlisten,
                                          thr_name,
                                          (),
                                          {})
        self.thread_EbusCtlListen.start()
        self.register_thread(self.thread_EbusCtlListen)

        # Add callback for new or changed devices
        self.log.info(u"==> Add callback for new or changed devices.")
        self.register_cb_update_devices(self.reload_devices)
        
        self.ready()

    # -------------------------------------------------------------------------------------------------
    def setEbusDevicessList(self, devices):
        self.log.info(u"==> Set ebus devices list ...")
  
        for a_device in devices:    # For each device
            # self.log.info(u"a_device:   %s" % format(a_device))
            device_id = a_device["id"] 
            device_name = a_device["name"] 
            device_type = a_device["device_type_id"]
               
            sensor_address = self.get_parameter(a_device, "address")
            self.log.info(u"==> Device '{0}' (id:{1}/{2}), name = {3}".format(device_name, device_id, device_type, sensor_address))
            #self.ebusdclass.ebusdevices.append({'device_id': device_id, 'device_name': device_name, 'device_type': device_type, 'sensor_address': sensor_address})  
            self.ebusdclass.ebusdevices.update({device_id: {'device_name': device_name, 'device_type': device_type, 'sensor_address': sensor_address}})  


    # -------------------------------------------------------------------------------------------------
    def send_data(self, device_id, sensor_name, value):
        """ Send the sensors values over MQ
        """
        self.log.debug(u"==> Send value '%s' (%s) for device '%s' (id:%s)" % (value, sensor_name, self.ebusdclass.ebusdevices[device_id]['device_name'], device_id))
        sensor_id = self.sensors[device_id][sensor_name]
        data = {sensor_id: value}
        
        try:
            self._pub.send_event('client.sensor', data)
        except:
            self.log.error(u"###Error while sending sensor MQ message for sensor values : {0}".format(traceback.format_exc()))
            pass


    # -------------------------------------------------------------------------------------------------
    def reload_devices(self, devices):
        """ Called when some devices are added/deleted/updated
        """
        self.log.info(u"==> Reload devices called")
        self.setEbusDevicessList(devices)
        self.devices = devices
        self.sensors = self.get_sensors(devices)

        

if __name__ == "__main__":
    ebusdManager()
