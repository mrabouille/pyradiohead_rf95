#!/usr/bin/env python
# coding=utf-8

import logging
from radio import Radio

log = logging.getLogger()
log.setLevel("DEBUG")
handler = logging.StreamHandler()
log.addHandler(handler)
formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(message)s")
handler.setFormatter(formatter)

radio = Radio(adress=1)

radio.send("test", 2)
radio.loop_forever()