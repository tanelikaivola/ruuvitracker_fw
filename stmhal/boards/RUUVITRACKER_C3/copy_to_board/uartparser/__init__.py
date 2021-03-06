"""UART parser helper, requires uasyncio"""
import pyb
from uasyncio.core import get_event_loop, sleep

class UARTParser():
    recv_bytes = b''
    EOL = b'\r\n'
    line = b'' # Last detected complete line without EOL marker
    sleep_time = 0.01 # When we have no data sleep this long

    _run = False
    _sol = 0 # Start of line
    _str_cbs = {} # map of 3 value tuples (functionname, comparevalue, callback)
    _re_cbs = {} # map of 2 value tuples (compiled_re, callback)
    _raw_cb = None

    def __init__(self, uart):
        self.uart = uart

    def flush(self):
        self.recv_bytes = b''
        self.line = b''
        self._sol = 0

    def flushto(self, pos):
        self.recv_bytes = self.recv_bytes[pos:]
        if pos > self._sol:
            self.line = b''
            self._sol = 0

    def enter_raw(self, cb):
        """Enters "raw mode" where the given callback is called (with reference to the parser as argument) whenever there is new data, all other parsing is suspended, remember to flush the buffers manually too!"""
        self._raw_cb = cb

    def exit_raw(self, flush=True):
        """Exits raw mode, automatically flushes the buffer unless told not to"""
        self.flush()
        self._raw_cb = None

    def parse_buffer(self):
        if self._raw_cb:
            # PONDER: Should we raise an exception ?
            return

        eolpos = self.recv_bytes.find(self.EOL, self._sol)
        while eolpos > -1:
            # End Of Line detected
            self.line = self.recv_bytes[self._sol:eolpos]
            flushnow = True
            for cbid in self._str_cbs:
                cbinfo =  self._str_cbs[cbid]
                if getattr(self.line, cbinfo[0])(cbinfo[1]):
                    if (cbinfo[2](self.line)):
                        flushnow = False

            for cbid in self._re_cbs:
                cbinfo =  self._re_cbs[cbid]
                match = cbinfo[0](self.line)
                if match:
                    if (cbinfo[1](match)):
                        flushnow = False

            if flushnow:
                self.flushto(eolpos+len(self.EOL))
            else:
                # Point the start-of-line to next line
                self._sol = eolpos+len(self.EOL)
            # And loop, just in case we have multiple lines in the buffer...
            eolpos = self.recv_bytes.find(self.EOL, self._sol)

    def add_re_callback(self, cbid, regex, cb, method='search'):
        """Adds a regex callback for checking full lines, takes the regex as string and callback function. Optionally you can specify 'match' instead of 'search' as the method to use for matching.
        The callback will receive the match object. Return True from the callback to prevent flushing the buffer. NOTE: End Of Line is not part of the line, omit that from your regex too"""
        import ure
        # Sanity-check
        if cbid in self._re_cbs:
            raise RuntimeError("Trying to add same callback twice")
        # Compile the regex
        re = ure.compile(regex)
        # And add the the callback list
        self._re_cbs[cbid] = (getattr(re, method), cb)

    def del_re_callback(self, cbid):
        """Removes a regex callback"""
        if cbid in self._re_cbs:
            del(self._re_cbs[cbid])
            return True
        return False

    def add_line_callback(self, cbid, method, checkstr, cb):
        """Adds a callback for checking full lines, the method can be name of any valid bytearray method but 'startswith' and 'endswith' are probably the good choices.
        The check is performed (and callback will receive  the matched line) with End Of Line removed. Return True from the callback to flush the buffer"""
        # Sanity-check
        if cbid in self._str_cbs:
            raise RuntimeError("Trying to add same callback twice")
        # Check that the method is valid
        getattr(self.recv_bytes, method)
        # And add the the callback list
        self._str_cbs[cbid] = (method, checkstr, cb)

    def del_line_callback(self, cbid):
        """Removes a line callback"""
        if cbid in self._str_cbs:
            del(self._str_cbs[cbid])
            return True
        return False

    def start(self):
        self._run = True
        while self._run:
            if not self.uart.any():
                yield from sleep(self.sleep_time)
                continue
            recv = self.uart.read(100)
            if len(recv) == 0:
                # Timed out (it should be impossible though...)
                continue
            self.recv_bytes += recv
            if not self._raw_cb:
                # TODO: We may want to inline the parsing due to cost of method calls
                self.parse_buffer()
            else:
                self._raw_cb(self)

    def stop(self):
        self._run = False

