""" Python implementation of ImageSnap for Mac """

import objc
from AVFoundation import AVCaptureDevice, AVMediaTypeVideo, AVMediaTypeMuxed, AVCaptureStillImageOutput

# from Foundation import NSBundle

# Metadata_bundle = NSBundle.bundleWithIdentifier_("com.apple.AVFoundation")
# objc.loadBundleVariables(Metadata_bundle, globals(), [('AVMediaTypeVideo', '@')])

# AVCaptureDevices.devices deprecated in 10.15
# devices = AVCaptureDevice.devices()
# devices = [*AVCaptureDevice.devicesWithMediaType_(AVMediaTypeVideo), *AVCaptureDevice.devicesWithMediaType_(AVMediaTypeMuxed)]

# print(f"Found {len(devices)} devices")
# avc = AVCaptureDevice.alloc().init()
# print(avc.availableStillImageFormats())
# print(avc.deviceID())
# avc.devicesWithMediaType_AVMediaTypeMuxed_()

class imageSnap():
    def __init__(self):
        pass

    def video_devices(self):
        """ return list of connected video devices """
        self._devices = [*AVCaptureDevice.devicesWithMediaType_(AVMediaTypeVideo), *AVCaptureDevice.devicesWithMediaType_(AVMediaTypeMuxed)]
        return self._devices

    def default_video_device(self):
        device = AVCaptureDevice.defaultDeviceWithMediaType_(AVMediaTypeVideo)
        return device

    def device_named(self, name):
        """ returns device with localizedName == name """
        """ returns None if not found """
        devices = self.video_devices()
        for dev in devices:
            if dev.localizedName() == name:
                return dev
        return None

    def save_single_snapshot(self, device=None, path=None, warmup=0, timelapse=0):
        if not device:
            device = self.default_device()
        if not filename:
            filename = "imagesnap.jpg"

        #Use AVCapturePhotoOutput in 10.15+
        capture = AVCaptureStillImageOutput.alloc().init()
        

        

snap = imageSnap()
for dev in snap.video_devices():
    print(f"id: {dev.deviceID()}")
    print(f"id: {dev.availableStillImageFormats()}")
    print(f"isInUse: {dev.isInUseByAnotherApplication()}")
    print(f"mfg: {dev.manufacturer()}")
    print(f"name: {dev.localizedName()}")


default = snap.default_video_device()
print(f"{default.localizedName()}")

device = snap.device_named("FaceTime HD Camera")
print(f"device: {device.localizedName()}")
