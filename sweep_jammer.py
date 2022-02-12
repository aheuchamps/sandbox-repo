#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Test sweep jammer
# Author: Alexandre HEUCHAMPS
# GNU Radio version: 3.8.3.1

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio.qtgui import Range, RangeWidget
import epy_block_0_0

from gnuradio import qtgui

class sweep_jammer(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Test sweep jammer")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Test sweep jammer")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "sweep_jammer")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.n_channels = n_channels = 50
        self.f_stop = f_stop = 10e3
        self.f_start = f_start = 2e3
        self.sweep_rate = sweep_rate = 1
        self.samp_rate = samp_rate = 100e3
        self.f = f = [f_start + i*(f_stop-f_start)/(n_channels-1) for i in range(n_channels)]

        ##################################################
        # Blocks
        ##################################################
        self._sweep_rate_range = Range(1, 1e4, 1, 1, 200)
        self._sweep_rate_win = RangeWidget(self._sweep_rate_range, self.set_sweep_rate, 'sweep_rate', "counter_slider", float)
        self.top_layout.addWidget(self._sweep_rate_win)
        self.qtgui_waterfall_sink_x_1 = qtgui.waterfall_sink_f(
            1024, #size
            firdes.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "", #name
            1 #number of inputs
        )
        self.qtgui_waterfall_sink_x_1.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_1.enable_grid(True)
        self.qtgui_waterfall_sink_x_1.enable_axis_labels(True)


        self.qtgui_waterfall_sink_x_1.set_plot_pos_half(not True)

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_1.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_1.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_1.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_1_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_1.pyqwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_waterfall_sink_x_1_win, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.epy_block_0_0 = epy_block_0_0.blk(n_channels=n_channels, samp_rate=samp_rate, sweep_rate=sweep_rate, f_start=f_start, f_stop=f_stop)
        self.blocks_throttle_1 = blocks.throttle(gr.sizeof_float*1, samp_rate,True)
        self.blocks_message_debug_0 = blocks.message_debug()
        self.analog_sig_source_x_1 = analog.sig_source_f(samp_rate, analog.GR_SIN_WAVE, f_start, 1, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_0_0, 'frequency'), (self.analog_sig_source_x_1, 'cmd'))
        self.msg_connect((self.epy_block_0_0, 'debug'), (self.blocks_message_debug_0, 'print'))
        self.connect((self.analog_sig_source_x_1, 0), (self.blocks_throttle_1, 0))
        self.connect((self.blocks_throttle_1, 0), (self.epy_block_0_0, 0))
        self.connect((self.blocks_throttle_1, 0), (self.qtgui_waterfall_sink_x_1, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "sweep_jammer")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_n_channels(self):
        return self.n_channels

    def set_n_channels(self, n_channels):
        self.n_channels = n_channels
        self.set_f([self.f_start + i*(self.f_stop-self.f_start)/(self.n_channels-1) for i in range(self.n_channels)])
        self.epy_block_0_0.n_channels = self.n_channels

    def get_f_stop(self):
        return self.f_stop

    def set_f_stop(self, f_stop):
        self.f_stop = f_stop
        self.set_f([self.f_start + i*(self.f_stop-self.f_start)/(self.n_channels-1) for i in range(self.n_channels)])
        self.epy_block_0_0.f_stop = self.f_stop

    def get_f_start(self):
        return self.f_start

    def set_f_start(self, f_start):
        self.f_start = f_start
        self.set_f([self.f_start + i*(self.f_stop-self.f_start)/(self.n_channels-1) for i in range(self.n_channels)])
        self.analog_sig_source_x_1.set_frequency(self.f_start)
        self.epy_block_0_0.f_start = self.f_start

    def get_sweep_rate(self):
        return self.sweep_rate

    def set_sweep_rate(self, sweep_rate):
        self.sweep_rate = sweep_rate
        self.epy_block_0_0.sweep_rate = self.sweep_rate

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_1.set_sampling_freq(self.samp_rate)
        self.blocks_throttle_1.set_sample_rate(self.samp_rate)
        self.epy_block_0_0.samp_rate = self.samp_rate
        self.qtgui_waterfall_sink_x_1.set_frequency_range(0, self.samp_rate)

    def get_f(self):
        return self.f

    def set_f(self, f):
        self.f = f





def main(top_block_cls=sweep_jammer, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    def quitting():
        tb.stop()
        tb.wait()

    qapp.aboutToQuit.connect(quitting)
    qapp.exec_()

if __name__ == '__main__':
    main()
