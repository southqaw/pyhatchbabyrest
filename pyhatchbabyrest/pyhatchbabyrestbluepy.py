import time

import bluepy.btle as btle

from .pyhatchbabyrest import PyHatchBabyRest
from .constants import SERV_TX, SERV_FEEDBACK, PyHatchBabyRestSound


class PyHatchBabyRestBluePy(PyHatchBabyRest):
    def __init__(self, addr=None):
        self.peripheral = btle.Peripheral()
        self.peripheral.connect("fc:f2:86:26:f5:67", addrType=btle.ADDR_TYPE_RANDOM)
        self._write_service = self.peripheral.getServiceByUUID(SERV_TX)
        self._read_service = self.peripheral.getServiceByUUID(SERV_FEEDBACK)

        self.write_char = self._write_service.getCharacteristics()[0]
        self.read_char = self._read_service.getCharacteristics()[0]

    def _send_command(self, command: str):
        """ Send a command to the device.

        :param command: The command to send.
        """
        self.write_char.write(bytearray(command, "utf-8"))
        time.sleep(0.25)
        self._refresh_data()

    def _refresh_data(self) -> None:
        """ Request updated data from the device and set the local attributes. """
        response = [hex(x) for x in list(self.read_char.read())]

        # Make sure the data is where we think it is
        assert response[5] == "0x43"  # color
        assert response[10] == "0x53"  # audio
        assert response[13] == "0x50"  # power

        red, green, blue, brightness = [int(x, 16) for x in response[6:10]]

        sound = PyHatchBabyRestSound(int(response[11], 16))

        volume = int(response[12], 16)

        power = not bool(int("11000000", 2) & int(response[14], 16))

        self.color = (red, green, blue)
        self.brightness = brightness
        self.sound = sound
        self.volume = volume
        self.power = power

    def disconnect(self):
        return self.peripheral.disconnect()

    @property
    def connected(self):
        conn = False
        try:
            if self.peripheral.getState() == 'conn':
                conn = True
        except btle.BTLEInternalError:
            conn = False
        return conn
