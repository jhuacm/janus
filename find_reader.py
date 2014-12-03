#!/usr/bin/python3

# We find a hidraw device for this USB VID:PID pair
# and read card swipe data from it.
READER_VID = 0x0acd
READER_PID = 0x0500

import pyudev
import binascii
import os
import sys

class BitArray(object):
    def __init__(self, initial_content=b''):
        self._content = bytearray(initial_content)
        self._ptr = 0

    def __getitem__(self, idx):
        # Get a bit at the given index, returned as a bool.
        # Bits past the right end give False; bits past the left end give IndexError.
        byte, bit = divmod(idx, 8)
        if byte >= len(self._content):
            return False
        return bool(self._content[byte] & (0x80 >> bit))

    def next_bit(self):
        self._ptr += 1
        return self[self._ptr - 1]

    def past_data(self):
        return self._ptr >= 8 * len(self._content)

    def get_reversed(self):
        newbits = []
        oldptr = self._ptr
        self._ptr = 0
        while not self.past_data():
            byte = 0
            for i in range(8):
                byte = (byte >> 1) | (int(self.next_bit()) << 7)
            newbits.insert(0, byte)
        self._ptr = oldptr
        return BitArray(newbits)


def parity(n):
    parity = 0
    while n != 0:
        parity ^= n & 1
        n >>= 1
    return parity


def decode_from_bitarray(bits, base, charsize, start, end):
    # This masks to the lowest charsize bits.
    charmask = (1 << charsize) - 1
    # This masks off the parity bit too.
    datamask = charmask >> 1

    # First compute the bit pattern for the start sentinel.
    startbits = start - base
    assert startbits & datamask == startbits
    if parity(startbits) == 0:
        startbits |= 1 << (charsize - 1)

    # Search for it.
    bitbuf = 0
    while bitbuf != startbits:
        if bits.past_data():
            return None
        bitbuf = (bitbuf >> 1) | (int(bits.next_bit()) << (charsize - 1))

    # Read out characters until we reach the end sentinel.
    contents = chr(start)
    checksum = bitbuf
    while True:
        # Don't need to check bits.past_data() - we'll get all zeros, which
        # has invalid parity.
        for i in range(charsize):
            bitbuf = (bitbuf >> 1) | (int(bits.next_bit()) << (charsize - 1))
        if parity(bitbuf) != 1:
            # Invalid parity.
            return None
        nextchar = base + (bitbuf & datamask)
        checksum ^= bitbuf
        contents += chr(nextchar)
        if nextchar == end:
            break

    # Check string-wide checksum (next byte after end sentinel).
    for i in range(charsize):
        bitbuf = (bitbuf >> 1) | (int(bits.next_bit()) << (charsize - 1))
    if parity(bitbuf) != 1:
        # Invalid parity.
        return None
    if checksum & datamask != bitbuf & datamask:
        return None

    # It's good.
    return contents


def decode_raw_hexstring(hexstring):
    if hexstring == b'':
        return None

    # These strings come from the reader in the following format:
    # 1 byte for which track the data is from (0x01 to 0x03)
    # An even number of bytes that are the raw bits in capitalized hex
    # 1 byte terminator (0x0d)
    track = hexstring[0]
    bits = BitArray(binascii.unhexlify(hexstring[1:-1]))
    assert hexstring[-1] == 0x0d

    if track == 2:
        base = 0x30
        charsize = 5
        start = ord(';')
        end = ord('?')
    else:
        base = 0x20
        charsize = 7
        start = ord('%')
        end = ord('?')

    data = decode_from_bitarray(bits, base, charsize, start, end)
    # If it failed to decode, try the other way around.
    if data is None:
        data = decode_from_bitarray(bits.get_reversed(), base, charsize, start, end)
    return data


# Ask udev which USB device each device of the given subsystem came from
# so we can find the one we want.
def find_device_for_usb_vidpid(subsys, vid, pid):
    vidstr = '%04x' % (vid,)
    pidstr = '%04x' % (pid,)
    udev = pyudev.Context()
    for dev in udev.list_devices(subsystem=subsys):
        usbdev = dev.find_parent('usb', 'usb_device')
        # HID devices can be other things than USB...
        if usbdev is None:
            continue
        if usbdev.attributes.asstring('idVendor') == vidstr and usbdev.attributes.asstring('idProduct') == pidstr:
            return dev.device_node
    return None


class IDTechHIDReader(object):
    def __init__(self, devpath):
        self._fd = os.open(devpath, os.O_RDONLY)

    def __del__(self):
        os.close(self._fd)

    def fileno(self):
        return self._fd

    def read_card(self):
        hidblob = os.read(self._fd, 4096)

        FIRST_LENGTH = 3
        FIRST_DATA = 9
        lengths = hidblob[FIRST_LENGTH], hidblob[FIRST_LENGTH+1], hidblob[FIRST_LENGTH+2]
        offsets = FIRST_DATA, FIRST_DATA + lengths[0], FIRST_DATA + lengths[0] + lengths[1]
        rawstrings = [hidblob[offset:offset+length] for offset, length in zip(offsets, lengths)]
        return tuple(map(decode_raw_hexstring, rawstrings))


if __name__ == '__main__':
    devfile = find_device_for_usb_vidpid('hidraw', READER_VID, READER_PID)
    if devfile is None:
        sys.stderr.write('Unable to find the card reader.\n')
        sys.exit(1)
    print('Found card reader: %s' % devfile)
    reader = IDTechHIDReader(devfile)

    while True:
        print(reader.read_card())
