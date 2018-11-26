#!/usr/bin/env python
# coding=utf-8

import logging
from pyradiohead_rf95.radio import Radio
import itertools

log = logging.getLogger()
log.setLevel("DEBUG")
handler = logging.StreamHandler()
log.addHandler(handler)
formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(message)s")
handler.setFormatter(formatter)


def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i : i + n]


if __name__ == "__main__":
    master_radio = Radio(adress=1)
    text = """Le Capitaine Jonathan,
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
Si l'on ne fait pas d'omelette avant."""
    for i, chunk in enumerate(chunks(text, 100)):
        master_radio.send({"chunk_number": i, "text": chunk}, 2, wait=True)
    master_radio.send(False, 2, wait=True)
    master_radio.loop_forever()