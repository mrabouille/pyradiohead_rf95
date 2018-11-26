#!/usr/bin/env python
# coding=utf-8

import logging
from pyradiohead_rf95.radio import Radio
import time

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
    radio = Radio(address=2, listening_ratio=.9)
    text = {}
    for message in radio.receiver_stream:
        if message is None:
            continue
        if message.payload == False:
            break

        text[message.payload["chunk_number"]] = message.payload["text"]

    print("#" * 20)
    print("".join(text.values()))

    radio.off()
