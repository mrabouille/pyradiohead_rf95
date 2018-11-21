# pyRadioHeadRF95 fork, distributable form

This is a slightly rewritten fork from [exmorse](https://github.com/exmorse/pyRadioHeadRF95). Effort have been made into building a `setup.py` able to build the radiohead c++ sources to a dynamic library, and linking CFFI in order to have a clean and pip-distributable python library.

## Non-python Requirements

- bcm2835 (http://www.airspayce.com/mikem/bcm2835)

bcm2835 have to be installed first, with the following steps (up to you to change the bcm2835 version, it has been tested with the one below):

```bash
cd /tmp/
wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.57.tar.gz .
tar zxvf bcm2835-1.xx.tar.gz
cd bcm2835-1.xx
./configure
make
sudo make check
sudo make install
```

## `pyradiohead_rf95` installation

The last version can be installed via github (may be release later on pipy, but only if allowed by the main library author).

`pip install git+git://github.com/celliern/pyradiohead_rf95`

## Writing programs using `pyradiohead_rf95`

- Import the module: ```from pyradiohead_rf95 import RF95```


### Using directly the Driver with no Manager

- Instantiate an object of the ```RF95``` class: ```rf95 = RF95()```
- Call the initalizer: ```rf95.init()```
- Set the frequency: ```rf95.set_frequency(<FREQ>)```
- Set radio transmission power: ```rf95.set_tx_power(<dBm>, <useRFO>)```

#### Configuring Bandwidth

Done via the method ```rf95.set_signal_bandwidth(<BW>)```

Possible values are

- bandwidth7_k8_hz = 7800
- bandwidth10_k4_hz = 10400
- bandwidth15_k6_hz = 15600
- bandwidth20_k8_hz = 20800
- bandwidth31_k25_hz = 31250
- bandwidth41_k7_hz = 41700
- bandwidth62_k5_hz = 62500
- bandwidth125_khz = 125000
- bandwidth250_khz = 250000
- bandwidth500_khz = 500000

#### Configuring Spreading Factor 

Done via the method ```rf95.set_spreading_factor(<SF>)```

Possible values are:

- spreading_factor6 = 6
- spreading_factor7 = 7
- spreading_factor8 = 8
- spreading_factor9 = 9
- spreading_factor10 = 10
- spreading_factor11 = 11
- spreading_factor12 = 12

#### Configuring Coding Rate

Done via the method ```rf95.set_coding_rate4(<CR_DEN>)```

Possible values are:

- coding_rate4_5 = 5
- coding_rate4_6 = 6
- coding_rate4_7 = 7
- coding_rate4_8 = 8

#### Sending and Receiving

```python
rf95.send(msg, len(msg))  
rf95.waitPacketSent()  

if rf95.available():  
    (msg, l) = rf95.recv()
```

### Using the ReliableDatagram Manager

- Instantiate an object of the ```RF95``` class: ```rf95 = RF95()``` and initialize it as explained above
- Call the initalizer: ```rf95.manager_init(<MY_ADDRESS>)```, where the address is an integer

#### Sending and Receiving with the ReliableDatagram Manage

```python
    rf95.sendto_wait(msg, len(msg), destination)  

    if rf95.available():  
         (msg, l, source) = rf95.recvfrom_ack()
```

## Running Examples

Once the package is compiled run:

```bash
    sudo ./examples/rf_server.py
```

or

```bash
    sudo ./examples/rf_reliable_server.py
```