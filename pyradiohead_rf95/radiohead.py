#!/usr/bin/python

import os

from ._radiohead_cffi import ffi
from ._radiohead_cffi import lib as radiohead

buf = ffi.new("char*")
l = ffi.new("uint8_t*")
l[0] = 0
src = ffi.new("uint8_t*")
src[0] = 0


class RF95:

    # Bandwidth values
    bandwidth7_k8_hz = 7800
    bandwidth10_k4_hz = 10400
    bandwidth15_k6_hz = 15600
    bandwidth20_k8_hz = 20800
    bandwidth31_k25_hz = 31250
    bandwidth41_k7_hz = 41700
    bandwidth62_k5_hz = 62500
    bandwidth125_khz = 125000
    bandwidth250_khz = 250000
    bandwidth500_khz = 500000
    # Spreading factor values
    spreading_factor6 = 6
    spreading_factor7 = 7
    spreading_factor8 = 8
    spreading_factor9 = 9
    spreading_factor10 = 10
    spreading_factor11 = 11
    spreading_factor12 = 12
    # Coding rate denominator values
    coding_rate4_5 = 5
    coding_rate4_6 = 6
    coding_rate4_7 = 7
    coding_rate4_8 = 8

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
            radiohead.setSpreadingFactor(sf)

        def set_signal_bandwidth(self, sbw):
            radiohead.setSignalBandwidth(sbw)

        def set_coding_rate4(seld, denominator):
            radiohead.setCodingRate4(denominator)

    def manager_init(self, address):
        radiohead.managerInit(address)

    def send(self, data, l):
        r = radiohead.send(data, l)
        if r != 0:
            raise RuntimeError("nRF24 send failed")

    def wait_packet_sent(self):
        radiohead.waitPacketSent()

    def wait_available_timeout(self):
        radiohead.waitAvailableTimeout()

    def available(self):
        b = radiohead.available()
        if b == 1:
            return True
        else:
            return False

    def recv(self):
        radiohead.recv(buf, l)
        return (ffi.string(buf), l[0])

    def max_message_length(self):
        return radiohead.maxMessageLength()

    def print_registers(self):
        radiohead.printRegisters()

    def sleep(self):
        radiohead.enterSleepMode()

    def recvfrom_ack(self):
        radiohead.recvfromAck(buf, l, src)
        return (ffi.string(buf), l[0], src[0])

    def recvfrom_ack_timeout(self, timeout):
        ris = radiohead.recvfromAck(buf, l, timeout, src)
        if ris > 0:
            return (ffi.string(buf), l[0], src[0])
        else:
            return ("", -1, -1)

    def sendto_wait(self, data, l, dst):
        return radiohead.sendtoWait(data, l, dst)

    def retries(self):
        return radiohead.retries()

    def set_retries(self, retries):
        radiohead.setRetries(retries)

    def retransmissions(self):
        return radiohead.retransmissions()

    def reset_retransmissions(self):
        radiohead.resetRetransmissions()

    def set_timeout(self, timeout):
        radiohead.setTimeout(timeout)

    def set_mode_idle(self):
        radiohead.setModeIdle()

    def set_mode_tx(self):
        radiohead.setModeTx()

    def set_mode_rx(self):
        radiohead.setModeRx()
