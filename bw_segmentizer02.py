#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Bandwidth segmentizer
# Author: Alexandre HEUCHAMPS
# Copyright: hhh
# GNU Radio version: 3.8.3.1

from distutils.version import StrictVersion

if __name__ == "__main__":
    import ctypes
    import sys
    if sys.platform.startswith("linux"):
        try:
            x11 = ctypes.cdll.LoadLibrary("libX11.so")
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from PyQt5 import Qt
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import gr, blocks
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio.filter import pfb
import limesdr

from gnuradio import qtgui

class bw_segmentizer(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Bandwidth segmentizer")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Bandwidth segmentizer")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme("gnuradio-grc"))
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

        self.settings = Qt.QSettings("GNU Radio", "bw_segmentizer")

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
        # General parameters
        self.samp_rate = samp_rate = 60e6
        self.f_start = f_start = 2.4e9
        self.f_stop = f_stop = 2.485e9
        self.n_channels = n_channels = int(f_stop/samp_rate/2)
        self.f = f = [ f_start + i*(f_stop - f_start)/(n_channels - 1) for i in range(n_channels) ]
        self.pannel = pannel = 0

        # Filter parameters
        self.LPF_gain = LPF_gain = 1.0
        self.cutoff = 0.5 * samp_rate
        self.trans_bw = 0.1 * samp_rate
        self.LPF_taps = LPF_taps = firdes.low_pass(LPF_gain, samp_rate, self.cutoff, self.trans_bw, firdes.WIN_HAMMING, 6.76)

        # Frequency and waterfall sinks parameters
        n_inputs_freq_sink = 2
        n_inputs_waterfall_sink = 2

        # Threshold parameters
        self.thres_l = thres_l = 0.0
        self.thres_h = thres_h = 0.0

        # complex_to_mag² parameters
        self.vec_length = vec_length = 1
        self._vec_length_range = qtgui.Range(1, 20, 1, self.get_vec_length(), 200)
        self._vec_length_win = qtgui.RangeWidget(self._vec_length_range, self.set_vec_length, "vec_length", "counter_slider", int)
        self.top_layout.addWidget(self._vec_length_win)

        ##################################################
        # Blocks
        ##################################################
        # Pannel selection
        self.pannels = Qt.QTabWidget()

        self.pannels_freq_sinks = Qt.QWidget()
        self.pannels_layout_freq_sinks = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.pannels_freq_sinks)
        self.pannels_grid_layout_freq_sinks = Qt.QGridLayout()
        self.pannels_layout_freq_sinks.addLayout(self.pannels_grid_layout_freq_sinks)
        self.pannels.addTab(self.pannels_freq_sinks, "Frequency sink")

        self.pannels_waterfall_sinks = Qt.QWidget()
        self.pannels_layout_waterfall_sinks = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.pannels_waterfall_sinks)
        self.pannels_grid_layout_waterfall_sinks = Qt.QGridLayout()
        self.pannels_layout_waterfall_sinks.addLayout(self.pannels_grid_layout_waterfall_sinks)
        self.pannels.addTab(self.pannels_waterfall_sinks, "Waterfall sink")

        # Create the pannels
        self.top_layout.addWidget(self.pannels)

        # Create the options list
        self._pannel_options = [0, 1]

        # Create the labels list
        self._pannel_labels = ["Frequency sink", "Waterfall sink"]

        # Create the combo box
        self._pannel_tool_bar = Qt.QToolBar(self)
        self._pannel_tool_bar.addWidget(Qt.QLabel("pannel: "))
        self._pannel_combo_box = Qt.QComboBox()
        self._pannel_tool_bar.addWidget(self._pannel_combo_box)

        for _label in self._pannel_labels: self._pannel_combo_box.addItem(_label)

        self._pannel_callback = lambda i: Qt.QMetaObject.invokeMethod(self._pannel_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._pannel_options.index(i)))
        self._pannel_callback(self.pannel)
        self._pannel_combo_box.currentIndexChanged.connect(
            lambda i: self.set_pannel(self._pannel_options[i]))

        # Create the radio buttons
        self.top_layout.addWidget(self._pannel_tool_bar)

        # Graphical window parameters
        labels = ["Before", "After", "", "", "",
            "", "", "", "", ""]
        widths = [2, 2, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        # List of all graphical window display
        self._qtgui_freq_sinks_win = []
        self._qtgui_waterfall_sink_win = []

        # List of all sinks
        all_freq_sinks = []
        all_waterfall_sinks = []

        # List of all stream_to_vec, comp_to_mag², and thresholds
        all_stream_to_vec = []
        all_cmpl_to_mag2 = []
        all_thresholds = []



        for i in range(n_channels):
            # Parametrize the stream_to_vec
            all_stream_to_vec.append(
                blocks.stream_to_vector(
                    gr.sizeof_gr_complex*self.get_vec_length(), self.get_vec_length()
                )
            )

            # Parametrize the complex_to_mag²
            all_cmpl_to_mag2.append( blocks.complex_to_mag_squared(self.get_vec_length()) )

            # Parametrize the thresholds
            all_thresholds.append( blocks.threshold_ff(self.thres_l, self.thres_h, 0) )

            # Parametrize the frequency sink blocks correctly
            all_freq_sinks.append(
                qtgui.freq_sink_f(
                    1024, #size
                    firdes.WIN_BLACKMAN_hARRIS, #wintype
                    self.cutoff, #fc
                    samp_rate, #bw
                    f"Channel {i}", #name
                    n_inputs_freq_sink
                )
            )
            all_freq_sinks[i].set_update_time(0.10)
            all_freq_sinks[i].set_y_axis(-140, 10)
            all_freq_sinks[i].set_y_label("Relative Gain", "dB")
            all_freq_sinks[i].set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
            all_freq_sinks[i].enable_autoscale(False)
            all_freq_sinks[i].enable_grid(False)
            all_freq_sinks[i].set_fft_average(1.0)
            all_freq_sinks[i].enable_axis_labels(True)
            all_freq_sinks[i].enable_control_panel(False)
            all_freq_sinks[i].set_plot_pos_half(not True)

            for j in range(n_inputs_freq_sink):
                if len(labels[j]) == 0:
                    all_freq_sinks[i].set_line_label(j, "Data {0}".format(j))
                else:
                    all_freq_sinks[i].set_line_label(j, labels[j])
                all_freq_sinks[i].set_line_width(j, widths[j])
                all_freq_sinks[i].set_line_color(j, colors[j])
                all_freq_sinks[i].set_line_alpha(j, alphas[j])

            # Parametrize the graphical display for the frequency sinks
            self._qtgui_freq_sinks_win.append(
                sip.wrapinstance(all_freq_sinks[i].pyqwidget(), Qt.QWidget)
            )
            self.top_layout.addWidget(self._qtgui_freq_sinks_win[i])

            self.pannels_grid_layout_freq_sinks.addWidget(self._qtgui_freq_sinks_win[i], i, 0, 1, 1)
            for r in range(0, 1):
                self.pannels_grid_layout_freq_sinks.setRowStretch(r, 1)
            for c in range(0, 1):
                self.pannels_grid_layout_freq_sinks.setColumnStretch(c, 1)





            # Parametrize the waterfall sink blocks correctly (before threshold)
            all_waterfall_sinks.append(
                qtgui.waterfall_sink_f(
                    1024, #size
                    firdes.WIN_BLACKMAN_hARRIS, #wintype
                    0, #fc
                    samp_rate, #bw
                    f"Channel {i} ({labels[0]})", #name
                    1 #number of inputs
                )
            )
            all_waterfall_sinks[2*i].set_update_time(0.10)
            all_waterfall_sinks[2*i].enable_grid(False)
            all_waterfall_sinks[2*i].enable_axis_labels(True)

            for j in range(1):
                if len(labels[j]) == 0:
                    all_waterfall_sinks[2*i].set_line_label(j, "Data {0}".format(j))
                else:
                    all_waterfall_sinks[2*i].set_line_label(j, labels[j])
                all_waterfall_sinks[2*i].set_color_map(j, 0)
                all_waterfall_sinks[2*i].set_line_alpha(j, alphas[j])

            all_waterfall_sinks[2*i].set_intensity_range(-140, 10)
            self._qtgui_waterfall_sink_win.append(
                sip.wrapinstance(
                    all_waterfall_sinks[2*i].pyqwidget(), Qt.QWidget
                )
            )
            self.top_layout.addWidget(self._qtgui_waterfall_sink_win[2*i])

            self.pannels_grid_layout_waterfall_sinks.addWidget(self._qtgui_waterfall_sink_win[2*i], i, 0, 1, 1)
            for r in range(0, 1):
                self.pannels_grid_layout_waterfall_sinks.setRowStretch(r, 1)
            for c in range(0, 1):
                self.pannels_grid_layout_waterfall_sinks.setColumnStretch(c, 1)

            # Parametrize the waterfall sink blocks correctly (after threshold)
            all_waterfall_sinks.append(
                qtgui.waterfall_sink_f(
                    1024, #size
                    firdes.WIN_BLACKMAN_hARRIS, #wintype
                    0, #fc
                    samp_rate, #bw
                    f"Channel {i} ({labels[1]})", #name
                    1 #number of inputs
                )
            )
            all_waterfall_sinks[2*i+1].set_update_time(0.10)
            all_waterfall_sinks[2*i+1].enable_grid(False)
            all_waterfall_sinks[2*i+1].enable_axis_labels(True)

            for j in range(1):
                if len(labels[j]) == 0:
                    all_waterfall_sinks[2*i+1].set_line_label(j, "Data {0}".format(j))
                else:
                    all_waterfall_sinks[2*i+1].set_line_label(j, labels[j])
                all_waterfall_sinks[2*i+1].set_color_map(j, 0)
                all_waterfall_sinks[2*i+1].set_line_alpha(j, alphas[j])

            all_waterfall_sinks[2*i+1].set_intensity_range(-140, 10)
            self._qtgui_waterfall_sink_win.append(
                sip.wrapinstance(
                    all_waterfall_sinks[2*i+1].pyqwidget(), Qt.QWidget
                )
            )
            self.top_layout.addWidget(self._qtgui_waterfall_sink_win[2*i+1])

            self.pannels_grid_layout_waterfall_sinks.addWidget(self._qtgui_waterfall_sink_win[2*i+1], i, 1, 1, 1)
            for r in range(0, i):
                self.pannels_grid_layout_waterfall_sinks.setRowStretch(r, 1)
            for c in range(1, 2):
                self.pannels_grid_layout_waterfall_sinks.setColumnStretch(c, 1)



        self.PFB_channelizer = pfb.channelizer_ccf(
            n_channels,
            LPF_taps,
            1.0, #oversample
            100)
        self.PFB_channelizer.set_channel_map([])
        self.PFB_channelizer.declare_sample_delay(0)



        self.limesdr_source_0 = limesdr.source("", 0, "")
        self.limesdr_source_0.set_sample_rate(samp_rate)
        self.limesdr_source_0.set_center_freq( f[int(len(f)/2)], 0)
        self.limesdr_source_0.set_bandwidth(1.5e6, 0)
        self.limesdr_source_0.set_digital_filter(samp_rate, 0)
        self.limesdr_source_0.set_gain(60, 0)
        self.limesdr_source_0.set_antenna(255, 0)
        self.limesdr_source_0.calibrate(2.5e6, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.limesdr_source_0, 0), (self.PFB_channelizer, 0))
        for i in range(n_channels):
            self.connect((self.PFB_channelizer, i), (all_stream_to_vec[i], 0))
            self.connect((all_stream_to_vec[i], 0), (all_cmpl_to_mag2[i], 0))
            self.connect((all_cmpl_to_mag2[i], 0), (all_freq_sinks[i], 0))
            self.connect((all_cmpl_to_mag2[i], 0), (all_waterfall_sinks[2*i], 0))
            self.connect((all_cmpl_to_mag2[i], 0), (all_thresholds[i], 0))
            self.connect((all_thresholds[i], 0), (all_freq_sinks[i], 1))
            self.connect((all_thresholds[i], 0), (all_waterfall_sinks[2*i+1], 0))





    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "bw_segmentizer")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_LPF_taps(firdes.low_pass(self.LPF_gain, self.samp_rate, 0.5 * self.samp_rate, 0.5 * self.samp_rate, firdes.WIN_HAMMING, 6.76))
        self.limesdr_source_0.set_digital_filter(self.samp_rate, 0)
        self.limesdr_source_0.set_digital_filter(self.samp_rate, 1)
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_x_1.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_x_2.set_frequency_range(0, self.samp_rate)

    def get_n_channels(self):
        return self.n_channels

    def set_n_channels(self, n_channels):
        self.n_channels = n_channels
        self.set_ID([i for i in range(self.n_channels)])
        self.set_f([ self.f_start + i*(self.f_stop - self.f_start)/(self.n_channels - 1) for i in range(self.n_channels) ])
        self.set_f_start_channel([ self.f_start + i * (self.f_stop - self.f_start)/(self.n_channels-1) for i in range(self.n_channels-1) ])
        self.set_f_stop_channel([ self.f_start + (i+1) * (self.f_stop - self.f_start)/(self.n_channels-1) for i in range(self.n_channels-1) ])

    def get_f_stop(self):
        return self.f_stop

    def set_f_stop(self, f_stop):
        self.f_stop = f_stop
        self.set_f([ self.f_start + i*(self.f_stop - self.f_start)/(self.n_channels - 1) for i in range(self.n_channels) ])
        self.set_f_start_channel([ self.f_start + i * (self.f_stop - self.f_start)/(self.n_channels-1) for i in range(self.n_channels-1) ])
        self.set_f_stop_channel([ self.f_start + (i+1) * (self.f_stop - self.f_start)/(self.n_channels-1) for i in range(self.n_channels-1) ])

    def get_f_start(self):
        return self.f_start

    def set_f_start(self, f_start):
        self.f_start = f_start
        self.set_f([ self.f_start + i*(self.f_stop - self.f_start)/(self.n_channels - 1) for i in range(self.n_channels) ])
        self.set_f_start_channel([ self.f_start + i * (self.f_stop - self.f_start)/(self.n_channels-1) for i in range(self.n_channels-1) ])
        self.set_f_stop_channel([ self.f_start + (i+1) * (self.f_stop - self.f_start)/(self.n_channels-1) for i in range(self.n_channels-1) ])

    def get_vec_length(self):
        return self.vec_length

    def set_vec_length(self, vec_length):
        self.vec_length = vec_length

    def get_LPF_gain(self):
        return self.LPF_gain

    def set_LPF_gain(self, LPF_gain):
        self.LPF_gain = LPF_gain
        self.set_LPF_taps(firdes.low_pass(self.LPF_gain, self.samp_rate, 0.5 * self.samp_rate, 0.5 * self.samp_rate, firdes.WIN_HAMMING, 6.76))

    def get_f(self):
        return self.f

    def set_f(self, f):
        self.f = f
        self.limesdr_source_0.set_center_freq(self.f[ int(len(self.f)/2) ], 0)

    def get_LPF_taps(self):
        return self.LPF_taps

    def set_LPF_taps(self, LPF_taps):
        self.LPF_taps = LPF_taps
        self.PFB_channelizer.set_taps(self.LPF_taps)

    def get_ID(self):
        return self.ID

    def set_ID(self, ID):
        self.ID = ID

    def get_pannel(self):
        return self.pannel

    def set_pannel(self, pannel):
        self.pannel = pannel
        self._pannel_callback(self.pannel)





def main(top_block_cls=bw_segmentizer, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string("qtgui", "style", "raster")
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

if __name__ == "__main__":
    main()
