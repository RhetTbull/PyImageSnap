""" Python implementation of Robert Harder's imagesnap for Mac """
""" For original objective C version, see https://github.com/rharder/imagesnap """

import sys
import time
from datetime import datetime

import CoreMedia  # needed to prevent ObjCPointerWarning: PyObjCPointer created:...type ^{opaqueCMSampleBuffer=}.
import libdispatch
import objc
from AVFoundation import (
    AVCaptureDevice,
    AVCaptureDeviceInput,
    AVCaptureSession,
    AVCaptureSessionPresetPhoto,
    AVCaptureStillImageOutput,
    AVMediaTypeMuxed,
    AVMediaTypeVideo,
    AVVideoCodecJPEG,
)

# TODO: Fix bug with dispatch_async code requiring sleep(1)
# TODO: AVCaptureDevices.devices deprecated in 10.15

# Globals
_VERBOSE = False

# Utility functions
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
        self._imageQueue = libdispatch.dispatch_queue_create(b"Image Queue", None)
        self._semaphore = libdispatch.dispatch_semaphore_create(0)
        self._capture_device_input = (
            self._capture_session
        ) = self._capture_still_image_output = None
        self._devices = self.video_devices()

    # Public interface
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
        """ return default video device """
        device = AVCaptureDevice.defaultDeviceWithMediaType_(AVMediaTypeVideo)
        return device

    @classmethod
    def device_named(cls, name):
        """ return device with localizedName == name """
        """ return None if not found """
        """ example: if name == "FaceTime HD Camera", returns the built in front-facing camera """
        devices = cls.video_devices()
        for dev in devices:
            if dev.localizedName() == name:
                return dev
        return None

    def save_single_snapshot(self, device=None, path=None, warmup=0, timelapse=None):
        """ take a photo and save it to file """
        """ named after original function in imagesnap but is somewhat poorly named """
        """ as if timelapse > 0, it will take multiple photos """
        """ device: handle to device to use, as returned by video_devices() """
        """ path: output path for the jpeg file """
        """ warmup: number of seconds to warmup the camera before taking photo (float) """
        """ timelapse: number of seconds to wait before taking multiple photos (float) """
        """            if timelapse > 0, this function will run in infinite loop, taking a """
        """            photo every timelapse seconds; image file names will be timestamped """
        """            if timelapse > 0, path is ignored and timelapse images created in current working directory """

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
        """ setup the capture session for device """
        error = None

        # create the capture session
        self._capture_session = AVCaptureSession.alloc().init()
        if self._capture_session.canSetSessionPreset_(AVCaptureSessionPresetPhoto):
            self._capture_session.setSessionPreset_(AVCaptureSessionPresetPhoto)

        # create input object from device
        self._capture_device_input, error = AVCaptureDeviceInput.deviceInputWithDevice_error_(
            device, objc.nil
        )  # returns array with AVCaptureDeviceInput object and what I assume is the error

        if not error and self._capture_session.canAddInput_(self._capture_device_input):
            self._capture_session.addInput_(self._capture_device_input)

        self._capture_still_image_output = AVCaptureStillImageOutput.alloc().init()
        self._capture_still_image_output.setOutputSettings_(
            {"AVVideoCodecKey": AVVideoCodecJPEG}
        )

        if self._capture_session.canAddOutput_(self._capture_still_image_output):
            self._capture_session.addOutput_(self._capture_still_image_output)

        self._video_connection = self._capture_still_image_output.connectionWithMediaType_(
            AVMediaTypeVideo
        )

    def stop_session(self):
        """ tear down the capture session for device """
        """ call this when done taking pictures to free the device for use by other processes """

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
        """ start the capture session (turn on camera) """
        """ call this after calling setup_session_with_device """
        self._capture_session.startRunning()

    # Private methods
    def _create_connection_handler(self, filename):
        """ create completion handler function to pass to _capture_still_image_output.captureStillImageAsynchronouslyFromConnection_completionHandler_ """

        def _handler(buffer, error):
            image_data = AVCaptureStillImageOutput.jpegStillImageNSDataRepresentation_(
                buffer
            )
            # dispatch_async(self.imageQueue, ^{
            #              [imageData writeToFile:weakFilename atomically:YES];
            #              dispatch_semaphore_signal(_semaphore);
            #  });
            def _write_to_file():
                retval = image_data.writeToFile_atomically_(filename, True)
                libdispatch.dispatch_semaphore_signal(self._semaphore)

            libdispatch.dispatch_async(self._imageQueue, _write_to_file)

        return _handler

    def _take_snapshot_with_filename(self, filename):
        """ take a photo and save to filename """

        # - (void)captureStillImageAsynchronouslyFromConnection:(AVCaptureConnection *)connection
        #                          completionHandler:(void (^)(CMSampleBufferRef imageDataSampleBuffer, NSError *error))handler;

        # capture_handle = self._create_connection_handler(filename)
        # def capture_handle(buffer, err):
        #     print("capture_handle")
        #     image_data = AVCaptureStillImageOutput.jpegStillImageNSDataRepresentation_(
        #         buffer
        #     )
        #     retval = image_data.writeToFile_atomically_(filename, True)

        capture_handle = self._create_connection_handler(filename)
        self._capture_still_image_output.captureStillImageAsynchronouslyFromConnection_completionHandler_(
            self._video_connection, capture_handle
        )

        # BUG: Not sure why this is needed but if we don't sleep, the dispatch_async code in handler never runs
        time.sleep(1)

    def _filename_with_sequence_number(self, seq):
        """ create a filename if format snapshot-00001-YYYY-MM-ddd_HH-mm-ss.sss.jpg """
        now = datetime.now()
        nowstr = now.strftime("%Y-%m-%d_%H-%M-%S")
        msecstr = "{:0>3d}".format(int(now.microsecond / 1000))
        nowstr = f"{nowstr}.{msecstr}"
        seqstr = "{:0>5d}".format(seq)
        filename = f"snapshot-{seqstr}-{nowstr}.jpg"
        return filename

    def __del__(self):
        self.stop_session()


def _test():
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
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="USAGE: imagesnap [options] [filename]\n"
            "Version: 0.2.5\n"
            "Captures an image from a video device and saves it in a file.\n"
            "If no device is specified, the system default will be used.\n"
            "If no filename is specfied, snapshot.jpg will be used.\n"
            "JPEG is the only supported output type.",
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
    snap.stop_session()
