"""



Usage:
python3 gm_clipper.py -srcpth /home/olyna/Documents/RSLab/dimitris_mangos_ships/by_mangos/ships_dataset_v4/ships_ORIG_classes/ships_raw_data -zoom 18 -im_h 430 -im_w 670 -k AIzaSyByv2Wdy-kimcmDw6iZg0_PCbOCqpfZ2uM
"""
import os
import sys
import json
import rasterio
import geopandas as gpd
from argparse import ArgumentParser
import utils
import requests
import urllib
from urllib.request import urlopen
from io import BytesIO
from PIL import Image
import numpy as np

if __name__ == '__main__':

    # Create argument-parser
    arg_parser = ArgumentParser(description="Clip RGB images from Bing Maps,\
    Save RGB image as georeferenced raster. Burn annotation of shapefile to\
    label georeferenced image.")

    # Add arguments to argument-parser
    arg_parser.add_argument("-srcpth", dest="srcpth", required=True, type=str,
    help="Dictionary containing shapefiles with corresponding annotations.\
    Each shapefile must has a small spatial extend.")

    arg_parser.add_argument("-zoom", dest="zoom", required=True, type=int,
    help="Bing maps zoom.")

    arg_parser.add_argument("-im_h", dest="im_h", required=True, type=int,
    help="Height of final rgb and label images.")

    arg_parser.add_argument("-im_w", dest="im_w", required=True, type=int,
    help="Width of final rgb and label images.")

    arg_parser.add_argument("-k", dest="gm_api_key", required=True, type=str,
    help="Width of final rgb and label images.")

    # Parse arguments
    args = arg_parser.parse_args()

    # These 25 pixel will be cutted by rgb image, cuz I want to remove microsoft logo
    minus_pixels = 25
    args.im_h = args.im_h + minus_pixels
    args.im_w = args.im_w + minus_pixels

    # Create filesystem to save results
    dst_path = os.path.join(os.path.dirname(args.srcpth), 'bm_results')
    try:
        os.mkdir(dst_path)
    except:
        pass

    # Find all shp full-paths
    shp_paths = utils.find_shp_paths(args.srcpth)

    counter = 0
    all_annots = gpd.GeoDataFrame()
    for shp_path in shp_paths:
        print(f"{counter} - {os.path.basename(shp_path)}")
        # Read shp
        shp_data = gpd.read_file(shp_path)
        shp_data = shp_data.to_crs(4326)

        # Mean lat lon of current shp
        lat, lon = utils.data_centre(dst_path, counter, shp_data)

        # Gather all vector data to save as one dataframe, just to check data
        all_annots = all_annots.append(shp_data)

        # Retrieve RGB image as array
        k_args = {'z':args.zoom,
                'w':args.im_w,
                'h':args.im_h}

        # Image
        url_image=f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom={args.zoom}&size={args.im_w}x{args.im_h}&maptype=satellite&key={args.gm_api_key}"

        response = requests.get(url_image)
        # wb mode is stand for write binary mode
        f = open(f'{counter}_test_img.png ', 'wb')

        # r.content gives content,
        # in this case gives image
        f.write(response.content)
        
        # close method of file object
        # save and close the file
        f.close()
        counter = counter +1
