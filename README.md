# PyImageSnap

This is a clone (almost line-by-line) of Robert Harder's [imagesnap](https://github.com/rharder/imagesnap) for Mac.  It can be used to take a single photo or multiple time-lapsed photos using the Mac's built-in camera (or any other attached video device)

## Motivation

I built this for two reasons:

1) I wanted an easy way to programmaticly take a picture using the Mac's built in camera.  I wanted something lighter weight than [OpenCV](https://github.com/opencv/opencv) 
2) I wanted to learn [PyObjC](https://pyobjc.readthedocs.io/en/latest/) and needed a good project with which to do so.

## Getting Started

### Prerequisites

Install [PyObjC](https://pypi.org/project/pyobjc/)

```
pip install pyobjc
```

Note: This uses Cocoa framework APIs that are deprecated in OS X 10.15+.  It may not run on Catalina or may complain loudly if it does run. I've only tested in on OS X 10.14.6 (Mojave).

### Installing

Currently, everything in imagesnap.py.  I may refactor this to a package.

### Usage

```python3 imagesnap.py -h```

```usage: imagesnap.py [-h] [-v] [-l] [-t T] [-q] [-w W] [-d D] [FILE]
usage: imagesnap.py [-h] [-v] [-l] [-t T] [-q] [-w W] [-d D] [FILE]

USAGE: imagesnap [options] [filename]
Version: 0.2.5
Captures an image from a video device and saves it in a file.
If no device is specified, the system default will be used.
If no filename is specfied, snapshot.jpg will be used.
JPEG is the only supported output type.

positional arguments:
  FILE

optional arguments:
  -h, --help  show this help message and exit
  -v          Verbose mode
  -l          List available video devices
  -t T        Take a picture every T seconds (min 1.0 seconds)
  -q          Quiet mode. Do not output any text
  -w W        Warmup. Delay snapshot W seconds after turning on camera
  -d D        Use named video device D
  ```

## Known Issues

The minimum time between timelapse photos is 1.0 seconds.  This is a work-around to an issue with dispatch_async I've not yet solved.

## Authors

* **Rhet Turnbull** - *Python implementation* - [PyImageSnap](https://github.com/RhetTbull/PyImageSnap)
* **Robert Harder** - *Initial work in objective C* - [imagesnap](https://github.com/rharder/imagesnap)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## See Also

[OpenCV-IAV](https://github.com/macornwell/opencv-image-and-video) which provides a simpler interface to OpenCV for taking photos.

## Acknowledgments

* Thanks much to Robert Harder who built imagesnap and made it freely available to the Mac community.
* Thanks much to Ronald Oussoren who made it possible to use native Mac APIs directly in Python with PyObjC.