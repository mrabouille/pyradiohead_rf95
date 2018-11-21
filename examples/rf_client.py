#!/usr/bin/python

from pyradiohead_rf95 import RF95
import time

rf95 = RF95()

rf95.init()

rf95.set_tx_power(14, False)
rf95.set_frequency(868)

rf95.set_signal_bandwidth(rf95.bandwidth500_khz)
rf95.set_spreading_factor(rf95.spreading_factor12)
rf95.set_coding_rate4(rf95.coding_rate4_8)

print("StartUp Done!")

while True:
    msg = "Hello\0"
    print("Sending message...")
    rf95.send(msg, len(msg))
    rf95.wait_packet_sent()
    time.sleep(10)
