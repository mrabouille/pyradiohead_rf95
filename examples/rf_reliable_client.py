#!/usr/bin/python

from pyradiohead_rf95 import RF95
import time

CLIENT_ADDRESS = 1
SERVER_ADDRESS = 2

rf95 = RF95()
rf95.init()
rf95.manager_init(CLIENT_ADDRESS)

rf95.set_frequency(868)
rf95.set_tx_power(14, False)

print("Start-up Done!")

while True:
    msg = "Hello\0"
    print("Sending...")
    ret = rf95.sendto_wait(msg, len(msg), SERVER_ADDRESS)
    print("Sent " + str(ret))

    time.sleep(0.4)
    
    if rf95.available():
        (msg, l, source) = rf95.recvfrom_ack()
        print("Received: %s (%s) from: %s" % (msg, str(l), str(source)))

    time.sleep(10)
