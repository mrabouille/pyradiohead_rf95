#!/usr/bin/env python
# coding=utf-8

import logging
from radio import Radio
import time
import operator
from packet_pb2 import Packet

log = logging.getLogger()
log.setLevel("DEBUG")
handler = logging.StreamHandler()
log.addHandler(handler)
formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(message)s")
handler.setFormatter(formatter)

original_text = """Le Capitaine Jonathan,
Etant âgé de dix-huit ans
Capture un jour un pélican
Dans une île d'Extrême-orient,

Le pélican de Jonathan
Au matin, pond un oeuf tout blanc
Et il en sort un pélican
Lui ressemblant étonnamment.

Et ce deuxième pélican
Pond, à son tour, un oeuf tout blanc
D'où sort, inévitablement

Un autre, qui en fait autant.

Cela peut durer pendant très longtemps
Si l'on ne fait pas d'omelette avant. """


if __name__ == "__main__":
    radio = Radio(adress=2, listening_ratio=.9)
    text = {}
    while True:
        message = radio.receive()
        print(message)
        if message is None:
            continue
        if message.payload == False:
            break

        text[message.payload["chunk_number"]] = message.payload["text"]

    print("#" * 20)
    print("".join(text.values()))

    radio.off()
