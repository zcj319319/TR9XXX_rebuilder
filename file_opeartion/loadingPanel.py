#!/usr/bin/env python 
# -*- coding: utf-8 -*-
'''
Time    : 2022/06/14 18:10
Author  : zhuchunjin
Email   : chunjin.zhu@taurentech.net
File    : loadingPanel.py
Software: PyCharm
'''
import ctypes
import inspect
import os
import re
import threading
import time
from ctypes import *

import numpy as np
import openpyxl
import xlrd
import xlwt
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QDir
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

# from file_opeartion import ControlSPI
from file_opeartion.ClkOptDialog import ClkOptDialog
from file_opeartion.ControlSPI_FT4232 import spi_attribute
from file_opeartion.mainDialog1 import MainDialog1
from redesigner_ui.ui import Ui_MainWindow
from pyftdi.ftdi import Ftdi
from pyftdi.gpio import (GpioAsyncController,
                         GpioSyncController,
                         GpioMpsseController)
from pyftdi.spi import SpiController, SpiIOError

from binascii import hexlify
from redesigner_ui import logo_rc
from redesigner_ui import status_rc
from redesigner_ui import struc_rc
from redesigner_ui import xxx_rc
from redesigner_ui import head_rc


class LoadingPanel(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.log_textBrowser.setText("{0} initializing...".format(time.strftime("%F %T")))
        self.label_8.setPixmap(QtGui.QPixmap(":/head/head.png"))
        self.clk_option_cfg_button.clicked.connect(self.clk_opt_cfg)
        self.ddc_config()
        self.nco_update_pushButton.clicked.connect(self.nco_update)
        self.j204b_config()
        self.j204b_update_pushButton.clicked.connect(self.j204b_update)
        self.sds_config()
        self.sds_button.clicked.connect(self.sds_update)
        self.sds_button_2.clicked.connect(self.sds_test_prbs7)
        self.sds_button_3.clicked.connect(self.sds_test_clk0101)
        self.read_button.clicked.connect(self.read_addr)
        self.write_button.clicked.connect(self.write_addr)
        self.init_button.clicked.connect(self.load_test_seq)
        self.mem_rd_button.clicked.connect(self.mem_read)
        # self.spi_config()
        self.pushButton.clicked.connect(self.spi_update)
        self.push_button_cnt = 'start'
        self.clk_opt_cfg_param = []
        self.sheet_sel_lst = ""
        self.url_port = []
        self.port = []
        self.spi_a = None
        try:
            self.init_spi_config()
        except Exception as e:
            QMessageBox.information(self, 'warning', '%s' % e)
        self.clear_log_btn.clicked.connect(self.clear_log_content)
        self.view_all_log_btn.clicked.connect(self.get_log_content)

    def init_spi_config(self):
        self.lineEdit.setText('30')
        self.lineEdit_2.setText('8')
        Ftdi.show_devices()
        dev_urls = Ftdi.list_devices()
        # Scan device
        if len(dev_urls) == 0:
            self.label_6.setPixmap(QtGui.QPixmap(":/status/OFF.png"))
        else:
            self.label_6.setPixmap(QtGui.QPixmap(":/status/on.png"))
            for i in range(dev_urls[0][1]):
                self.url_port.append(
                    r'ftdi://ftdi:4232:' + str(dev_urls[0][0].bus) + ':' + str(
                        hex(dev_urls[0][0].address)) + r'/' + str(
                        i + 1))
            self.port.append(SpiController())
            self.port[0].configure(self.url_port[0], cs_count=1)
            self.port.append(SpiController())
            self.port[1].configure(self.url_port[1], cs_count=1)
            self.port.append(GpioAsyncController())
            self.port[2].configure(self.url_port[2], direction=0xff, initial=0x83)
            self.port.append(GpioAsyncController())
            self.port[3].configure(self.url_port[3], direction=0x00, initial=0x0)
            # Set channelA
            dq = spi_attribute
            self.spi_a = self.port[dq.chn].get_port(dq.cs)
            self.spi_a.set_frequency(dq.freq)
            self.spi_a.set_mode(dq.mode)
            self.textBrowser_normal_log('available device is %s' % ','.join(self.url_port))

    def textBrowser_normal_log(self, info):
        self.log_textBrowser.append("{0} {1}".format(time.strftime("%F %T"), info))

    def textBrowser_error_log(self, info):
        self.log_textBrowser.append("<font color='red'>" + '{0} {1}'.format(time.strftime("%F %T"), info))

    """
    FT4232H write and read
    """

    def write_atom(self, addr, data, flag=None):
        addr_str_1 = '%#x' % addr
        data_str_1 = '%#x' % data
        self.textBrowser_normal_log('write addr = ' + addr_str_1 + ' data = ' + data_str_1)
        try:
            write_buffer = []
            addr_str = addr_str_1.split('x')[1]
            if len(addr_str) != 4:
                new_addr = '0' * (4 - len(addr_str)) + addr_str
            else:
                new_addr = addr_str
            write_buffer.append(int(new_addr[0:2], 16))
            write_buffer.append(int(new_addr[2:], 16))
            write_buffer.append(int(data_str_1.split('x')[1], 16))
            self.spi_a.write(write_buffer, 1)
            if flag is None:
                self.textBrowser_normal_log('write addr = ' + addr_str_1 + ' data = ' + data_str_1)
        except Exception as e:
            self.textBrowser_error_log('write_atom err:%s' % e)

    def read_atom(self, addr, flag=None):
        addr_str_1 = '%#x' % addr
        try:
            write_buffer = []
            read_buffer = []
            addr_str = addr_str_1.split('x')[1]
            if len(addr_str) != 4:
                new_addr = '0' * (4 - len(addr_str)) + addr_str
            else:
                new_addr = addr_str
            write_buffer.append(int(new_addr[0:2], 16) + 128)
            write_buffer.append(int(new_addr[2:], 16))
            read_data = self.spi_a.exchange(write_buffer, 1)
            read_buffer.append(read_data)
            read_data_str = hex(int(hexlify(read_data).decode(), 16))
            if flag is None:
                info = 'read addr = ' + addr_str + ' data = ' + read_data_str
                self.textBrowser_normal_log(info)
            return read_buffer
        except Exception as e:
            print(e)

    # def write_atom(self, addr, data, flag=None):
    #     write_buffer = (c_ubyte * 3)()
    #     read_buffer = (c_ubyte * 1)()
    #     addr_str = '{:0>4x}'.format(addr)
    #     data_str = '{:0>4x}'.format(data)
    #     write_buffer[0] = int(addr_str[0:2], 16)
    #     write_buffer[1] = int(addr_str[2:], 16)
    #     write_buffer[2] = data
    #     if flag is None:
    #         self.textBrowser_normal_log('write addr = ' + addr_str + ' data = ' + data_str)
    #     nRet = ControlSPI.VSI_WriteBytes(ControlSPI.VSI_USBSPI, 0, 0, write_buffer, 3)

    # def read_atom(self, addr, flag=None):
    #     write_buffer = (c_ubyte * 2)()
    #     read_buffer = (c_ubyte * 1)()
    #     addr_str = '{:0>4x}'.format(addr)
    #     write_buffer[0] = int(addr_str[0:2], 16) + 128
    #     write_buffer[1] = int(addr_str[2:], 16)
    #     nRet = ControlSPI.VSI_WriteReadBytes(ControlSPI.VSI_USBSPI, 0, 0, write_buffer, 2, read_buffer, 1)
    #     if flag is None:
    #         info = 'read addr = ' + addr_str + ' data = ' + str(read_buffer[0])
    #         self.textBrowser_normal_log(info)
    #     return read_buffer

    def read_addr(self):
        now_addr = self.addr_textEdit.text()
        try:
            if re.match('^0x', now_addr):
                addr_read = int(now_addr, 16)
            else:
                addr_read = int(now_addr)
            read_value = self.read_atom(addr_read)
            self.textEdit.setText(hex(int(hexlify(read_value[0]).decode(), 16)))
            # read_value_bin = '{:0>8b}'.format(read_value[0])
        except Exception as e:
            self.textBrowser_error_log('read pushbutton pressed exists err:%s' % e)

    def write_addr(self):
        now_addr = self.addr_textEdit.text()
        try:
            if re.match('^0x', now_addr):
                addr_write = int(now_addr, 16)
            else:
                addr_write = int(now_addr)
            now_value = self.textEdit.text()
            if re.match('^0x', now_value):
                write_value = int(now_value, 16)
            else:
                write_value = int(now_value)
            # write_value_bin = '{:0>8b}'.format(write_value)
            self.write_atom(addr_write, write_value)
        except Exception as e:
            self.textBrowser_error_log('write pushbutton pressed err:%s' % e)

    def load_test_seq(self):
        test_seq_file, filetype = QFileDialog.getOpenFileName(self, "choose file", "./",
                                                              "All Files (*);;excel Files (*.xlsx);;excel Files (*.xls)")  # 设置文件扩展名过滤,注意用双分号间隔
        if test_seq_file == "":
            return
        else:
            self.textBrowser_normal_log("open a file:%s" % test_seq_file)
            self.parser_seq_file(test_seq_file)

    def parser_seq_file(self, fn):
        try:
            data = xlrd.open_workbook(fn)
            sheetsall = data.sheet_names()
            dialog = MainDialog1(sheetsall)
            dialog.Signal_parp.connect(self.deal_emit_sheet)
            dialog.show()
            dialog.exec_()
            if self.sheet_sel_lst != "":
                sheet_idx = sheetsall.index(self.sheet_sel_lst)
                self.textBrowser_normal_log('%s config begin!\n' % self.sheet_sel_lst)
                sheet_data = data.sheets()[sheet_idx]
                rows_num = sheet_data.nrows
                for x in range(0, rows_num):
                    if sheet_data.cell_value(x, 0) == 'sleep':
                        if sheet_data.cell_value(x, 1) == '':
                            self.textBrowser_normal_log('sleep 5\n')
                            time.sleep(5)
                        else:
                            try:
                                tmp_time = int(sheet_data.cell_value(x, 1))
                                self.textBrowser_normal_log('sleep %s \n' % str(tmp_time))
                                time.sleep(tmp_time)
                            except:
                                self.textBrowser_error_log('Error converting character to int')
                    elif sheet_data.cell_value(x, 0) == 'wait':
                        try:
                            temp_addr = int(sheet_data.cell_value(x, 1), 16)
                            temp_value = int(sheet_data.cell_value(x, 2), 16)
                            self.textBrowser_normal_log('start read_atom address : %s' % sheet_data.cell_value(x, 1))
                            read_flag = 0
                            for i in range(0, 300):
                                self.textBrowser_normal_log('sleep 1s')
                                time.sleep(1)
                                read_value = self.read_atom(temp_addr)
                                if read_value[0] == temp_value:
                                    read_flag = 1
                                    self.textBrowser_normal_log(
                                        'end read_atom address : %s real_value:%d is equal to temp_value:%d' % (
                                            sheet_data.cell_value(x, 1), read_value[0], temp_value))
                                    break
                                else:
                                    read_flag = 0
                            if read_flag != 1:
                                self.textBrowser_normal_log('loop 300 read_atom but real_value is not equal to '
                                                            'temp_value')
                        except Exception as e:
                            self.textBrowser_error_log('%s' % e)
                    elif sheet_data.cell_value(x, 0) == '':
                        pass
                    else:
                        try:
                            temp_addr = int(sheet_data.cell_value(x, 0), 16)
                            temp_data = int(sheet_data.cell_value(x, 1), 16)
                            info = 'write addr = ' + sheet_data.cell_value(x, 0) + ' data = ' + sheet_data.cell_value(x,
                                                                                                                      1)
                            self.textBrowser_normal_log(info)
                            self.write_atom(temp_addr, temp_data)
                        except Exception as e:
                            self.textBrowser_error_log('%s' % e)
            else:
                self.textBrowser_error_log("No sheet was selected")
        except Exception as e:
            info = 'error open file:%s,please input a excel file' % fn
            self.textBrowser_error_log(info)

    def deal_emit_sheet(self, select_sheet):
        self.sheet_sel_lst = select_sheet

    #
    # def read_mem_reg(self, addr0, addr1):
    #     addr0_str = '{:0>4x}'.format(addr0)
    #     addr1_str = '{:0>4x}'.format(addr1)
    #     self.textBrowser_normal_log('read_mem_reg addr0:%s addr1:%s' % (addr0_str, addr1_str))
    #     write_buffer = (c_ubyte * 2)()
    #     read_buffer = (c_ubyte * 4096)()
    #     write_buffer[0] = addr0
    #     write_buffer[1] = addr1
    #     # nRet = ControlSPI.VSI_WriteReadBytes(ControlSPI.VSI_USBSPI, 0, 0, write_buffer, 2, read_buffer, 4096)
    #     self.read_atom(addr0_str+addr1_str)
    #     return read_buffer

    def mem_read(self):
        smp_lst = ['smp ddc output', 'smp tiskew corr', 'initial mem to 0', 'initial mem to 1', 'weight_rd']
        dialog = MainDialog1(smp_lst)
        dialog.Signal_parp.connect(self.deal_emit_sheet)
        dialog.show()
        dialog.exec_()
        if self.sheet_sel_lst in smp_lst:
            self.textBrowser_normal_log('choose %s' % self.sheet_sel_lst)
            sheet_idx = smp_lst.index(self.sheet_sel_lst)
            if sheet_idx == 0:
                # self.textBrowser.insertPlainText('start sample ddc output!\n')
                # ddc output
                self.textBrowser_normal_log('start sample ddc output!')
                try:
                    list_addr = [0xf18, 0xf16, 0xf1d, 0xf1c, 0xf16, 0xf17, 0xf19, 0xf1a, 0xf1b, 0xf1d, 0xf1c, 0xf18]
                    list_data = [0x00, 0x00, 0x1, 0x1, 0x08, 0x40, 0x3c, 0x00, 0x10, 0x0, 0x0, 0x02]
                    list_zip_addr_data = list(zip(list_addr, list_data))
                    target_write_idx1 = threading.Thread(target=self.write_thread(list_zip_addr_data))
                    target_write_idx1.start()
                except Exception as e:
                    self.textBrowser_error_log('ddc output err:' + "%s" % e)
            elif sheet_idx == 1:
                # self.textBrowser.insertPlainText('start sample tiskew_corr output!\n')
                self.textBrowser_normal_log('start sample tiskew_corr output!')
                pass
            elif sheet_idx == 2:
                # self.textBrowser.insertPlainText('start initial mem to 0!\n')
                self.textBrowser_normal_log('start initial mem to 0!')
                list_addr_data = [(0xf10, 0x0), (0xf11, 0x0)]
                self.write_thread(list_addr_data)
                target_write_idx_mem0 = threading.Thread(target=self.pressure_idx_mem0())
                target_write_idx_mem0.start()
                self.textBrowser_normal_log('end initial mem to 0!')
            elif sheet_idx == 3:
                # self.textBrowser.insertPlainText('start initial mem to 1!\n')
                self.textBrowser_normal_log('start initial mem to 1!')
                list_addr_data = [(0xf10, 0x0), (0xf11, 0x0)]
                self.write_thread(list_addr_data)
                target_write_idx_mem1 = threading.Thread(target=self.pressure_idx_mem1())
                target_write_idx_mem1.start()
                self.textBrowser_normal_log('end initial mem to 1!')
            elif sheet_idx == 4:
                self.textBrowser_normal_log('start weight_rd!')
                self.weight_rd()
            ##read mem
            if sheet_idx == 0 or sheet_idx == 1:
                addr_data_list = [(0xf16, 0x10), (0xf10, 0x01), (0xf10, 0x0), (0xf11, 0x0)]
                self.write_thread(addr_data_list)
                time.sleep(5)
                self.textBrowser_normal_log('write to memory_dump_data.txt')
                self.memory_dump_data_write()
                # target_memory_dump_data_write = threading.Thread(target=self.memory_dump_data_write())
                # target_memory_dump_data_write.start()
            if sheet_idx == 1:
                if os.path.exists('memory_dump_data.txt'):
                    target_read_memory_dump_data = threading.Thread(target=self.read_memory_dump_data())
                    target_read_memory_dump_data.start()
                else:
                    return

    def pressure_idx_mem0(self):
        for i in range(0, 131072):
            self.write_atom(0xf24, 0x0, True)

    def pressure_idx_mem1(self):
        for i in range(0, 131072):
            self.write_atom(0xf24, 0xff, True)

    def memory_dump_data_write(self):
        offset = 0x00
        data_old = 0x55
        with open('memory_dump_data.txt', 'w') as fp:
            for i in range(0, 16):
                data_new = i * 4 + offset
                self.write_atom(0xf11, data_old)
                self.write_atom(0xf11, data_new)
                read_buffer = self.read_mem_reg(0x8f, 0x24)
                for k in range(0, len(read_buffer)):
                    fp.write("%02x\n" % (read_buffer[k]))

    def read_mem_reg(self, addr0, addr1):
        read_data = self.spi_a.exchange([addr0, addr1], 4096)
        return read_data

    def read_memory_dump_data(self):
        with open(r'memory_dump_data.txt', 'r') as fd:
            all_data = [x.strip() for x in fd]
        with open('mem.dat', 'w') as fo:
            try:
                for i in range(0, 2):
                    for j in range(0, 2048):
                        dout = ''
                        for k in range(0, 8):
                            for m in range(0, 4):
                                idx = j * 4 + k * 8192 + m
                                dout = all_data[idx] + dout
                        fo.write(dout + '\n')
                self.textBrowser_normal_log('mem read done!')
            except Exception as e:
                self.textBrowser_error_log("mem read exist err:%s" % e)

    def weight_rd(self):
        try:
            os.remove('ana_weight.xls')
        except:
            pass
        try:
            wb = xlwt.Workbook()
            ws = wb.add_sheet('adc_weight')
            write_content_list = [(0, 0, 'ch_idx'), (0, 1, 'ch0'), (0, 2, 'ch1'), (0, 3, 'ch2'), (0, 4, 'ch3'),
                                  (1, 0, 'mdac0_weight1'), (2, 0, 'mdac1_weight1'), (3, 0, 'mdac2_weight1'),
                                  (4, 0, 'mdac3_weight1'), (5, 0, 'mdac4_weight1'), (6, 0, 'mdac5_weight1'),
                                  (7, 0, 'mdac6_weight1'), (8, 0, 'mdac7_weight1'), (9, 0, 'mdac0_weight2'),
                                  (10, 0, 'mdac1_weight2'), (11, 0, 'mdac2_weight2'), (12, 0, 'mdac3_weight2'),
                                  (13, 0, 'mdac4_weight2'), (14, 0, 'mdac5_weight2'), (15, 0, 'mdac6_weight2'),
                                  (16, 0, 'mdac7_weight2'), (17, 0, 'bkadc0_weight1'), (18, 0, 'bkadc1_weight1'),
                                  (19, 0, 'bkadc2_weight1'), (20, 0, 'bkadc3_weight1'), (21, 0, 'bkadc4_weight1'),
                                  (22, 0, 'bkadc5_weight1'), (23, 0, 'bkadc6_weight1'), (24, 0, 'bkadc7_weight1'),
                                  (25, 0, 'bkadc0_weight2'), (26, 0, 'bkadc1_weight2'), (27, 0, 'bkadc2_weight2'),
                                  (28, 0, 'bkadc3_weight2'), (29, 0, 'bkadc4_weight2'), (30, 0, 'bkadc5_weight2'),
                                  (31, 0, 'bkadc6_weight2'), (32, 0, 'bkadc7_weight2'), (33, 0, 'bkadc0_weight3'),
                                  (34, 0, 'bkadc1_weight3'), (35, 0, 'bkadc2_weight3'), (36, 0, 'bkadc3_weight3'),
                                  (37, 0, 'bkadc4_weight3'), (38, 0, 'bkadc5_weight3'), (39, 0, 'bkadc6_weight3'),
                                  (40, 0, 'bkadc7_weight3'), (41, 0, 'mdac_os0_weight'), (42, 0, 'mdac_os1_weight'),
                                  (43, 0, 'mdac_gec_weight'), (44, 0, 'mdac_dither_weight'), (45, 0, 'gec_coeff'),
                                  (46, 0, 'chopper_coeff'), (47, 0, 'tios_coeff'), (48, 0, 'tigain_coeff'),
                                  (49, 0, 'tiskew_code'), (50, 0, 'opgain_code')]
            for item in write_content_list:
                ws.write(item[0], item[1], item[2])
            for ch_idx in range(0, 4):
                for os_idx in range(0, 2):
                    read_data = self.read_atom(0x800 + 0x1d + ch_idx * 4 + os_idx * 2)
                    read_data1 = self.read_atom(0x800 + 0x1e + ch_idx * 4 + os_idx * 2)
                    weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                    ws.write(41 + os_idx, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x2d + ch_idx * 2)
                read_data1 = self.read_atom(0x800 + 0x2e + ch_idx * 2)
                weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                ws.write(43, 1 + ch_idx, weight)
                for mdac_idx in range(0, 8):
                    read_data = self.read_atom(0x800 + 0x3c + ch_idx * 24 + mdac_idx * 3)
                    read_data1 = self.read_atom(0x800 + 0x3d + ch_idx * 24 + mdac_idx * 3)
                    read_data2 = self.read_atom(0x800 + 0x3e + ch_idx * 24 + mdac_idx * 3)
                    weight = int(hexlify(read_data2[0]).decode(),16) * 65536 + int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                    ws.write(1 + mdac_idx, 1 + ch_idx, weight)
                    read_data = self.read_atom(0x800 + 0x9c + ch_idx * 16 + mdac_idx * 2)
                    read_data1 = self.read_atom(0x800 + 0x9d + ch_idx * 16 + mdac_idx * 2)
                    weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                    ws.write(9 + mdac_idx, 1 + ch_idx, weight)
                    read_data = self.read_atom(0x800 + 0xdc + ch_idx * 16 + mdac_idx * 2)
                    read_data1 = self.read_atom(0x800 + 0xdd + ch_idx * 16 + mdac_idx * 2)
                    weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                    ws.write(17 + mdac_idx, 1 + ch_idx, weight)
                    read_data = self.read_atom(0x800 + 0x11c + ch_idx * 16 + mdac_idx * 2)
                    read_data1 = self.read_atom(0x800 + 0x11d + ch_idx * 16 + mdac_idx * 2)
                    weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                    ws.write(25 + mdac_idx, 1 + ch_idx, weight)
                    read_data = self.read_atom(0x800 + 0x15c + ch_idx * 16 + mdac_idx * 2)
                    read_data1 = self.read_atom(0x800 + 0x15d + ch_idx * 16 + mdac_idx * 2)
                    weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                    ws.write(33 + mdac_idx, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x19c + ch_idx * 3)
                read_data1 = self.read_atom(0x800 + 0x19d + ch_idx * 3)
                read_data2 = self.read_atom(0x800 + 0x19e + ch_idx * 3)
                weight = int(hexlify(read_data2[0]).decode(),16) * 65536 + int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                ws.write(44, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x355 + ch_idx * 2)
                read_data1 = self.read_atom(0x800 + 0x356 + ch_idx * 2)
                weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                ws.write(45, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x383 + ch_idx * 2)
                read_data1 = self.read_atom(0x800 + 0x384 + ch_idx * 2)
                weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                ws.write(46, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x3a6 + ch_idx * 2)
                read_data1 = self.read_atom(0x800 + 0x3a7 + ch_idx * 2)
                weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                ws.write(47, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x3c8 + ch_idx * 2)
                read_data1 = self.read_atom(0x800 + 0x3c9 + ch_idx * 2)
                weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                ws.write(48, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x3fd + ch_idx * 2)
                read_data1 = self.read_atom(0x800 + 0x3fe + ch_idx * 2)
                weight = int(hexlify(read_data1[0]).decode(), 16) * 256 + int(hexlify(read_data[0]).decode(), 16)
                ws.write(49, 1 + ch_idx, weight)
                read_data = self.read_atom(0x800 + 0x38 + ch_idx)
                weight = int(hexlify(read_data[0]).decode(), 16)
                ws.write(50, 1 + ch_idx, weight)
            wb.save('ana_weight.xls')
            self.textBrowser_normal_log('weight save done!')
        except Exception as e:
            self.textBrowser_error_log('%s + please close excel first' % e)
        # self.textBrowser.insertPlainText(time.ctime() + ': weight read done!\n')

    def _async_raise(self, tid, exctype):
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError('invalid thread id')
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop_thread(self, thread):
        self._async_raise(thread.ident, SystemExit)

    def clk_opt_cfg(self):
        dialog = ClkOptDialog()
        dialog.Signal_parp.connect(self.deal_emit_clkopt)
        dialog.show()
        dialog.exec_()
        if len(self.clk_opt_cfg_param) == 3:
            if self.clk_opt_cfg_param[0] != '' and self.clk_opt_cfg_param[1] != '':
                try:
                    fs = float(self.clk_opt_cfg_param[0])
                    fin = float(self.clk_opt_cfg_param[1])
                    direct2 = (np.sign(np.sin(2 * np.pi * fin / fs)) * -1 + 1) / 2
                    direct1 = (np.sign(np.sin(2 * np.pi * 2 * fin / fs)) * -1 + 1) / 2
                    direct0 = (np.sign(np.sin(2 * np.pi * fin / fs)) * -1 + 1) / 2
                    direct = int(direct2 * 4 + direct1 * 2 + direct0)
                    self.fs_display.setText(self.clk_opt_cfg_param[0])
                    self.fin_display.setText(self.clk_opt_cfg_param[1])
                    self.fin_display_2.setText(self.clk_opt_cfg_param[2])
                    self.textBrowser_normal_log(
                        'set adc sampling rate:%d MHz,Freq:%d MHz,Lane rate:%s GHz' % (
                            fs, fin, self.clk_opt_cfg_param[2]))
                    self.write_atom(0xbf9, direct)
                except Exception as e:
                    QMessageBox.information(self, "warning", "%s" % e)
        else:
            return

    def deal_emit_clkopt(self, opt_cfg):
        self.clk_opt_cfg_param = opt_cfg

    def ddc_config(self):
        self.fs_display.setText('3000')
        self.fin_display_2.setText('15.0')
        chip_mode = ['Full bandwidth', 'One DDC mode', 'Two DDC mode', 'Four DDC mode']
        self.chip_mode_config.addItems(chip_mode)
        real_mode = ['Real', 'Complex']
        self.real_mode_config.addItems(real_mode)
        self.mix_mode_config.addItems(['Real', 'Complex'])
        self.freq_mode_config.addItems(['Variable IF', '0 Hz IF', 'fs/4 Hz IF', 'Test'])
        self.gain_mode_config.addItems(['0db', '6db'])
        self.ddc0_config.addItem('Decimation=1')
        self.ddc1_config.addItem('Unused')
        self.ddc2_config.addItem('Unused')
        self.ddc3_config.addItem('Unused')
        self.chip_mode_config.activated.connect(self.ddc_mode_cfg_active)
        self.real_mode_config.activated.connect(self.ddc_mode_cfg_active)
        self.textBrowser_normal_log('ddc_config configure is finish')

    def ddc_mode_cfg_active(self):
        self.ddc0_config.clear()
        self.ddc1_config.clear()
        self.ddc2_config.clear()
        self.ddc3_config.clear()
        self.m_reg_cfg.clear()
        ddc_real_config = ['Decimation=1', 'Decimation=2', 'Decimation=3', 'Decimation=4', 'Decimation=5',
                           'Decimation=6',
                           'Decimation=8', 'Decimation=10', 'Decimation=12', 'Decimation=20', 'Decimation=24']
        ddc_complex_config = ['Decimation=2', 'Decimation=3', 'Decimation=4', 'Decimation=6', 'Decimation=8',
                              'Decimation=10',
                              'Decimation=12', 'Decimation=15', 'Decimation=16', 'Decimation=20''Decimation=24',
                              'Decimation=30',
                              'Decimation=40', 'Decimation=48']
        cur_mode = self.chip_mode_config.currentText()
        real_mode = self.real_mode_config.currentText()
        if cur_mode == 'Full bandwidth':
            self.ddc0_config.addItem('Decimation=1')
            self.ddc1_config.addItem('Unused')
            self.ddc2_config.addItem('Unused')
            self.ddc3_config.addItem('Unused')
            self.m_reg_cfg.addItems(['1', '2'])
        elif cur_mode == 'One DDC mode':
            if real_mode == 'Real':
                self.ddc0_config.addItems(ddc_real_config)
                self.m_reg_cfg.addItem('1')
            else:
                self.ddc0_config.addItems(ddc_complex_config)
                self.m_reg_cfg.addItem('2')
            self.ddc1_config.addItem('Unused')
            self.ddc2_config.addItem('Unused')
            self.ddc3_config.addItem('Unused')
        elif cur_mode == 'Two DDC mode':
            if real_mode == 'Real':
                self.ddc0_config.addItems(ddc_real_config)
                self.ddc1_config.addItems(ddc_real_config)
                self.m_reg_cfg.addItem('2')
            else:
                self.ddc0_config.addItems(ddc_complex_config)
                self.ddc1_config.addItems(ddc_complex_config)
                self.m_reg_cfg.addItem('4')
            self.ddc2_config.addItem('Unused')
            self.ddc3_config.addItem('Unused')
        elif cur_mode == 'Four DDC mode':
            if real_mode == 'Real':
                self.ddc0_config.addItems(ddc_real_config)
                self.ddc1_config.addItems(ddc_real_config)
                self.ddc2_config.addItems(ddc_real_config)
                self.ddc3_config.addItems(ddc_real_config)
                self.m_reg_cfg.addItem('4')
            else:
                self.ddc0_config.addItems(ddc_complex_config)
                self.ddc1_config.addItems(ddc_complex_config)
                self.ddc2_config.addItems(ddc_complex_config)
                self.ddc3_config.addItems(ddc_complex_config)
                self.m_reg_cfg.addItem('8')

    def hcf(self, a, b):
        while (b != 0):
            temp = a % b
            a = b
            b = temp
        return a

    def nco_update(self):
        try:
            nco0_freq = self.nco0_line_edit.text()
            nco1_freq = self.nco1_line_edit.text()
            nco2_freq = self.nco2_line_edit.text()
            nco3_freq = self.nco3_line_edit.text()
            fs = self.fs_display.text()
            ddc_num = self.chip_mode_config.currentIndex()
            real_mode = 1 - self.real_mode_config.currentIndex()
            freq_mode = self.freq_mode_config.currentIndex()
            gain_mode = self.gain_mode_config.currentIndex()
            mix_mode = self.mix_mode_config.currentIndex()
            ddc_dcm_str = self.ddc0_config.currentText()
            ddc_dcm = int(re.match('Decimation=(\d+)', ddc_dcm_str).group(1))
            self.write_atom(0x200, ddc_num)
            self.textBrowser_normal_log('start nco_update')
            self.gen_nco_cfg(nco0_freq, fs, 0)
            self.gen_nco_cfg(nco1_freq, fs, 1)
            self.gen_nco_cfg(nco2_freq, fs, 2)
            self.gen_nco_cfg(nco3_freq, fs, 3)
            transfer_text = ''
            if ddc_dcm == 1:
                self.textBrowser_normal_log('ddc_dcm is 1')
                self.write_atom(0x201, 0x0)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 15 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(15 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 2:
                self.textBrowser_normal_log('ddc_dcm is 2')
                self.write_atom(0x201, 0x1)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 3, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 3)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 3:
                self.textBrowser_normal_log('ddc_dcm is 3')
                self.write_atom(0x201, 0x8)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 7 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(7 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 4:
                self.textBrowser_normal_log('ddc_dcm is 4')
                self.write_atom(0x201, 0x2)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 0, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 0)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 5:
                self.textBrowser_normal_log('ddc_dcm is 5')
                self.write_atom(0x201, 0x5)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 10 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(10 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 6:
                self.textBrowser_normal_log('ddc_dcm is 6')
                self.write_atom(0x201, 0x9)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 4, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 4)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 8:
                self.textBrowser_normal_log('ddc_dcm is 8')
                self.write_atom(0x201, 0x3)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 1, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 1)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 10:
                self.textBrowser_normal_log('ddc_dcm is 10')
                self.write_atom(0x201, 0x6)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 2 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(2 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 12:
                self.textBrowser_normal_log('ddc_dcm is 12')
                self.write_atom(0x201, 0xa)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 5, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 5)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 15:
                self.textBrowser_normal_log('ddc_dcm is 15')
                self.write_atom(0x201, 0x7)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 8 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(8 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 16:
                self.textBrowser_normal_log('ddc_dcm is 16')
                self.write_atom(0x201, 0x4)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 2, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 2)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 20:
                self.textBrowser_normal_log('ddc_dcm is 20')
                self.write_atom(0x201, 0xd)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 3 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(3 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 24:
                self.textBrowser_normal_log('ddc_dcm is 24')
                self.write_atom(0x201, 0xb)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 6, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 6)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 30:
                self.textBrowser_normal_log('ddc_dcm is 30')
                self.write_atom(0x201, 0xe)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 9 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(9 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 40:
                self.textBrowser_normal_log('ddc_dcm is 40')
                self.write_atom(0x201, 0xf)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 4 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(4 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            elif ddc_dcm == 48:
                self.textBrowser_normal_log('ddc_dcm is 48')
                self.write_atom(0x201, 0xc)
                for i in range(4):
                    self.write_atom(0x310 + 32 * i,
                                    mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7, True)
                    addr_str_1 = '{:0>4x}'.format(0x310 + 32 * i)
                    data_str_1 = '{:0>4x}'.format(mix_mode * 128 + gain_mode * 64 + freq_mode * 16 + real_mode * 8 + 7)
                    transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                    self.write_atom(0x311 + 32 * i, 0 * 16, True)
                    addr_str_2 = '{:0>4x}'.format(0x311 + 32 * i)
                    data_str_2 = '{:0>4x}'.format(0 * 16)
                    transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.textBrowser_normal_log(transfer_text)
            time.sleep(1)
            self.textBrowser_normal_log('sleep 1s')
            self.write_atom(0x300, 0x10)
            time.sleep(1)
            self.textBrowser_normal_log('sleep 1s')
            self.write_atom(0x300, 0x0)
            self.textBrowser_normal_log('end nco update')
        except Exception as e:
            self.textBrowser_error_log('nco update err: %s' % e)

    def gen_nco_cfg(self, fin, fs, nco_no):
        if fin != '' and fs != '':
            fin = float(fin)
            fs = float(fs)
            tmp_div = self.hcf(fin, fs)
            fin_r = int(fin / tmp_div)
            fs_r = int(fs / tmp_div)
            ftw = '{:0>12x}'.format(int(2 ** 48 * fin_r / fs_r))
            maw = '{:0>12x}'.format(2 ** 48 * fin_r % fs_r)
            mbw = '{:0>12x}'.format(fs_r)
            transfer_text = ''
            for i in range(6):
                self.write_atom(0x316 + 32 * nco_no + i, int(ftw[10 - 2 * i:12 - 2 * i], 16), True)
                addr_str_1 = '{:0>4x}'.format(0x316 + 32 * nco_no + i)
                data_str_1 = '{:0>4x}'.format(int(ftw[10 - 2 * i:12 - 2 * i], 16))
                transfer_text += 'write addr: ' + addr_str_1 + " data: " + data_str_1 + "\n"
                self.write_atom(0x390 + 16 * nco_no + i, int(maw[10 - 2 * i:12 - 2 * i], 16), True)
                addr_str_2 = '{:0>4x}'.format(0x390 + 16 * nco_no + i)
                data_str_2 = '{:0>4x}'.format(int(maw[10 - 2 * i:12 - 2 * i], 16))
                transfer_text += 'write addr: ' + addr_str_2 + " data: " + data_str_2 + "\n"
                self.write_atom(0x398 + 16 * nco_no + i, int(mbw[10 - 2 * i:12 - 2 * i], 16), True)
                addr_str_3 = '{:0>4x}'.format(0x398 + 16 * nco_no + i)
                data_str_3 = '{:0>4x}'.format(int(mbw[10 - 2 * i:12 - 2 * i], 16))
                transfer_text += 'write addr: ' + addr_str_3 + " data: " + data_str_3 + "\n"
            self.textBrowser_normal_log(transfer_text)

    def j204b_config(self):
        self.ntotal_reg_cfg.addItems(['16', '12', '8'])
        self.m_reg_cfg.addItems(['1', '2', '4', '8'])
        self.l_reg_cfg.addItems(['1', '2', '4', '8'])
        self.f_reg_cfg.addItems(['1', '2', '3', '4', '6', '8', '16'])
        self.k_reg_cfg.addItem('32')
        self.n_reg_cfg.addItems(['16', '15', '14', '13', '12', '11', '10', '9', '8'])
        self.s_reg_cfg.addItem('1')
        self.ntotal_reg_cfg.activated.connect(self.j204b_mode_cfg_active)
        self.m_reg_cfg.activated.connect(self.j204b_mode_cfg_active)
        self.l_reg_cfg.activated.connect(self.j204b_mode_cfg_active2)
        self.f_reg_cfg.activated.connect(self.j204b_mode_cfg_active2)
        self.ddc0_config.activated.connect(self.calc_lane_rate)

    def j204b_mode_cfg_active(self):
        self.s_reg_cfg.clear()
        self.n_reg_cfg.clear()
        m_reg = self.m_reg_cfg.currentText()
        ntotal_reg = self.ntotal_reg_cfg.currentText()
        f_reg = self.f_reg_cfg.currentText()
        l_reg = self.l_reg_cfg.currentText()
        s_reg = 8 * int(f_reg) * int(l_reg) / int(m_reg) / int(ntotal_reg)
        self.s_reg_cfg.addItem(str(int(s_reg)))
        self.f_reg_cfg.clear()
        if ntotal_reg == '16':
            self.n_reg_cfg.addItems(['16', '15', '14', '13', '12', '11', '10', '9', '8'])
            if m_reg == '1':
                self.f_reg_cfg.addItems(['1', '2', '4'])
            elif m_reg == '8':
                self.f_reg_cfg.addItems(['2', '4', '8', '16'])
            else:
                self.f_reg_cfg.addItems(['1', '2', '4', '8'])
        elif ntotal_reg == '12':
            self.l_reg_cfg.clear()
            self.n_reg_cfg.addItems(['12', '11', '10', '9', '8'])
            if m_reg == '1':
                self.f_reg_cfg.addItems(['1', '3', '6'])
                self.l_reg_cfg.addItems(['1', '2', '3'])
            elif m_reg == '2':
                self.f_reg_cfg.addItems(['1', '3'])
                self.l_reg_cfg.addItems(['1', '2', '3', '4'])
            elif m_reg == '4':
                self.f_reg_cfg.addItems(['2', '3', '6'])
                self.l_reg_cfg.addItems(['1', '2', '3', '4'])
            else:
                self.f_reg_cfg.addItems(['3', '6'])
                self.l_reg_cfg.addItems(['2', '4'])
        else:
            self.n_reg_cfg.addItem('8')
            self.l_reg_cfg.clear()
            self.l_reg_cfg.addItems(['1', '2', '4'])
            self.f_reg_cfg.addItems(['1', '2', '4'])

    def j204b_mode_cfg_active2(self):
        self.s_reg_cfg.clear()
        m_reg = self.m_reg_cfg.currentText()
        ntotal_reg = self.ntotal_reg_cfg.currentText()
        f_reg = self.f_reg_cfg.currentText()
        l_reg = self.l_reg_cfg.currentText()
        s_reg = 8 * int(f_reg) * int(l_reg) / int(m_reg) / int(ntotal_reg)
        self.s_reg_cfg.addItem(str(int(s_reg)))
        self.calc_lane_rate()

    def calc_lane_rate(self):
        m_reg = self.m_reg_cfg.currentText()
        ntotal_reg = self.ntotal_reg_cfg.currentText()
        l_reg = self.l_reg_cfg.currentText()
        fadc = self.fs_display.text()
        ddc_dcm_str = self.ddc0_config.currentText()
        ddc_dcm = float(re.match('Decimation=(\d+)', ddc_dcm_str).group(1))
        if fadc == '':
            lane_rate = 0
        else:
            fadc = float(fadc) / 1000
            lane_rate = float(m_reg) * float(ntotal_reg) * (10 / 8) * fadc / ddc_dcm / float(l_reg)
        self.fin_display_2.setText(str(lane_rate))

    def j204b_update(self):
        self.textBrowser_normal_log('start 204B update')
        try:
            m_reg = self.m_reg_cfg.currentText()
            ntotal_reg = self.ntotal_reg_cfg.currentText()
            f_reg = self.f_reg_cfg.currentText()
            l_reg = self.l_reg_cfg.currentText()
            s_reg = self.s_reg_cfg.currentText()
            n_reg = self.n_reg_cfg.currentText()
            k_reg = self.k_reg_cfg.currentText()
            fs = self.fs_display.text()
            lane_rate = self.fin_display_2.text()  ##str
            self.write_atom(0x571, 0x4)
            self.write_atom(0x5f9, 0x0)
            if fs != '' and lane_rate != '':
                ddc_freq = float(fs) / 4
                link_freq = float(lane_rate) * 1000 / 40
                clk_div = int(ddc_freq / link_freq)
                self.write_atom(0xf0d, clk_div)
            else:
                self.write_atom(0xf0d, 0x2)
            self.write_atom(0x5f9, 0x0)
            self.write_atom(0x58b, 128 + int(l_reg) - 1)
            self.write_atom(0x58e, int(m_reg) - 1)
            self.write_atom(0x58c, int(f_reg) - 1)
            self.write_atom(0x591, int(s_reg) - 1)
            self.write_atom(0x58f, int(n_reg) - 1)
            self.write_atom(0x590, 32 + int(ntotal_reg) - 1)
            self.write_atom(0x58d, int(k_reg) - 1)
            self.write_atom(0x5e4, int(k_reg) * int(f_reg))
            self.write_atom(0x5b2, 0x45)
            self.write_atom(0x5b3, 0x76)
            self.write_atom(0x5b5, 0x03)
            self.write_atom(0x5b6, 0x12)
            self.write_atom(0x571, 0x5)
        except Exception as e:
            self.textBrowser_error_log("204B update err:%s" % e)

    def sds_config(self):
        self.refclk_div.setText('64')
        self.fbc_div.setText('160')
        self.comboBox.addItems(['0db', '3.5db', '6db', '9db'])

    def sds_update(self):
        lane_rate = self.fin_display_2.text()  ##str
        ffe_sel = self.comboBox.currentIndex()  ##int
        refclk_div = int(int(self.refclk_div.text()) / 2)
        fbc_div = int(self.fbc_div.text())
        self.write_atom(0x107d, refclk_div)
        self.write_atom(0x1148, fbc_div)
        if lane_rate == '':
            self.textBrowser_normal_log('lane_rate is null,sds_update')
            list_addr_data = [(0x113a, 0x90), (0x113b, 0xfd), (0x113c, 0x07), (0x113d, 0x05), (0x113e, 0x90),
                              (0x113f, 0x81), (0x1140, 0x00), (0x1141, 0x0f), (0x1142, 0x02), (0x1143, 0x40),
                              (0x1144, 0xf0), (0x1145, 0x57), (0x1146, 0x2f), (0x1149, 0x00), (0x114a, 0x50),
                              (0x1150, 0x49), (0x1151, 0x16), (0x1088, 0x50)]
            self.write_thread(list_addr_data)
        else:
            lane_rate = float(lane_rate)
            self.textBrowser_normal_log('lane_rate is %d,sds_update' % lane_rate)
            if 4 <= lane_rate <= 6.5:
                list_add_data = [(0x113a, 0x10), (0x113b, 0xfd), (0x113c, 0x0e), (0x113d, 0x7d), (0x113e, 0x90),
                                 (0x113f, 0x84), (0x1140, 0x00), (0x1141, 0x00), (0x1142, 0x02), (0x1143, 0x55),
                                 (0x1144, 0xf0), (0x1145, 0x07), (0x1146, 0x2f), (0x1149, 0x40), (0x114a, 0x5a),
                                 (0x1150, 0x49), (0x1151, 0x12), (0x1088, 0x50)]
                self.write_thread(list_add_data)
            elif 6.5 < lane_rate <= 8:
                lis_addr_data = [(0x113a, 0x90), (0x113b, 0xfd), (0x113c, 0x07), (0x113d, 0x00), (0x113e, 0x90),
                                 (0x113f, 0x81), (0x1140, 0x00), (0x1141, 0x0f), (0x1142, 0x02), (0x1143, 0x55),
                                 (0x1144, 0xf0), (0x1145, 0x57), (0x1146, 0x2f), (0x1149, 0x40), (0x114a, 0x5a),
                                 (0x1150, 0x49), (0x1151, 0x16), (0x1088, 0x50)]
                self.write_thread(lis_addr_data)
            elif 8 < lane_rate <= 13.5:
                list_addr_data = [(0x113a, 0x10), (0x113b, 0xfd), (0x113c, 0x0e), (0x113d, 0x7d), (0x113e, 0x90),
                                  (0x113f, 0x84), (0x1140, 0x00), (0x1141, 0x00), (0x1142, 0x02), (0x1143, 0x55),
                                  (0x1144, 0xf0), (0x1145, 0x07), (0x1146, 0x2f), (0x1149, 0x40), (0x114a, 0x5a),
                                  (0x1150, 0x49), (0x1151, 0x12), (0x1088, 0x50)]
                self.write_thread(list_addr_data)
            elif 13.5 < lane_rate <= 16:
                list_addr_data = [(0x113a, 0x90), (0x113b, 0xfd), (0x113c, 0x07), (0x113d, 0x00), (0x113e, 0x90),
                                  (0x113f, 0x81), (0x1140, 0x00), (0x1141, 0x0f), (0x1142, 0x02), (0x1143, 0x55),
                                  (0x1144, 0xf0), (0x1145, 0x57), (0x1146, 0x2f), (0x1149, 0x40), (0x114a, 0x5a),
                                  (0x1150, 0x49), (0x1151, 0x16), (0x1088, 0x50)]
                self.write_thread(list_addr_data)
        transfer_text = ''
        for i in range(8):
            self.write_atom(0x1092 + i * 10, 0x84, True)
            addr_str = '{:0>4x}'.format(0x1092 + i * 10)
            data_str = '{:0>4x}'.format(0x84)
            transfer_text += 'write addr: ' + addr_str + " data: " + data_str + "\n"
        self.textBrowser_normal_log(transfer_text)
        if lane_rate == '':
            pass
        else:
            lane_rate = float(lane_rate)
            if 8 <= lane_rate <= 16:  ##8-16G
                for i in range(8):
                    if ffe_sel == 0:
                        self.write_atom(0x1091 + i * 10, 0x60)
                    else:
                        self.write_atom(0x1091 + i * 10, 0x63)
            elif 4 <= lane_rate < 8:  ##4-8G
                for i in range(8):
                    if ffe_sel == 0:
                        self.write_atom(0x1091 + i * 10, 0x70)
                    else:
                        self.write_atom(0x1091 + i * 10, 0x73)
        if ffe_sel == 0:
            for i in range(8):
                self.write_atom(0x1090 + i * 10, 0x3c)
                self.write_atom(0x108f + i * 10, 0xf4)
                self.write_atom(0x108e + i * 10, 0x0)
        elif ffe_sel == 1:
            for i in range(8):
                self.write_atom(0x1090 + i * 10, 0x38)
                self.write_atom(0x108f + i * 10, 0xd4)
                self.write_atom(0x108e + i * 10, 0x0)
        elif ffe_sel == 2:
            for i in range(8):
                self.write_atom(0x1090 + i * 10, 0x3c)
                self.write_atom(0x108f + i * 10, 0xc4)
                self.write_atom(0x108e + i * 10, 0x0)
        elif ffe_sel == 3:
            for i in range(8):
                self.write_atom(0x1090 + i * 10, 0x3e)
                self.write_atom(0x108f + i * 10, 0xb4)
                self.write_atom(0x108e + i * 10, 0x0)
        self.write_atom(0x1089, 0xf0)
        time.sleep(0.5)
        self.write_atom(0x1089, 0xf1)
        for i in range(8):
            self.write_atom(0x10e3 + 12 * i, 0x02)
        time.sleep(0.5)
        for i in range(8):
            self.write_atom(0x10e3 + 12 * i, 0x00)
        time.sleep(0.5)
        self.write_atom(0x1087, 0x04)
        time.sleep(0.5)
        self.write_atom(0x1087, 0x0c)

    def sds_test_prbs7(self):
        for i in range(8):
            self.write_atom(0x108d + i * 10, 0x80)
        time.sleep(0.5)
        for i in range(8):
            self.write_atom(0x108d + i * 10, 0xa0)

    def sds_test_clk0101(self):
        for i in range(8):
            self.write_atom(0x108d + i * 10, 0x91)

    # def spi_config(self):
    #     self.lineEdit_2.setText('8')
    #     self.lineEdit.setText('1.125')
    #     # Scan device
    #     nRet = ControlSPI.VSI_ScanDevice(1)
    #     if nRet <= 0:
    #         self.label_6.setPixmap(QtGui.QPixmap(":/status/OFF.png"))
    #     else:
    #         self.label_6.setPixmap(QtGui.QPixmap(":/status/on.png"))
    #     # Open device
    #     nRet = ControlSPI.VSI_OpenDevice(ControlSPI.VSI_USBSPI, 0, 0)
    #     if nRet != ControlSPI.ERR_SUCCESS:
    #         self.label_6.setPixmap(QtGui.QPixmap(":/status/OFF.png"))
    #     else:
    #         self.label_6.setPixmap(QtGui.QPixmap(":/status/on.png"))
    # Initialize device
    # SPI_Init = ControlSPI.VSI_INIT_CONFIG()
    # SPI_Init.ClockSpeed = 1125000
    # SPI_Init.ControlMode = 3
    # SPI_Init.CPHA = 0
    # SPI_Init.CPOL = 0
    # SPI_Init.LSBFirst = 0
    # SPI_Init.MasterMode = 1
    # SPI_Init.SelPolarity = 0
    # SPI_Init.TranBits = 8
    # nRet = ControlSPI.VSI_InitSPI(ControlSPI.VSI_USBSPI, 0, byref(SPI_Init))
    # if nRet != ControlSPI.ERR_SUCCESS:
    #     self.label_6.setPixmap(QtGui.QPixmap(":/status/OFF.png"))
    # else:
    #     self.label_6.setPixmap(QtGui.QPixmap(":/status/on.png"))

    # def spi_update(self):
    #     # Scan device
    #     # Set channelA
    #     nRet = ControlSPI.VSI_ScanDevice(1)
    #     if nRet <= 0:
    #         self.textBrowser_normal_log('No device connect!')
    #         print("No device connect!")
    #     else:
    #         self.textBrowser_normal_log("Connected device number is:" + repr(nRet))
    #         print("Connected device number is:" + repr(nRet))
    #     # Open device
    #     nRet = ControlSPI.VSI_OpenDevice(ControlSPI.VSI_USBSPI, 0, 0)
    #     if nRet != ControlSPI.ERR_SUCCESS:
    #         self.textBrowser_normal_log("Open device error!")
    #         print("Open device error!")
    #     else:
    #         self.textBrowser_normal_log("Open device success!")
    #         print("Open device success!")
    #     # Initialize device
    #     SPI_Init = ControlSPI.VSI_INIT_CONFIG()
    #     if self.lineEdit.text() == '':
    #         SPI_Init.ClockSpeed = 1125000
    #     else:
    #         SPI_Init.ClockSpeed = int(float(self.lineEdit.text()) * 1000000)
    #     SPI_Init.ControlMode = 3
    #     SPI_Init.CPHA = 0
    #     SPI_Init.CPOL = 0
    #     SPI_Init.LSBFirst = 0
    #     SPI_Init.MasterMode = 1
    #     SPI_Init.SelPolarity = 0
    #     SPI_Init.TranBits = 8
    #     nRet = ControlSPI.VSI_InitSPI(ControlSPI.VSI_USBSPI, 0, byref(SPI_Init))
    #     if nRet != ControlSPI.ERR_SUCCESS:
    #         self.textBrowser_normal_log("Initialization device error!")
    #         print("Initialization device error!")
    #     else:
    #         self.textBrowser_normal_log("Initialization device success!")
    #         print("Initialization device success!")
    #         self.label_6.setPixmap(QtGui.QPixmap(":/status/on.png"))

    def spi_update(self):
        # Set channelA
        if len(self.url_port) != 0:
            dq = spi_attribute
            self.spi_a = self.port[dq.chn].get_port(dq.cs)
            if self.lineEdit.text() == '':
                SPI_Init_ClockSpeed = dq.freq
            else:
                SPI_Init_ClockSpeed = int(float(self.lineEdit.text()) * 1000000)
            self.spi_a.set_frequency(SPI_Init_ClockSpeed)
            self.spi_a.set_mode(dq.mode)
            self.textBrowser_normal_log('spi_update success')
        else:
            self.textBrowser_error_log('spi_update error')

    def write_thread(self, list_addr_data):
        transfer_text = ''
        for item in list_addr_data:
            self.write_atom(item[0], item[1], True)
            addr_str = '{:0>4x}'.format(item[0])
            data_str = '{:0>4x}'.format(item[1])
            transfer_text += 'write addr: ' + addr_str + " data: " + data_str + "\n"
        self.textBrowser_normal_log(transfer_text)

    def clear_log_content(self):
        self.log_textBrowser.clear()

    def get_log_content(self):
        file_name, file_type = QFileDialog.getSaveFileName(self, "文件保存", "./", "text file (*.txt)")
        if file_name.strip(" ") != "":
            with open(file_name, 'w') as fileOpen:
                fileOpen.write(self.log_textBrowser.toPlainText())
