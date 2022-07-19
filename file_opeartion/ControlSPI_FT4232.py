#!/usr/bin/env python 
# -*- coding: utf-8 -*-
'''
Time    : 2022/06/16 13:59
Author  : zhuchunjin
Email   : chunjin.zhu@taurentech.net
File    : ControlSPI_FT4232.py
Software: PyCharm
'''
from pyftdi.ftdi import Ftdi
from pyftdi.gpio import (GpioAsyncController,
                         GpioSyncController,
                         GpioMpsseController)
from pyftdi.spi import SpiController, SpiIOError

from binascii import hexlify

class spi_attribute:
    freq = 30000000
    cs = 0
    mode = 0
    cpol = 0
    cpha = 0
    tranbits = 8
    chn = 0
