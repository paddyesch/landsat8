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

import urllib
import httplib
import os
import gzip
import shutil
import random
import subprocess
import json
import time
import math
from landsat.downloader import Downloader
from landsat.image import Simple
from colorama import init, Fore
init(autoreset=True)

work_folder = "temp"

def download_scene_list():
    gzip_path = work_folder + "/scene_list.gz"
    unpack_path = work_folder + "/scene_list.csv"
    if os.path.isfile(unpack_path):
        now = time.time()
        last_modified = os.path.getmtime(unpack_path)
        interval_in_seconds = now - last_modified
        if interval_in_seconds < (3 * 60 * 60):
            print "Already downloaded list is recent enough (<3h) ..."
            return unpack_path

    print "Downloading ..."
    urllib.urlretrieve ("http://landsat-pds.s3.amazonaws.com/scene_list.gz", gzip_path)
    gzip_handle = gzip.open(gzip_path)
    with open(unpack_path, "w") as out:
        for line in gzip_handle:
            out.write(line)
    return unpack_path

def tail_from_scene_list(file_path, num_scenes):
    stdin, stdout = os.popen2("tail -n " + str(num_scenes) + " " + file_path)
    stdin.close()
    lines = stdout.readlines(); stdout.close()
    scenes = list()
    for line in lines:
        tokens = line.split(',')
        scene = (tokens[0], tokens[10][:-11]) # Remove /index.hmtl\n
        scenes.append(scene)
    return scenes

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

def download_mtl(scene):
    mtl_path = work_folder + "/" + scene[0] + "_scene.mtl"
    urllib.urlretrieve (scene[1] + scene[0] + "_MTL.txt", mtl_path)
    return parse_mtl(mtl_path)

def is_scene_suitable(scene, max_cloud_cover):
    mtl = download_mtl(scene)
    projection = mtl["L1_METADATA_FILE"]["PROJECTION_PARAMETERS"]["MAP_PROJECTION"]
    cloud_cover = mtl["L1_METADATA_FILE"]["IMAGE_ATTRIBUTES"]["CLOUD_COVER"]
    cloud_cover = float(cloud_cover)
    return projection == '"UTM"' and cloud_cover < max_cloud_cover

def find_scene(max_cloud_cover):
    print Fore.GREEN + "# Downloading scene list ..."
    if not os.path.exists(work_folder):
        os.makedirs(work_folder)
    num_scenes = 500
    file_path = download_scene_list()
    print ""
    print Fore.GREEN + "# Finding recent and suitable scene ..."
    scenes = tail_from_scene_list(file_path, num_scenes)
    for count in range(0, num_scenes):
        random_index = random.randint(0, num_scenes - 1)
        scene = scenes[random_index]
        if is_scene_suitable(scene, max_cloud_cover):
            print scene[0]
            print ""
            return scene[0]
    print "No suitable scene found ..."
    return ""

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
    convertedJPG = scene_id + ".jpg"
    command = "convert -quality {} -resize {}% {} {}".format(str(quality_in_percent), str(resize_in_percent), processedTIF, convertedJPG)
    subprocess.call(command, shell=True)
    print ""

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

def calculate_latlon_midpoint(lat1, lon1, lat2, lon2):
    "Calculation of geographic midpoint with method A: http://www.geomidpoint.com/calculation.html"
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    w1 = 1
    w2 = 2
    w_total = w1 + w2
    x1 = math.cos(lat1) * math.cos(lon1)
    y1 = math.cos(lat1) * math.sin(lon1)
    z1 = math.sin(lat1)
    x2 = math.cos(lat2) * math.cos(lon2)
    y2 = math.cos(lat2) * math.sin(lon2)
    z2 = math.sin(lat2)
    x = ((x1 * w1) + (x2 * w2)) / w_total
    y = ((y1 * w1) + (y2 * w2)) / w_total
    z = ((z1 * w1) + (z2 * w2)) / w_total
    hyp = math.sqrt(x * x + y * y)
    mid_lat = math.atan2(z, hyp)
    mid_lon = math.atan2(y, x)
    return (math.degrees(mid_lat), math.degrees(mid_lon))

def collect_metadata(scene_id):
    print Fore.GREEN + "# Collecting metadata ..."
    mtl_path = work_folder + "/" + scene_id + "/" + scene_id + "_MTL.txt"
    mtl = parse_mtl(mtl_path)
    date = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["DATE_ACQUIRED"]
    cloud_cover = mtl["L1_METADATA_FILE"]["IMAGE_ATTRIBUTES"]["CLOUD_COVER"]
    ll_lat = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LL_LAT_PRODUCT"]
    ll_lon = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_LL_LON_PRODUCT"]
    ur_lat = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_UR_LAT_PRODUCT"]
    ur_lon = mtl["L1_METADATA_FILE"]["PRODUCT_METADATA"]["CORNER_UR_LON_PRODUCT"]
    center_latlon = calculate_latlon_midpoint(float(ll_lat), float(ll_lon), float(ur_lat), float(ur_lon))
    countries = list(determine_countries(mtl))
    print "Scene ID: " + scene_id
    print "Date acquired: " + date
    print "Cloud cover: " + cloud_cover
    print "Lower left latitude: " + ll_lat
    print "Lower left longitude: " + ll_lon
    print "Upper right latitude: " + ur_lat
    print "Upper right longitude: " + ur_lon
    print "Center latitude: " + str(center_latlon[0])
    print "Center longitude: " + str(center_latlon[1])
    print "Countries: " + str(countries)

    metadata = {}
    metadata["scene_id"] = scene_id
    metadata["date_acquired"] = date
    metadata["cloud_cover"] = float(cloud_cover)
    metadata["lower_left_lat"] = float(ll_lat)
    metadata["lower_left_lon"] = float(ll_lon)
    metadata["upper_right_lat"] = float(ur_lat)
    metadata["upper_right_lon"] = float(ur_lon)
    metadata["center_lat"] = center_latlon[0]
    metadata["center_lon"] = center_latlon[1]
    metadata["countries"] = countries

    metadataPath = scene_id + "_metadata.json"
    with open(metadataPath, "w") as outfile:
        json.dump(metadata, outfile)
    print ""

def create_soft_links(scene_id):
    print Fore.GREEN + "# Creating soft links ..."
    lns_source_path = scene_id + ".jpg"
    lns_target_path = "LATEST.jpg"
    lns_meta_source_path = scene_id + "_metadata.json"
    lns_meta_target_path = "LATEST_metadata.json"
    try:
        os.remove(lns_target_path)
    except:
        pass
    try:
        os.remove(lns_meta_target_path)
    except:
        pass
    os.symlink(lns_source_path, lns_target_path)
    os.symlink(lns_meta_source_path, lns_meta_target_path)
    print lns_target_path
    print lns_meta_target_path
    print ""

def clean_up_scene(scene_id):
    print Fore.GREEN + "# Cleaning up ..."
    clean_path = work_folder + "/" + scene_id
    shutil.rmtree(clean_path)
    print clean_path

    clean_mtl = work_folder + "/" + scene_id + "_scene.mtl"
    try:
        os.remove(clean_mtl)
        print clean_mtl
    except:
        pass
        
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
