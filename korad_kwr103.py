#!/usr/bin/env python

"""korad_kwr103.py: Allow for control of a Korad KWR103 PSU"""

__author__ = "Charith Perera"

import socket
from netifaces import interfaces, ifaddresses, AF_INET
import time


class korad_kwr103:
    # Init with either an IP and port, a MAC address or nothing to auto discover
    def __init__(self, ip='', port=18190, mac='', interface_ip=''):
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.settimeout(0.1)
        self.connected = False
        if ip != '':
            self.device_ip = ip
            self.device_port = int(port)
            self.device_mac = None
            self.bind_interface_ip = interface_ip.encode()
            try:
                self.sock.bind((self.bind_interface_ip, self.device_port))
                self.connected = True
            except:
                self.connected = False
        else:
            self.device_ip = None
            self.device_port = None
            if mac == '':
                mac = None
            else:
                mac = str(mac)
                mac = mac.lower()
            self.auto_connect(mac)

    def discover_devices(self, port=18191):
        # Iterating over networks to discover devices on
        networks = []
        try:
            for ifaceName in interfaces():
                try:
                    addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': "Not Connected"}])]

                    for item in addresses:  # Scan through all interface addresses
                        if item != "Not Connected":  # Filter out the unconnected ones
                            networks.append(item)
                except:
                    print("Error looping through interfaces")
        except:
            print("Error retrieving interfaces")

        #print(networks)
        psu_list = []

        for network in networks:
            network = network.encode()
            discover_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            discover_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            discover_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            discover_sock.settimeout(0.1)

            discover_sock.bind((network, port))

            discover_sock.sendto(b"find_ka000", ('<broadcast>', port))

            awaiting_timeout = True
            while awaiting_timeout:
                try:
                    data, addr = discover_sock.recvfrom(10000)
                    #print(data)
                    data = data.decode()
                    data = data.splitlines()
                    if len(data) == 4:
                        psu = {}
                        psu["ip"] = data[0]
                        psu["mac"] = data[1].replace("-", ":")
                        psu["port"] = int(data[2])
                        psu["interface_ip"] = network.decode()
                        psu_list.append(psu)
                        #print(["Found", network, psu])
                except Exception as e:
                    #print(e)
                    awaiting_timeout = False
        if len(psu_list) == 0:
            print("No PSU's found, note that the default IP is 192.168.1.198 so you'll need a network adapter appropriately configure to communicate with that IP")
        return psu_list

    # Auto discover and connect to either a given MAC address or the only PSU found
    def auto_connect(self, mac=None):
        devices = self.discover_devices()
        conn_dev = None

        # If a MAC address is specified, try to find that supply
        if mac is not None:
            for device in devices:
                if device['mac'] == mac:
                    conn_dev = device
                    break
            if conn_dev is None:
                print("Could not find {mac}".format(mac=mac))

        # If only one supply is found, connect to that
        elif len(devices) == 1:
            conn_dev = devices[0]

        # If there are multiple, let things break
        elif len(devices) > 1:
            print("We have more than one device detected but no specified MAC address to connect to")

        if conn_dev is not None:
            self.device_ip = conn_dev['ip']
            self.device_port = int(conn_dev['port'])
            self.device_mac = conn_dev['mac']
            self.bind_interface_ip = conn_dev['interface_ip']
            self.sock.bind((self.bind_interface_ip, self.device_port))
            print("Connected to PSU: {psu}".format(psu=conn_dev))
            #print(conn_dev)

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

    def save_memory(self, mem_num: int):
        assert mem_num >= 1, "Memory must be within 1-5"
        assert mem_num <= 5, "Memory must be within 1-5"

        message = "SAV:{:.0f}".format(mem_num)
        self.udp_transact(message=message, bufsize=None)

    def recall_memory(self, mem_num: int):
        assert mem_num >= 1, "Memory must be within 1-5"
        assert mem_num <= 5, "Memory must be within 1-5"

        message = "RCL:{:.0f}".format(mem_num)
        self.udp_transact(message=message, bufsize=None)


    def set_voltage(self, voltage):
        message="VSET:{:.3f}".format(voltage)
        self.udp_transact(message=message, bufsize=None)

    def meas_voltage(self, read_setpoint=False):
        if read_setpoint:
            read = self.udp_transact(message="VSET?", bufsize=10000)
        else:
            read = self.udp_transact(message="VOUT?", bufsize=10000)
        try:
            return float(read)
        except:
            return float("nan")

    def set_ovp(self, ovp):
        message = "OVP:{:.2f}".format(ovp)
        self.udp_transact(message=message, bufsize=None)

    def set_current(self, current):
        message = "ISET:{:.3f}".format(current)
        self.udp_transact(message=message, bufsize=None)

    def meas_current(self, read_setpoint=False):
        if read_setpoint:
            read = self.udp_transact(message="ISET?", bufsize=10000)
        else:
            read = self.udp_transact(message="IOUT?", bufsize=10000)
        try:
            return float(read)
        except:
            return float("nan")

    def set_ocp(self, ocp):
        message = "OCP:{:.2f}".format(ocp)
        self.udp_transact(message=message, bufsize=None)

    def output(self, enable=True):
        if enable:
            self.udp_transact(message="OUT:1", bufsize=None)
        else:
            self.udp_transact(message="OUT:0", bufsize=None)



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
        self.sock.close()
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

    instr = korad_kwr103()
    #instr = korad_kwr103(ip='', port=18190, mac='8a:53:ee:48:56:42')
    discovered = instr.discover_devices()
    print(discovered)

    #instr.update_device(ip=discovered[0]["ip"], port=discovered[0]["port"])
    #print(instr.device_ip)
    #print(instr.device_port)


    instr.set_ovp(32)
    instr.set_ocp(5)

    instr.output(True)
    # for i in range(10):
    #     instr.set_voltage(i)
    #     time.sleep(0.5)
    #     print([instr.meas_voltage(read_setpoint=True), instr.meas_voltage()])
    #     time.sleep(0.5)
    print(instr.query_idn())

    print([instr.meas_current(read_setpoint=True), instr.meas_current()])
    instr.output(False)

    instr.set_voltage(5)
    instr.set_current(3)
    time.sleep(0.1)
    instr.save_memory(1)
    instr.save_memory(4)
    instr.save_memory(5)

    instr.set_voltage(12)
    instr.set_current(3)
    time.sleep(0.1)
    instr.save_memory(2)

    instr.set_voltage(24)
    instr.set_current(3)
    time.sleep(0.1)
    instr.save_memory(3)

    instr.recall_memory(3)
    instr.set_ip(dhcp=True)
