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

radio = Radio(adress=2, listening_ratio=.9)

for message in radio.receiver_stream:
    print(message)