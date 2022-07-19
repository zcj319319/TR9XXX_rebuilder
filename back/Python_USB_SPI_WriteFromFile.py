"""
Program test environment
Pyhone version:3.4.1
Firmware version:2.2.12
Dependent files(MacOSX):libGinkgo_Driver.dylib,libusb-0.1.4.dylib,libusb-1.0.0.dylib,ControlSPI.py
Dependent files(Windows):Ginkgo_Driver.dll,ControlSPI.py
Dependent files(Linux):libGinkgo_Driver.so,libusb-1.0.so,ControlSPI.py
More Infomation:www.viewtool.com
"""
from ctypes import *
# Import module
from file_opeartion import ControlSPI

# Scan device
nRet = ControlSPI.VSI_ScanDevice(1)
if(nRet <= 0):
    print("No device connect!")
    exit()
else:
    print("Connected device number is:"+repr(nRet))

# Open device
nRet = ControlSPI.VSI_OpenDevice(ControlSPI.VSI_USBSPI, 0, 0)
if(nRet != ControlSPI.ERR_SUCCESS):
    print("Open device error!")
    exit()
else:
    print("Open device success!")
# Initialize device
SPI_Init = ControlSPI.VSI_INIT_CONFIG()
SPI_Init.ClockSpeed = 450000;
SPI_Init.ControlMode = 1;
SPI_Init.CPHA = 0;
SPI_Init.CPOL = 0;
SPI_Init.LSBFirst = 0;
SPI_Init.MasterMode = 1;
SPI_Init.SelPolarity = 0;
SPI_Init.TranBits = 8;

nRet = ControlSPI.VSI_InitSPI(ControlSPI.VSI_USBSPI, 0, byref(SPI_Init))
if(nRet != ControlSPI.ERR_SUCCESS):
    print("Initialization device error!")
    exit()
else:
    print("Initialization device success!")


write_buffer = (c_ubyte * 1024)()
read_buffer = (c_ubyte * 4096)()

write_buffer[0] = 0x86
write_buffer[1] = 0x04
write_buffer[2] = 0x87
write_buffer[3] = 0x00
write_buffer[4] = 0x00
write_buffer[5] = 0x00
nRet = ControlSPI.VSI_WriteReadBytes(ControlSPI.VSI_USBSPI, 0, 0, write_buffer, 6, read_buffer, 2)

if(nRet != ControlSPI.ERR_SUCCESS):
	print("Write&Read data error :%d"%nRet)
	exit()
else:
	print("Read data(Hex):")

if(read_buffer[0] == 0x04):
    print("clock reset succuss!")
else:
    print("clock reset fail!")

write_buffer[0] = 0xc1
write_buffer[1] = 0x00
write_buffer[2] = 0x00
write_buffer[3] = 0x20
write_buffer[4] = 0x00
write_buffer[5] = 0x00
fp = open('data_mem.out', 'w')
#nRet = ControlSPI.VSI_WriteBytes(ControlSPI.VSI_USBSPI,0,0,write_buffer,2)
nRet = ControlSPI.VSI_WriteReadBytes(ControlSPI.VSI_USBSPI, 0, 0, write_buffer, 6, read_buffer, 4096)
if(nRet != ControlSPI.ERR_SUCCESS):
	print("Write&Read data error :%d"%nRet)
	exit()
else:
	print("Read data from spi:")

for i in range(0,4096):
    fp.write("%02X "%(read_buffer[i]))
#print("%02X "%(read_buffer[i]))
print("Write data to file data_mem.out")




















