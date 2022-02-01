# korad_kwr103 Ethernet
Library to simplify control of a KWR103 PSU over Ethernet, a seemingly nice PSU with good features for the dollars.

# Communication
The KWR103 supports Ethernet communication but the interface is not officially documented. The KWR100 software shipped with the PSU exposes the commands that are required and Wireshark is able to reveal further details as needed.
The KWR103 is commanded via UDP SCPI-like strings on its configured port. 

## Setup
Out of the box, the KWR103 comes with a static IP of 192.168.1.198 


