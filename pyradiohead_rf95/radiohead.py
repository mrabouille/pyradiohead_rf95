#!/usr/bin/python

import os

from ._radiohead_cffi import ffi
from ._radiohead_cffi import lib as radiohead

buffer_ = ffi.new("char*")
length_ = ffi.new("uint8_t*")
length_[0] = 0
from_ = ffi.new("uint8_t*")
from_[0] = 0
to_ = ffi.new("uint8_t*")
to_[0] = 0
id_ = ffi.new("uint8_t*")
id_[0] = 0
rssi_ = ffi.new("int8_t*")
rssi_[0] = 0


class RF95:

    # Bandwidth values
    available_bandwidth = (
        7800,
        10400,
        15600,
        20800,
        31250,
        41700,
        62500,
        125000,
        250000,
        500000,
    )
    # Spreading factor values
    available_spreading_factor = 6, 7, 8, 9, 10, 11, 12
    # Coding rate denominator values
    available_coding_rate4 = 5, 6, 7, 8

    def init(self):
        r = radiohead.init()
        if r != 0:
            raise RuntimeError("RF95 init failed - value: %i" % r)

    def set_tx_power(self, power, useRFO):
        radiohead.setTxPower(power, useRFO)

    def set_frequency(self, centre):
        r = radiohead.setFrequency(centre)
        return r

    def set_spreading_factor(self, sf):
        if sf not in self.available_spreading_factor:
            raise ValueError("Spreading factor not allowed. See RH95.available_spreading_factor")
        radiohead.setSpreadingFactor(sf)

    def set_signal_bandwidth(self, sbw):
        if sbw not in self.available_bandwidth:
            raise ValueError("Bandwidth not allowed. See RH95.available_bandwidth")
        radiohead.setSignalBandwidth(sbw)

    def set_coding_rate4(self, denominator):
        if denominator not in self.available_coding_rate4:
            raise ValueError("denominator not allowed. See RH95.available_coding_rate4")
        radiohead.setCodingRate4(denominator)

    def manager_init(self, address):
        radiohead.managerInit(address)

    def send(self, data, length):
        r = radiohead.send(data, length)
        if r != 0:
            raise RuntimeError("nRF24 send failed")

    def wait_packet_sent(self):
        radiohead.waitPacketSent()

    def wait_available_timeout(self):
        radiohead.waitAvailableTimeout()

    @property
    def message_available(self):
        return bool(radiohead.available())

    def recv(self):
        radiohead.recv(buffer_, length_)
        return (ffi.string(buffer_), length_[0])

    @property
    def max_message_length(self):
        return radiohead.maxMessageLength()

    def print_registers(self):
        radiohead.printRegisters()

    def sleep(self):
        radiohead.enterSleepMode()

    def recvfrom_ack(self):
        received = radiohead.recvfromAck(buffer_, length_, from_, to_, id_, rssi_)
        if received:
            extras = {
                key: extra[0]
                for key, extra in zip(["dest", "id", "rssi"], [to_, id_, rssi_])
            }
            return (ffi.string(buffer_), length_[0], from_[0], extras)
        raise ValueError("No valid message copied to the buffer")

    def recvfrom_ack_timeout(self, timeout, ask_dst=True, ask_id=True, ask_rssi=False):
        received = radiohead.recvfromAck(buffer_, length_, from_, to_, id_, rssi_)
        if received:
            extras = {
                key: extra[0]
                for key, extra in zip(["dest", "id", "rssi"], [to_, id_, rssi_])
            }
            return (ffi.string(buffer_), length_[0], from_[0], extras)
        raise ValueError("No valid message copied to the buffer")

    def sendto_wait(self, data, length, dst):
        return radiohead.sendtoWait(data, length, dst)

    @property
    def retries(self):
        return radiohead.retries()

    def set_retries(self, retries):
        radiohead.setRetries(retries)

    @property
    def retransmissions(self):
        return radiohead.retransmissions()

    def reset_retransmissions(self):
        radiohead.resetRetransmissions()

    def set_timeout(self, timeout):
        radiohead.setTimeout(int(timeout))

    def set_mode_idle(self):
        radiohead.setModeIdle()

    def set_mode_tx(self):
        radiohead.setModeTx()

    def set_mode_rx(self):
        radiohead.setModeRx()

    def last_rssi(self):
        return radiohead.lastRssi()