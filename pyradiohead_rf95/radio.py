#!/usr/bin/env python
# coding=utf-8

import logging
from collections import namedtuple
from queue import Queue, PriorityQueue, Empty
from threading import Lock, Thread, Event, Timer
import time
import attr
import ujson
from collections import deque
from retrying import retry
from itertools import cycle
from typing import Tuple, Any, Dict, Callable, Optional, List

from pyradiohead_rf95 import RF95

logger = logging.getLogger(__name__)

TAIL_SIZE = 256

msg_id_cycle = cycle(range(TAIL_SIZE))


class NotReadyException(Exception):
    """Raised when the radio is not ready to transmit or receive."""
    pass


@attr.s(frozen=True)
class InputMessage:
    """ Container for message received by the radio.

    Returns:
        InputMessages
    """

    id = attr.ib(type=int)
    timestamp = attr.ib(type=int)
    payload = attr.ib(type=Any, cmp=False)
    source = attr.ib(type=int)
    dest = attr.ib(type=int)

    @staticmethod
    def from_raw(raw: Tuple[bytes, int, int, Dict]):
        raw_data, length, source, extras = raw
        logger.debug(
            "convert raw info < %s (%s), %s > in message" % (
                raw_data, length, source)
        )
        try:
            data = ujson.loads(raw_data[:length].decode())
            payload = data["payload"]
            timestamp = data["timestamp"]
            id = data["id"]
            dest = extras["dest"]
            return InputMessage(
                id=id, timestamp=timestamp, source=source, dest=dest, payload=payload
            )
        except Exception:
            logger.debug(
                "Unable to convert raw info < %s (%s), %s > in message"
                % (raw_data, length, source)
            )
            return


@attr.s(frozen=True)
class OutputMessage:
    destination = attr.ib(cmp=False, type=int)
    payload = attr.ib(cmp=False, type=Any)
    id = attr.ib(factory=lambda: next(msg_id_cycle), type=int)
    timestamp = attr.ib(factory=lambda: int(time.time()), type=int)
    priority = attr.ib(default=0, type=int)

    @property
    def raw(self):
        logger.debug("process message %s in raw info" % self)
        return self.serialized_data, len(self.serialized_data), self.destination

    @property
    def serialized_data(self):
        return ujson.dumps(
            dict(id=self.id, timestamp=self.timestamp, payload=self.payload)
        ).encode()

    def __len__(self):
        return len(self.serialized_data)


class Radio:
    """Radio main class : wrap the low level pyradiohead that is in charge to communicate with the LORA
        transmitter / receiver.
        It consists into three components:

        - A transmitter
        - A receiver
        - A listen / send switch

        The Transmitter take the messages to send, and put it into a queue.PriorityQueue. Whenever the state of the
        radio is "sending", it starts transmit the higher level priority messages.

        The Receiver check if there is an incomming message from the LORA card and add them to an another queue.Queue,
        after what the user can freely retrieve them.

        The StateSwitch schedule the part of the time dedicated to listening and the one to sending the messages.
        It consists into a threading. Timer that trigger the change of the radio state, waiting the proper time,
        and doing that perpetually.

        Args:
            address (int): Address of this radio
            bandwidth (int, optional): Defaults to 434. Emission bandwidth
            listening_sending_cyle (float, optional): Defaults to 1. Duration of one listening / sending cycle.
            listening_ratio (float, optional): Defaults to 0.5. Part of that cycle that is dedicated to listening.
        """

    def __init__(
        self,
        address: int,
        bandwidth: int = 434,
        listening_sending_cyle: float = 1,
        listening_ratio: float = 0.5,
        turn_on=True
    ):

        self.address = address
        self.bandwidth = bandwidth
        self.listening_ratio = listening_ratio
        self.listening_sending_cycle = listening_sending_cyle

        self.receiver = Receiver(self)
        self.transmitter = Transmitter(self)

        self._is_on = Event()
        self._sending = Event()
        self._listening = Event()
        self.lock = Lock()

        self.on()

    def on(self):
        """Turn on the radio. The steps are:

        - initialization of the low-lever radiohead interface
        - starting the receiver and the transmitter
        - start the listen / send switch
        """

        if not self.is_on:
            logger.info("turning on the radio")

            logger.debug("initialize radiohead interface")
            self._rh_interface = RF95()
            self._rh_interface.init()
            self._rh_interface.manager_init(self.address)
            self._rh_interface.set_frequency(self.bandwidth)
            self._rh_interface.set_tx_power(14, False)
            # The event _is_on has to be set before starting the receiver and the transmitter.
            # They quit their loops when that event is cleared.
            self._is_on.set()
            logger.debug("starting receiver and transmitter")
            self.receiver.start()
            self.transmitter.start()

            logger.debug(
                "setup alternance cycle for listening / sending time.")
            self.state_switch = StateSwitch(
                self, self.listening_sending_cycle, self.listening_ratio
            )
            logger.info("radio is on")

    def off(self):
        """Turn the radio off. The steps are:

        - clearing the _is_on event (so the transmitter and receiver quit their loops)
        - properly terminating the transmitter and receiver
        - cancel the state switch
        - recreate the receiver and transmitter so they can be started when the radio is turned on again.
        """
        if self.is_on:
            logger.info("turning off the radio")
            self._is_on.clear()
            self.receiver.join()
            self.transmitter.join()
            self.state_switch.cancel()
            logger.info("radio is off")

            self.receiver = Receiver(self)
            self.transmitter = Transmitter(self)

    @property
    def state(self):
        if self.listening:
            return "listening"
        else:
            return "sending"

    @state.setter
    def state(self, value: str):
        if value == "listening":
            self.listening = True
            self.sending = False
            return
        if value == "sending":
            self.sending = True
            self.listening = False
            return
        else:
            raise ValueError(
                "State not valid : should be 'listening' or 'sending'")

    def toggle_state(self):
        if self.state == "listening":
            self.state = "sending"
            return

        if self.state == "sending":
            self.state = "listening"
            return

    @property
    def is_on(self):
        return self._is_on.is_set()

    @is_on.setter
    def is_on(self, value: bool):
        if value:
            self.on()
        else:
            self.off()

    @property
    def sending(self):
        return self._sending.is_set()

    @sending.setter
    def sending(self, value: bool):
        if value:
            self._sending.set()
        else:
            self._sending.clear()

    @property
    def listening(self):
        return self._listening.is_set()

    @listening.setter
    def listening(self, value: bool):
        if value:
            self._listening.set()
        else:
            self._listening.clear()

    def send(
        self, data: Any, destination: int, priority: int = 0, wait: bool = False
    ):
        """Send a message to another device.

        Behind the hood, it add a message to the transmitter queue.
        The priority can be set thanks to the dedicated argument,
        and the highest priority will be sent first.
        By default, this call does not block, until the wait parameter
        is set to True.
        If the address is set to 255, the message will be broadcasted: 
        every devices will receive the message and no acknowledgelent
        will be sent back.

        Args:
            data (Any): The core data that will be transmitted.
            destination (int). The address of the device to reach.
            priority (int, optional): Defaults to 0. low value means high prority.
            wait (bool, optional): Defaults to False. If true, the call blocks until the transmitter queue is empty.

        Raises:
            NotReadyException: Raised if the radio is off.
        """

        if not self.is_on:
            raise NotReadyException(
                "Radio is off. Try radio.on() before sending a message."
            )
        self.transmitter.add_to_queue(data, destination, priority, wait)

    def receive(self, timeout: float = 1):
        """Get a message in the order of arrival in the Receiver Queue.
        The call block until a message is available or the timeout is reached.

        Args:
            timeout (float, optional): Defaults to 1 (sec).

        Raises:
            NotReadyException: Raised if the radio is off.

        Returns:
            InputMessage: the next message available.
        """

        if not self.is_on and self.receiver.incoming_messages.empty():
            raise NotReadyException(
                "Radio is off and receiver queue is empty. "
                "Try radio.on() before receiving a message."
            )
        return self.receiver.get_one(timeout=timeout)

    def receive_all(self):
        """Get all the messaged available in the Receiver.

        Raises:
            NotReadyException: [description]

        Returns:
            List[InputMessage]: all the messages available in the Receiver Queue.
        """

        if not self.is_on and self.receiver.incoming_messages.empty():
            raise NotReadyException(
                "Radio is off and receiver queue is empty. "
                "Try radio.on() before receiving a message."
            )
        return list(self.receiver.get_all())

    # TODO: put that in the receiver and making it an iterator.
    @property
    def receiver_stream(self):
        if not self.is_on and self.receiver.incoming_messages.empty():
            raise NotReadyException(
                "Radio is off and receiver queue is empty. "
                "Try radio.on() before receiving a message."
            )
        return self.receiver.stream()

    def discover(self, timeout=10):
        """Ask every devices to send an answer.
            timeout (int, optional): Defaults to 10. Time let to the device to answer the request.

        Returns:
            List[int]: the list of active devices addresses.
        """

        logger.info("launch discover, broadcast report signal")
        self.transmitter.broadcast("report")
        self.state_switch.cancel()
        self.state = "listening"
        start_discovery = time.time()
        available_devices = []
        for message in self.receiver_stream:
            if message.payload == "alive":
                logger.info("discovered device %i" % message.source)
                available_devices.append(message.source)
            else:
                self.receiver.incoming_messages.put((1, message))
            if time.time() - start_discovery > timeout:
                self.state_switch._set_listening()
                return available_devices

    def lock_radio(self):
        """Lock the radio (which will be unable to send or receive until released).
        """

        logger.debug("lock the radio interface")
        self.lock.acquire()

    def release_radio(self):
        """Unlock the radio (which will be able to send or receive again).
        """

        logger.debug("release the radio interface")
        self.lock.release()

    def lock_radio_for(self, lock_time: float):
        """Lock the radio for a time, then releases it.

        Args:
            lock_time (float): time (in sec) before the radio will be released.

        Return:
            Timer: the timer that will release the radio after the lock_time. Has a cancel() method.
        """

        logger.debug("lock the radio interface for %g sec." % lock_time)
        self.lock_radio()
        Timer(lock_time, self.release_radio).start()

    def __del__(self):
        self.off()

    def loop_forever(self):
        """Give a simple loop to keep the radio alive (in order to send / receive).
        """

        while True:
            pass


def report_to_discover(message: InputMessage, radio: Radio):
    """If the input message is an ask to discover, answer immediatly.
    The message is not forwarded to the radio.

    Args:
        message (InputMessage)
        radio (Radio)

    Returns:
        Optional[InputMessage]: return None if the message was a discovering one, forward the message otherwise.
    """

    if message.payload == "report":
        radio.send("alive", message.source, priority=-9)
        return
    return message


class Receiver(Thread):
    """__init__ [summary]

    Args:
        radio (Radio): [description]
        history_size (int, optional): Defaults to 255. [description]
    """

    daemon = True

    def __init__(self, radio: Radio, history_size: int = 255):

        self.radio = radio
        self.incoming_messages = PriorityQueue()  # type: ignore
        self.message_history = deque([], history_size)  # type: ignore
        self.callbacks = [
            ("report_to_discover", report_to_discover)
        ]  # type: List[Tuple[str, Callable[[InputMessage, Radio], Optional[InputMessage]]]]
        self.callbacks = []
        super().__init__()

    def register_callback(
        self, name, callback: Callable[[InputMessage, Radio], Optional[InputMessage]]
    ):
        """register_callback [summary]

        Args:
            name ([type]): [description]
            callback (Callable[[InputMessage, Radio], Optional[InputMessage]]): [description]
        """

        self.callbacks.append((name, callback))

    def check_destination(self, message: InputMessage):
        """check_destination [summary]

        Args:
            message (InputMessage): [description]

        Returns:
            [type]: [description]
        """

        if message.dest not in [self.radio.address, 255]:
            return False
        return True

    def check_duplicate(self, message: InputMessage):
        """check_duplicate [summary]

        Args:
            message (InputMessage): [description]

        Returns:
            [type]: [description]
        """

        if message in self.message_history:
            return False
        return True

    def get_one(self, timeout: float = 1):
        """get_one [summary]
            timeout (float, optional): Defaults to 1. [description]

        Returns:
            [type]: [description]
        """

        try:
            _, msg = self.incoming_messages.get(timeout=timeout)
            return msg
        except Empty:
            return None

    def get_all(self):
        """get_all [summary]
        """

        while not self.incoming_messages.empty():
            yield self.incoming_messages.get()

    def stream(self):
        """stream [summary]
        """

        while True:
            msg = self.get_one(0)
            if msg is not None:
                yield msg

    def _apply_callbacks(self, message):
        """_apply_callbacks [summary]

        Args:
            message ([type]): [description]

        Returns:
            [type]: [description]
        """

        for name, callback in self.callbacks:
            logger.info("using callback < %s > in the message." % name)
            message = callback(message, self.radio)
        return message

    def _retrieve(self):
        """_retrieve [summary]
        """

        with self.radio.lock:
            if not self.radio._rh_interface.available:
                return
            raw = self.radio._rh_interface.recvfrom_ack()
        message = InputMessage.from_raw(raw)
        logging.debug("receiving message from %i" % message.source)
        message = self._apply_callbacks(message)
        if message is None:
            return
        if self.check_destination(message) and self.check_duplicate(message):
            logger.info("message %s retrieved." % message)
            self.message_history.append(
                (message.source, message.id, message.timestamp))
            self.incoming_messages.put((0, message))

    def run(self):
        while self.radio.is_on and self.radio._listening.wait():
            self._retrieve()


class Transmitter(Thread):
    """__init__ [summary]

    Args:
        radio (Radio): [description]
    """

    daemon = True

    def __init__(self, radio: Radio):
        """__init__ [summary]

        Args:
            radio (Radio): [description]
        """

        self.to_send_messages = PriorityQueue()  # type: ignore
        self.radio = radio
        super().__init__()

    def transmit(self):
        """transmit [summary]

        Raises:
            ValueError: [description]
        """

        try:
            priority, data, destination = self.to_send_messages.get_nowait()
        except Empty:
            return
        message = OutputMessage(
            payload=data, destination=destination, priority=priority
        )
        logger.info("sending the message %s" % message)

        @retry(
            wait_exponential_multiplier=100,
            wait_exponential_max=3000,
            stop_max_attempt_number=5,
        )
        def send_one(message: OutputMessage):
            """send_one [summary]

            Args:
                message (OutputMessage): [description]

            Raises:
                ValueError: [description]
            """

            with self.radio.lock:
                if not self.radio._rh_interface.available:
                    return
                ack = self.radio._rh_interface.sendto_wait(*message.raw)
            if ack == -1:
                raise ValueError("ack not received")

        try:
            send_one(message)
            logger.debug("message %s sent" % message)
        except ValueError:
            logging.warning("message transmission < %s > failed" % message)

    def broadcast(self, data: Any, priority: int = -1):
        """broadcast [summary]

        Args:
            data (Any): [description]
            priority (int, optional): Defaults to -1. [description]
        """

        message = OutputMessage(payload=data, destination=255)
        logger.debug("broadcast message %s." % message)
        self.to_send_messages.put((priority, data, 255))

    def add_to_queue(
        self, data: Any, destination: int, priority: int = 1, wait: bool = False
    ):
        """add_to_queue [summary]

        Args:
            data (Any): [description]
            destination (int): [description]
            priority (int, optional): Defaults to 1. [description]
            wait (bool, optional): Defaults to False. [description]
        """

        logger.debug("add the message %s to %s to the queue." %
                     (data, destination))
        self.to_send_messages.put((priority, data, destination))
        if not wait:
            return
        while not self.to_send_messages.empty():
            pass

    def run(self):
        while self.radio.is_on and self.radio._sending.wait():
            self.transmit()


class StateSwitch:
    """__init__ [summary]

    Args:
        radio (Radio): [description]
        duty_time (float, optional): Defaults to 1. [description]
        listening_ratio (float, optional): Defaults to 0.5. [description]
    """

    def __init__(
        self, radio: Radio, duty_time: float = 1, listening_ratio: float = 0.5
    ):
        """__init__ [summary]

        Args:
            radio (Radio): [description]
            duty_time (float, optional): Defaults to 1. [description]
            listening_ratio (float, optional): Defaults to 0.5. [description]
        """

        self.radio = radio
        self.cancel()
        self._listening_time = duty_time * listening_ratio
        self._sending_time = duty_time * (1 - listening_ratio)
        self._set_listening()

    def cancel(self):
        try:
            self._toggle_timer.cancel()
        except (AttributeError, NameError):
            pass

    def __del__(self):
        self.cancel()

    def _set_listening(self):
        """_set_listening [summary]
        """

        self.cancel()
        self.radio.state = "listening"
        self._toggle_timer = Timer(self._listening_time, self._set_sending)
        self._toggle_timer.daemon = True
        self._toggle_timer.start()

    def _set_sending(self):
        """_set_sending [summary]
        """

        self.cancel()
        self.radio.state = "sending"
        self._toggle_timer = Timer(self._sending_time, self._set_listening)
        self._toggle_timer.daemon = True
        self._toggle_timer.start()
