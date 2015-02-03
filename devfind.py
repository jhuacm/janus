import pyudev

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
