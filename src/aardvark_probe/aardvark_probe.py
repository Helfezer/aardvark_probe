#!/usr/bin/python3

from aardvark_py import *
from enum import Enum
import logging
import toml

class pinConfig(Enum):
    GPIO_ONLY = AA_CONFIG_GPIO_ONLY
    SPI_ONLY  = AA_CONFIG_SPI_GPIO 
    I2C_ONLY  = AA_CONFIG_GPIO_I2C 
    SPI_I2C   = AA_CONFIG_SPI_I2C   

class GpioBits(Enum):
    AA_GPIO_SCL_Pin_1	= 0
    AA_GPIO_SDA_Pin_3	= 1
    AA_GPIO_MISO_Pin_5	= 2
    AA_GPIO_SCK_Pin_7	= 3
    AA_GPIO_MOSI_Pin_8	= 4
    AA_GPIO_SS_Pin_9	= 5

def SetGpioMask(array: dict, pin: GpioBits, enable: bool):
    array[pin] = int(enable)

def GetGpioMask(array: dict):
    return sum(array[gpio] << gpio.value for gpio in GpioBits)

def TranslateGpioMask(array: dict, mask: int):
    for gpio in GpioBits:
        array[gpio] = (mask & (1 << gpio.value)) >> gpio.value

# -----------------------------------------------------------------------------

class probe:
    def __init__(self, Conf=None):
        self.SerialId = 0
        self.aa_handler = None
        self.port = None

        self.__aa_spi = self.aardvark_spi(self)
        self.__aa_gpio = self.aardvark_pin(self)

        self.spi = self.spi_api(self.__aa_spi)

        self.log = logging.getLogger(f"aardvark probe {self.SerialId}" )

        if Conf != None:
            self.configure(Conf)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# -----------------------------------------------------------------------------

    def configure(self, conf):
        config = toml.load(conf)

        self.SerialId = config["Probe"]["SerialId"]
        self.log = logging.getLogger(f"aardvark probe {self.SerialId}" )
        self.open()
        self.PinConfiguration(pinConfig[config["Probe"]["EnablePin"]])

        self.__aa_spi.Configure(config["SPI"])
        self.__aa_gpio.Configure(config)

# -----------------------------------------------------------------------------

    def device_discorvery(self):
        '''DEVICE DISCOVERY'''
        # Run a simple discovery
        MAX_NUMBER_OF_DEVICE_TO_DETECT=8
        aa_devices_extended = aa_find_devices_ext(MAX_NUMBER_OF_DEVICE_TO_DETECT, MAX_NUMBER_OF_DEVICE_TO_DETECT)

        #
        number_of_connected_aardvark = aa_devices_extended[0]
        if number_of_connected_aardvark == 0:
            raise Exception("No aardvark found")

        self.log.debug(f"number of connected aardvark {number_of_connected_aardvark}")
        self.log.debug(f"Found devices : {aa_devices_extended}")
        # Get the index of the port of the aardvark we want to control
        index_of_the_port=0
        try:
            index_of_the_port = aa_devices_extended[2].index(self.SerialId)
        except ValueError:
            raise Exception(f"Aadvark with serial id {self.SerialId} not connected")

        # take the port of the first device found
        self.port = aa_devices_extended[1][index_of_the_port]

# -----------------------------------------------------------------------------

    def open(self):       
        self.device_discorvery()
        self.aa_handler = aa_open(self.port)
        self.log.info(f"open aardvark on port {self.port}")
        if self.aa_handler < 0:
            self.log.error(f"error opening aardvark '{aa_status_string(self.aa_handler)}'")
            raise Exception(aa_status_string(self.aa_handler))

# -----------------------------------------------------------------------------

    def close(self):
        if self.aa_handler != None:
            self.log.debug(f"closing handler of port {self.port}")
            aa_close(self.aa_handler)

# -----------------------------------------------------------------------------

    def PinConfiguration(self, pc: pinConfig):
        '''Activate/deactivate individual subsystems (I2C, SPI, GPIO).
           e.g: If I2C deactivated: Pin can be manipulate as GPIO        
        '''
        status = aa_configure(self.aa_handler, pc.value)
        if self.aa_handler < 0:
            self.log.error(f"Pin configuration error: '{aa_status_string(status)}'")
            raise

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
    class aardvark_spi:
        def __init__(self, object):
            self.probe = object

            # Default SPI configuration

            # minimal bitrate possible (in kHz)
            self.bitrate = 125 

            # polarity = mode 0 (CPOL 0 / CPHA 0)
            self.polarity = AA_SPI_POL_RISING_FALLING
            self.phase = AA_SPI_PHASE_SAMPLE_SETUP

            self.bitorder = AA_SPI_BITORDER_MSB
            self.ss_polarity = AA_SPI_SS_ACTIVE_LOW

            self.log = logging.getLogger(f"aardvark spi {self.probe.SerialId}" )
            self.log.debug("Initialised internal SPI")

    # -----------------------------------------------------------------------------

        def ModeSelection(self, mode):
            if mode == 0:
                self.polarity = AA_SPI_POL_RISING_FALLING
                self.phase    = AA_SPI_PHASE_SAMPLE_SETUP
            elif mode == 1:
                self.polarity = AA_SPI_POL_RISING_FALLING
                self.phase    = AA_SPI_PHASE_SETUP_SAMPLE
            elif mode == 2:
                self.polarity = AA_SPI_POL_FALLING_RISING
                self.phase    = AA_SPI_PHASE_SAMPLE_SETUP
            elif mode == 3:
                self.polarity = AA_SPI_POL_FALLING_RISING
                self.phase    = AA_SPI_PHASE_SETUP_SAMPLE
            else:
                self.log.error(f"Mode {mode} does not exist")

    # -----------------------------------------------------------------------------

        def Configure(self, conf=None):
            
            if conf != None:
                self.bitrate     = conf["Bitrate"]
                self.ModeSelection(conf["Mode"])
                self.bitorder    = conf["Bitorder"]
                self.ss_polarity = conf["SsPolarity"]

            status = aa_spi_bitrate(self.probe.aa_handler, self.bitrate)
            if status < 0:
                self.log.debug(f"fail setting bitrate {self.bitrate}, ({aa_status_string(status)})")

            status = aa_spi_configure(self.probe.aa_handler, self.polarity, self.phase, self.bitorder)
            if status < 0:
                self.log.debug(f"fail spi configuration ({aa_status_string(status)})")

            status = aa_spi_slave_disable(self.probe.aa_handler)
            if status < 0:
                self.log.debug(f"fail spi slave disable ({aa_status_string(status)})")

            status = aa_spi_master_ss_polarity(self.probe.aa_handler, self.ss_polarity)
            if status < 0:
                self.log.debug(f"fail spi cs polarity ({aa_status_string(status)})")


    # -----------------------------------------------------------------------------

        def Write(self, data_out):
            miso_data = array_u08(len(data_out))
            status, miso_data = aa_spi_write(self.probe.aa_handler, data_out, miso_data)
            if status < 0:
                self.log.error(f"fail sending data ({aa_status_string(status)})")
                return None
            else:
                self.log.debug(f"data {data_out} sent on spi (MOSI)")

            self.log.debug(f"{miso_data=}")

            return miso_data

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

    class aardvark_pin:
        def __init__(self, object):
            self.probe = object
            self.Direction = dict()
            self.Pullup = dict()
            self.PinStatus = dict()
            
            for gpio in GpioBits:
                self.Pullup[gpio] = 0
                self.Direction[gpio] = 0
                self.PinStatus[gpio] = 0

            self.log = logging.getLogger(f"aardvark pin {self.probe.SerialId}" )

    # -----------------------------------------------------------------------------

        def Configure(self, conf):
            
            for gpio in GpioBits:
                self.Direction[gpio] = conf["Direction"][gpio.name]
                self.Pullup[gpio]    = conf["PullUp"][gpio.name]

            status = aa_gpio_direction(self.probe.aa_handler, GetGpioMask(self.Direction))
            if status < 0:
                self.log.debug(f"fail getting pin direction, ({aa_status_string(status)})")

            status = aa_gpio_pullup(self.probe.aa_handler, GetGpioMask(self.Pullup))
            if status < 0:
                self.log.debug(f"fail getting pin pullup, ({aa_status_string(status)})")

            PinBitmask = aa_gpio_get(self.probe.aa_handler)
            if PinBitmask < 0:
                self.log.debug(f"fail getting pin status, ({aa_status_string(PinBitmask)})")
            else:
                TranslateGpioMask(self.PinStatus, PinBitmask)

    # -----------------------------------------------------------------------------

        def GetPin(self, pin: GpioBits):
            PinBitmask = aa_gpio_get(self.probe.aa_handler)
            if PinBitmask < 0:
                self.log.debug(f"fail getting pin status, ({aa_status_string(PinBitmask)})")
                raise
            else:
                TranslateGpioMask(self.PinStatus, PinBitmask)

            return self.PinStatus[pin]


    # -----------------------------------------------------------------------------

        def SetPin(self, pin: GpioBits):
            SetGpioMask(self.PinStatus, pin, True)
            aa_gpio_set(self.probe.aa_handler, GetGpioMask(self.PinStatus))

    # -----------------------------------------------------------------------------

        def UnsetPin(self, pin: GpioBits):
            SetGpioMask(self.PinStatus, pin, False)
            aa_gpio_set(self.probe.aa_handler, GetGpioMask(self.PinStatus))

    # -----------------------------------------------------------------------------

        def SetOutputPin(self, pin: GpioBits):
            SetGpioMask(self.Direction, pin, True)
            aa_gpio_set(self.probe.aa_handler, GetGpioMask(self.Direction))

    # -----------------------------------------------------------------------------

        def UnsetOutputPin(self, pin: GpioBits):
            SetGpioMask(self.Direction, pin, False)
            aa_gpio_set(self.probe.aa_handler, GetGpioMask(self.Direction))

    # -----------------------------------------------------------------------------

        def SetPullUpPin(self, pin: GpioBits):
            SetGpioMask(self.Pullup, pin, True)
            aa_gpio_set(self.probe.aa_handler, GetGpioMask(self.Pullup))

    # -----------------------------------------------------------------------------

        def UnsetPullUpPin(self, pin: GpioBits):
            SetGpioMask(self.Pullup, pin, False)
            aa_gpio_set(self.probe.aa_handler, GetGpioMask(self.Pullup))
