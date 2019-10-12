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

### Installing

Currently, everything in imagesnap.py.  I may refactor this to a package.

## Authors

* **Rhet Turnbull** - *Python implementation* - [PyImageSnap](https://github.com/RhetTbull/PyImageSnap)
* **Robert Harder** - *Initial work in objective C* - [imagesnap](https://github.com/rharder/imagesnap)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## See Also

[OpenCV-IAV](https://github.com/macornwell/opencv-image-and-video) which provides a simpler interface to OpenCV for taking photos.

## Acknowledgments

Thanks much to Robert Harder who built imagesnap and made it freely available to the Mac community.
Thanks much to Ronald Oussoren who made it possible to use native Mac APIs directly in Python with PyObjC.