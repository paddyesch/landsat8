# MIT License
#
# Copyright (c) 2016 Patrick Eschenbach
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import feedparser
import httplib
import re
import os
import shutil
import subprocess
import json
from landsat.downloader import Downloader
from landsat.image import Simple
from colorama import init, Fore
init(autoreset=True)

aws_domain = "landsat-pds.s3.amazonaws.com"
work_folder = "temp"

def construct_scene_url_path(scene_id):
    return "/L8/" + scene_id[3:6] + "/" + scene_id[6:9] + "/" + scene_id

def is_scene_available(scene_id):
    connection = httplib.HTTPConnection(aws_domain)
    connection.request("GET", construct_scene_url_path(scene_id) + "/index.html")
    response = connection.getresponse()
    return response.status == 200

def extract_scene_id_from_description(description):
    match_obj = re.search(r'^Scene ID: (.*)$', description, re.M|re.I)
    if match_obj:
        return match_obj.group(1)
    else:
        return ""

def bisect_scenes(scenes):
    lo = 0
    hi = len(scenes)
    while lo < hi:
        mid = (lo+hi)//2
        scene_id = extract_scene_id_from_description(scenes[mid].description)
        print "Trying " + scene_id + " - Entry " + str(mid)
        if is_scene_available(scene_id): hi = mid
        else: lo = mid + 1
    if lo < len(scenes):
        result_scene_id = extract_scene_id_from_description(scenes[lo].description)
        if is_scene_available(result_scene_id): return result_scene_id
    return ""

def find_latest_scene_id():
    print Fore.GREEN + "# Finding the latest scene ..."
    feed_url = "https://landsat.usgs.gov/Landsat8.rss"
    print "Reading from " + feed_url
    feed = feedparser.parse(feed_url)
    scene_id = bisect_scenes(feed.entries)
    print scene_id
    print ""
    return scene_id

def download_scene(scene_id):
    print Fore.GREEN + "# Downloading scene ..."
    downloader = Downloader(verbose=True, download_dir=work_folder)
    loaded = downloader.download([str(scene_id)], [4, 3, 2])
    print ""
    return len(loaded) == 1

def convert_scene(scene_id, quality_in_percent, resize_in_percent):
    print Fore.GREEN + "# Processing scene ..."
    processor = Simple(work_folder + "/" + scene_id, [4, 3, 2], work_folder)
    processedTIF = processor.run()
    convertedJPG = scene_id + ".JPG"
    command = "convert -quality {} -resize {}% {} {}".format(str(quality_in_percent), str(resize_in_percent), processedTIF, convertedJPG)
    subprocess.call(command, shell=True)
    print ""

def parse_mtl(mtl_path):
    mtl = dict()
    groupStack = [mtl];

    for line in open(mtl_path, "r"):
        if line.strip() == "END":
            break

        parts = line.split("=", 1)
        key   = parts[0].strip()
        value = parts[1].strip()

        if key == "GROUP":
            group = dict()
            groupStack[-1][value] = group
            groupStack.append(group)
        elif key == "END_GROUP":
            groupStack.pop()
        else:
            groupStack[-1][key] = value

    return mtl

def determine_country(lat, lon):
    connection = httplib.HTTPConnection("maps.googleapis.com")
    connection.request("GET", "/maps/api/geocode/json?latlng={},{}".format(lat, lon))
    response = json.load(connection.getresponse())
    if response["status"] == "OK":
        for result in response["results"]:
            if "country" in result["types"]:
                return result["formatted_address"]
    return ""

def determine_countries(mtl):
    ll_lat = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LL_LAT_PRODUCT"]
    ll_lon = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LL_LON_PRODUCT"]
    lr_lat = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LR_LAT_PRODUCT"]
    lr_lon = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LR_LON_PRODUCT"]
    ur_lat = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_UR_LAT_PRODUCT"]
    ur_lon = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_UR_LON_PRODUCT"]
    ul_lat = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_UL_LAT_PRODUCT"]
    ul_lon = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_UL_LON_PRODUCT"]

    countries = set([determine_country(ll_lat, ll_lon),
                     determine_country(lr_lat, lr_lon),
                     determine_country(ur_lat, ur_lon),
                     determine_country(ul_lat, ul_lon)])
    if "" in countries: countries.remove("")
    return countries

def collect_metadata(scene_id):
    print Fore.GREEN + "# Collecting metadata ..."
    mtl_path = work_folder + "/" + scene_id + "/" + scene_id + "_MTL.txt"
    mtl = parse_mtl(mtl_path)
    date = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["DATE_ACQUIRED"]
    ll_lat = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LL_LAT_PRODUCT"]
    ll_lon = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LL_LON_PRODUCT"]
    countries = list(determine_countries(mtl))
    print "Date acquired: " + date
    print "Lower left latitude: " + ll_lat
    print "Lower left longitude: " + ll_lon
    print "Countries: " + str(countries)

    metadata = {}
    metadata["date_acquired"] = date
    metadata["lower_left_lat"] = ll_lat
    metadata["lower_left_lon"] = ll_lon
    metadata["countries"] = countries

    metadataPath = scene_id + "_metadata.json"
    with open(metadataPath, "w") as outfile:
        json.dump(metadata, outfile)
    print ""

def clean_up_scene(scene_id):
    print Fore.GREEN + "# Cleaning up ..."
    clean_path = work_folder + "/" + scene_id
    shutil.rmtree(clean_path)
    print clean_path
    try:
        os.rmdir(work_folder)
        print work_folder + "/"
    except:
        print work_folder + "/ is not empty: no action"
    print ""

def print_scene_result(scene_id):
    print Fore.GREEN + "# Scene image created ..."
    print scene_id + ".JPG"
    print scene_id + "_metadata.json"
    print ""
