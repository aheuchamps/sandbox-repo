"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt


class blk(gr.sync_block): # other base classes are basic_block, decim_block, interp_block
    """!
    Embedded Python Block
    Function changing periodically the signal source's frequency, from
    f_min to f_max, by step of BW_per_channel [i.e. (f_max-f_min)/(n_channels-1)]

    Input:
    ------
    n_channels: <class int> (default: 3)
        Number of frequencies (called channels)

    samp_rate: <class float> (default: 32e3)
        Number of samples to have 1 second

    sweep_rate: <classs int> (default: 1)
        Number of total bandwidth sweepings per second

    f_start: <class float> (default: 2.4e3)
        First channel

    f_stop: <class float> (default: 2.5e3)
        Last channel
    """

    def __init__(self, n_channels=3, samp_rate=32e3, sweep_rate=1, f_start=2.4e3, f_stop=2.5e3): # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Frequency sweeper', # will show up in GRC
            in_sig=[np.float32],
            out_sig=[]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.n_channels = n_channels
        self.samp_rate = samp_rate
        self.sweep_rate = sweep_rate
        self.f_start = f_start
        self.f_stop = f_stop

        self.BW_tot = self.f_stop - f_start

        self.frequencies = [self.f_start + i*self.BW_tot/(self.n_channels-1) for i in range(self.n_channels)]

        self.counter = 0 # if bigger than given threshold, update the frequency
        self.i = 0 # which frequency to select

        self.t_per_freq = self.samp_rate/self.sweep_rate/self.n_channels

        self.outPortFreq = "frequency"
        self.message_port_register_out(pmt.intern(self.outPortFreq))
        self.outPortDebugMsg = "debug"
        self.message_port_register_out(pmt.intern(self.outPortDebugMsg))



    def work(self, input_items, output_items):
        """!
        Example: change frequency of signal source periodically
        """

        # Create dictionaries to send messages to source and terminal
        dict_debug = pmt.make_dict()
        dict_msg = pmt.make_dict()

        # Some debug messages sent to the terminal
        dict_debug = pmt.dict_add(dict_debug, pmt.intern("t_per_freq"), pmt.from_double(self.t_per_freq))
        dict_debug = pmt.dict_add(dict_debug, pmt.intern("counter"), pmt.from_double(self.counter))
        pmt_msg_debug = pmt.dict_add(dict_debug, pmt.intern(f"freq[{self.i}]"), pmt.from_double(self.frequencies[self.i]))
        self.message_port_pub(pmt.intern(self.outPortDebugMsg), pmt_msg_debug)

        self.counter = self.counter + len(input_items[0])

        if self.counter > self.t_per_freq:
            self.i += 1
            self.counter = 0

        if self.i > len(self.frequencies)-1: self.i = 0

        # Message sent to update the source frequency
        pmt_msg = pmt.dict_add(dict_msg, pmt.intern("freq"), pmt.from_double(self.frequencies[self.i]))
        self.message_port_pub(pmt.intern(self.outPortFreq), pmt_msg)

        return len(input_items[0])
