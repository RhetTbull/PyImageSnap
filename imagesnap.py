""" Python implementation of Robert Harder's imagesnap for Mac """
""" For original objective C version, see https://github.com/rharder/imagesnap """

import sys
import time
from datetime import datetime

import libdispatch
import objc
from AVFoundation import (AVCaptureDevice, AVCaptureDeviceInput,
                          AVCaptureSession, AVCaptureSessionPresetPhoto,
                          AVCaptureStillImageOutput, AVMediaTypeMuxed,
                          AVMediaTypeVideo, AVVideoCodecJPEG)

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


_VERBOSE = False


def verbose(string):
    global _VERBOSE
    if _VERBOSE:
        print(string)


def generate_filename():
    filename = "snapshot.jpg"
    verbose(f"No filename specified. Using {filename}")
    return filename


class imageSnap:
    def __init__(self):
        print(f"__init__")
        self._imageQueue = libdispatch.dispatch_queue_create(b"Image Queue", None)
        self._semaphore = libdispatch.dispatch_semaphore_create(0)
        self._capture_device_input = (
            self._capture_session
        ) = self._capture_still_image_output = None
        self._devices = self.video_devices()
        print(self._imageQueue)

    @classmethod
    def video_devices(cls):
        """ return list of connected video devices """
        devices = [
            *AVCaptureDevice.devicesWithMediaType_(AVMediaTypeVideo),
            *AVCaptureDevice.devicesWithMediaType_(AVMediaTypeMuxed),
        ]
        return devices

    @classmethod
    def default_video_device(cls):
        device = AVCaptureDevice.defaultDeviceWithMediaType_(AVMediaTypeVideo)
        return device

    @classmethod
    def device_named(cls, name):
        """ returns device with localizedName == name """
        """ returns None if not found """
        devices = cls.video_devices()
        for dev in devices:
            if dev.localizedName() == name:
                return dev
        return None

    def save_single_snapshot(self, device=None, path=None, warmup=0, timelapse=None):
        if not device:
            device = self.default_video_device()
        if not path:
            path = generate_filename()

        interval = timelapse

        # device already started by get_ready_to_take_picture
        # todo: fix error in imagesnap.m here --> call get_ready...
        verbose("Starting device...")
        verbose("Device started.")

        if warmup <= 0:
            verbose("Skipping warmup period")
        else:
            verbose(f"Warming up for {warmup} seconds")
            time.sleep(warmup)

        if interval:
            verbose(
                f"Time lapse: snapping every {interval} seconds to current directory"
            )  # todo: current directory or path?
            seq = 0
            while True:
                self._take_snapshot_with_filename(
                    self._filename_with_sequence_number(seq)
                )
                seq += 1
                time.sleep(interval)
        else:
            self._take_snapshot_with_filename(path)

        self.stop_session()

    def setup_session_with_device(self, device):
        error = None

        # create the capture session
        self._capture_session = AVCaptureSession.alloc().init()
        if self._capture_session.canSetSessionPreset_(AVCaptureSessionPresetPhoto):
            self._capture_session.setSessionPreset_(AVCaptureSessionPresetPhoto)

        # create input object from device
        self._capture_device_input, error = AVCaptureDeviceInput.deviceInputWithDevice_error_(
            device, objc.nil
        )  # returns array with AVCaptureDeviceInput object and what I assume is the error

        print(self._capture_device_input)
        if not error and self._capture_session.canAddInput_(self._capture_device_input):
            self._capture_session.addInput_(self._capture_device_input)

        self._capture_still_image_output = AVCaptureStillImageOutput.alloc().init()
        self._capture_still_image_output.setOutputSettings_(
            {"AVVideoCodecKey": AVVideoCodecJPEG}
        )

        if self._capture_session.canAddOutput_(self._capture_still_image_output):
            self._capture_session.addOutput_(self._capture_still_image_output)

        # for (AVCaptureConnection *connection in self.captureStillImageOutput.connections) {
        self._video_connection = None
        for connection in self._capture_still_image_output.connections():
            for port in connection.inputPorts():
                # todo: kludge because I can't figure out how to use isEqual:
                # if ([port.mediaType isEqual:AVMediaTypeVideo] ) {
                if AVMediaTypeVideo in str(port.mediaType):
                    self._video_connection = connection
                    break
            if self._video_connection:
                break
        print(f"connection: {self._video_connection}")
        if self._capture_session.canAddOutput_(self._capture_still_image_output):
            self._capture_session.addOutput_(self._capture_still_image_output)

    def stop_session(self):
        verbose("Stopping session...")

        # make sure we've stopped
        while self._capture_session != objc.nil:
            verbose("\tCaptureSession != nil")

            verbose("\tStopping CaptureSession...")
            self._capture_session.stopRunning()
            verbose("Done.")

            if self._capture_session.isRunning():
                verbose("[captureSession isRunning]")
                time.sleep(0.1)
                # [[NSRunLoop currentRunLoop] runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.1]];
            else:
                verbose("\tShutting down 'stopSession(..)'")

                self._capture_session = objc.nil
                self._capture_device_input = objc.nil
                self._capture_still_image_output = objc.nil

    def get_ready_to_take_picture(self):
        self._capture_session.startRunning()

    #     for (AVCaptureInputPort *port in [connection inputPorts]) {
    #         if ([port.mediaType isEqual:AVMediaTypeVideo] ) {
    #             self.videoConnection = connection;
    #             break;
    #         }
    #     }
    #     if (self.videoConnection) { break; }
    # }

    # Internal methods
    def _create_connection_handler(self, filename):
        def _handler(buffer, error):
            print(f"_handler {filename}")
            image_data = AVCaptureStillImageOutput.jpegStillImageNSDataRepresentation_(
                buffer
            )
            # dispatch_async(self.imageQueue, ^{
            #              [imageData writeToFile:weakFilename atomically:YES];
            #              dispatch_semaphore_signal(_semaphore);
            #  });
            def _write_to_file():
                print(f"_write_to_file")
                image_data.writeToFile_atomically_(filename, True)
                libdispatch.dispatch_semaphore_signal(self._semaphore)

            print("calling dispatch_async")
            libdispatch.dispatch_async(self._imageQueue, _write_to_file)

        return _handler

    def _take_snapshot_with_filename(self, filename):
        handler = self._create_connection_handler(filename)
        print(f"connection: {self._video_connection}")
        self._capture_still_image_output.captureStillImageAsynchronouslyFromConnection_completionHandler_(
            self._video_connection, handler
        )

        # TODO: BUG: Not sure why this is needed but if we don't sleep, the dispatch_async code in handler never runs
        time.sleep(1)
        # 196

    def _filename_with_sequence_number(self, seq):
        now = datetime.now()
        nowstr = now.strftime("%Y-%m-%d_%H-%M-%S")
        msecstr = "{:0>3d}".format(int(now.microsecond / 1000))
        nowstr = f"{nowstr}.{msecstr}"
        seqstr = "{:0>5d}".format(seq)
        filename = f"snapshot-{seqstr}-{nowstr}.jpg"
        return filename

    def __del__(self):
        print("Goodbye!")
        self.stop_session()


def test():
    snap = imageSnap()
    for dev in snap.video_devices():
        print(f"id: {dev.deviceID()}")
        print(f"isInUse: {dev.isInUseByAnotherApplication()}")
        print(f"mfg: {dev.manufacturer()}")
        print(f"name: {dev.localizedName()}")

    default = snap.default_video_device()
    print(f"{default.localizedName()}")

    device = snap.device_named("FaceTime HD Camera")
    print(f"device: {device.localizedName()}")

    print("setup_session")
    snap.setup_session_with_device(snap.default_video_device())
    time.sleep(2)
    print("ready")
    snap.get_ready_to_take_picture()
    time.sleep(2)
    print("save_single")
    snap.save_single_snapshot(warmup=3)
    print(snap._file_name_with_sequence_number(42))
    del snap
    # snap._take_snapshot_with_filename("img.jpg")


if __name__ == "__main__":
    import argparse

    def process_args():
        parser = argparse.ArgumentParser(
            description="USAGE: imagesnap [options] [filename]"
            "Version: 0.2.5\n"
            "Captures an image from a video device and saves it in a file.\n"
            "If no device is specified, the system default will be used.\n"
            "If no filename is specfied, snapshot.jpg will be used.\n"
            "JPEG is the only supported output type."
        )
        parser.add_argument(
            "-v", action="store_true", default=False, help="Verbose mode"
        )
        parser.add_argument(
            "-l",
            action="store_true",
            default=False,
            help="List available video devices",
        )
        parser.add_argument(
            "-t",
            type=float,
            default=None,
            help="Take a picture every T seconds (min 1.0 seconds)",
        )
        parser.add_argument(
            "-q",
            action="store_true",
            default=False,
            help="Quiet mode. Do not output any text",
        )
        parser.add_argument(
            "-w",
            type=float,
            help="Warmup. Delay snapshot W seconds after turning on camera",
            default=0,
        )
        parser.add_argument(
            "-d", type=str, default=None, help="Use named video device D"
        )
        parser.add_argument("FILE", nargs="?")
        args = parser.parse_args()
        return args

    def list_devices():
        snap = imageSnap()
        devices = snap.video_devices()
        print("Video Devices:")
        for dev in devices:
            print(dev)

    _args = process_args()

    if _args.v:
        _VERBOSE = True
    if _args.q:
        _VERBOSE = False

    if _args.l:
        list_devices()
        sys.exit()

    device = None
    if _args.d:
        device = imageSnap.device_named(_args.d)
    else:
        device = imageSnap.default_video_device()
        verbose(f"No device specified. Using {device}")

    if not device:
        sys.exit("No video devices found.")
    else:
        if not _args.q:
            print(f"Capturing image from device {device}...")

    filename = _args.FILE if _args.FILE else generate_filename()
    snap = imageSnap()
    snap.setup_session_with_device(device)
    snap.get_ready_to_take_picture()
    snap.save_single_snapshot(
        device=device, path=filename, warmup=_args.w, timelapse=_args.t
    )
