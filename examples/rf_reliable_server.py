#!/usr/bin/python

from pyradiohead_rf95 import RF95
import time

CLIENT_ADDRESS = 1
SERVER_ADDRESS = 2

rf95 = RF95()

rf95.manager_init(SERVER_ADDRESS)

rf95.set_frequency(868)
rf95.set_tx_power(14, False)

print("Start-up Done!")
print("Receiving...")

while True:
    if rf95.available():
        print("Available")
        (msg, l, source) = rf95.recvfrom_ack()
        print("Received: %s (%s) from: %s" % (msg, str(l), str(source)))
        time.sleep(0.1)
    
        msg = "Hello back\0"
        print("Sending...")
        ret = rf95.sendto_wait(msg, len(msg), source)
        print("Sent %s" % ret)

        time.sleep(0.05)

