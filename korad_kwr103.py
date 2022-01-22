#!/usr/bin/env python

"""korad_kwr103.py: Allow for control of a Korad KWR103 PSU"""

__author__ = "Charith Perera"

import socket
import ctypes
import numpy as np
import time

import threading
import pandas as pd
import numpy as np
from influxdb import InfluxDBClient
import pytz
import datetime


class korad_kwr103:

    def __init__(self, ip='192.168.1.198', port=18190, interface_ip='192.168.0.14'):
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(0.1)
        self.sock.bind((interface_ip.encode(), port))
        self.device_ip = ip
        self.device_port = port

    def discover_devices(self, port=18191):
        # Might need to iterate over all Ethernet interfaces to do this right :(
        self.sock.sendto(b"find_ka000", ('<broadcast>', port))
        psu_list = []
        #data, addr = self.sock.recvfrom(10000)
        awaiting_timeout = True
        while awaiting_timeout:
            try:
                data, addr = self.sock.recvfrom(10000)
                #print(data)
                data = data.decode()
                data = data.splitlines()
                if len(data) == 4:
                    psu = {}
                    psu["ip"] = data[0]
                    psu["mac"] = data[1]
                    psu["port"] = int(data[2])
                    psu_list.append(psu)
            except Exception as e:
                print(e)
                awaiting_timeout = False

        return psu_list

    def discover_and_assign(self):
        pass

    def update_device(self, ip='192.168.1.198', port=18190):
        self.device_ip = ip
        self.device_port = port

    def query_idn(self):
        ret = self.udp_transact(message="*IDN?")
        return ret

    def set_ip(self, dhcp=True, ip="", subnet_mask="", gateway=""):
        if dhcp:
            self.udp_transact(message=":SYST:DHCP 1", bufsize=None)
        else:
            pass


    def udp_transact(self, message, bufsize=10000):
        message = message + "\r"
        message = message.encode()
        self.sock.sendto(message, (self.device_ip, self.device_port))
        if bufsize is not None:
            data, addr = self.sock.recvfrom(bufsize)
            data = data.decode()
            return data
        #print("received message: %s" % data)


    def close(self):
        pass
        #if self.device_handle is not None:
            #print("Trying to close")
            #status = tc08.usb_tc08_close_unit(self.device_handle)
            #assert_pico2000_ok(status)
            #self.device_handle = None


    def __exit__(self, type, value, traceback):
        print("Exit Called")
        self.close()

    def __enter__(self):
        print("Enter Called")
        return self

if __name__ == '__main__':
    import time

    instr = korad_kwr103(ip='192.168.0.16', port=18190)
    discovered = instr.discover_devices()
    print(discovered)
    #instr.update_device(ip=discovered[0]["ip"], port=discovered[0]["port"])
    #print(instr.device_ip)
    #print(instr.device_port)

    print(instr.query_idn())
    instr.set_ip()
