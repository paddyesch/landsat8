# Landsat8

Command line tool for downloading Landsat8 scenes and converting them to natural color JPG images.
The downloading and image band processing for natural colors is done by the [landsat-util](https://github.com/developmentseed/landsat-util) library.
I use this tool for creating daily satellite images for my [website](http://patrickeschenbach.de).

## Examples

Randomly chosen but recent scene with default parameters:

```
$ landsat8
```

Random recent scene with maximum cloud cover of 30%:

```
$ landsat8 --cloud 30
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

## Scene Metadata

The following metadata is collected for a scene and provided as JSON file:

```json
{
    "scene_id": "LC81860252017120LGN00",
    "center_lat": 50.62015,
    "center_lon": 23.61397,
    "cloud_cover": 67.34,
    "countries": [
        "Ukraine",
	"Poland",
	"Slovakia"
    ],
    "upper_right_lat": 51.29884,
    "upper_right_lon": 24.7672,
    "lower_left_lat": 49.22997,
    "lower_left_lon": 21.40519,
    "date_acquired": "2017-04-30"
}
```

## Usage

```
Usage: landsat8 [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -c, --cleanup         clean up all files created during the process
                        [default: keep all files]
  -s SCENE, --scene=SCENE
                        choose the scene by its landsat scene ID [default:
                        find a suitable and recent scene randomly]
  -o CLOUD, --cloud=CLOUD
                        find a scene with the given maximum cloud cover in
                        percent [default: any cloud cover]
  -q QUALITY, --quality=QUALITY
                        set the image output quality in percent [default: use
                        80% quality]
  -r RESIZE, --resize=RESIZE
                        set the image output size in percent of the original
                        [default: use 50% original size]
  -l, --symlink         create symbolic links LATEST.jpg and
                        LATEST_metadata.json [default: no symbolic links]
```

## License

MIT License

Copyright (c) 2016 Patrick Eschenbach
