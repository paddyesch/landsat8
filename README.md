# Landsat8

Command line tool for downloading the latest available Landsat8 scene and converting it to a natural color JPG image.
Downloading and processing of the image bands is done by the [landsat-util](https://github.com/developmentseed/landsat-util).

## Usage

Latest available scene with default parameters:

```
$ landsat8
```

Specific scene with resizing to 40%:

```
$ landsat8 --scene LC81520432016280LGN00 --resize 40
```

## Build & Install

This tool has only been tested on Ubuntu and Fedora Linux.

* Install `imagemagick`
* Install dependencies for [landsat-util](https://pythonhosted.org/landsat-util/installation.html)
* Clone the repository and execute `python setup.py install` with `sudo` or use virtualenv

## License

MIT License

Copyright (c) 2016 Patrick Eschenbach
