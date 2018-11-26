#!/usr/bin/env python
# coding=utf-8

from pyradiohead_rf95.radiohead import RF95
import time
import warnings

rf95 = RF95()

rf95.init()
rf95.manager_init(1)
rf95.set_frequency(434)

for i in range(10):
    if rf95.available:
        print("Radio reached !")
        break
    warnings.warn("Attempt %i, unable to communicate with the radio." % i)
    time.sleep(1)
else:
    raise RuntimeError("Unable to reach radio !")

