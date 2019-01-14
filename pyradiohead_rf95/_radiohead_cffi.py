#!/usr/bin/env python
# coding=utf-8

from pathlib import Path

import warnings
from cffi import FFI
from pkg_resources import resource_filename
import platform

module_name = "_radiohead_cffi"

ffi = FFI()
ffi.cdef(
    """
int init();
void setTxPower(int8_t power, bool useRFO);
bool setFrequency(float centre);
void setSpreadingFactor(int8_t sf);
void setSignalBandwidth(long sbw);
void setCodingRate4(int8_t denominator);
int send(uint8_t* data, uint8_t len);
int waitPacketSent();
int waitAvailableTimeout(int ms);
int available();
int recv(char* buf, uint8_t* len);
int maxMessageLength();
int printRegisters();
int enterSleepMode();
int setModeIdle();
int setModeTx();
int setModeRx();
int managerInit(int address);
int sendtoWait(uint8_t* data, uint8_t len, uint8_t dst);
int recvfromAck(char* buf, uint8_t* len, uint8_t* from, uint8_t* to, uint8_t* id, uint8_t* flags);
int recvfromAckTimeout(char* buf, uint8_t* len, uint16_t timeout, uint8_t* from, uint8_t* to, uint8_t* id, uint8_t* flags);
int setTimeout(uint16_t timeout);
int retries();
int setRetries(uint8_t retries);
int retransmissions();
int resetRetransmissions();
int headerFrom();
int headerTo();
int headerId();
int headerFlags();"""
)

compiler = platform.python_implementation().lower()
pyver = "".join(platform.python_version_tuple()[:2])
dll_name = "{compiler}-{pyver}m".format(compiler=compiler, pyver=pyver)
dll_file = resource_filename("pyradiohead_rf95", "libradiohead.%s.so" % dll_name)
try:
    lib = ffi.dlopen(dll_file)
except OSError:
    raise OSError("Link failed with the RadioHead C++ library. Try to reinstall the lib.")
