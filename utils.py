import os
import json
from geopandas.geodataframe import GeoDataFrame
import requests
from urllib.request import urlopen
from io import BytesIO
import numpy as np
import rasterio
from rasterio import features
from PIL import Image


def find_shp_paths(src_path:str):
    # Find all shp and keep centroid
    shp_paths = []
    for root, _, files in os.walk(src_path):
        for name in files:
                if name.endswith('.shp'):
                    shp_paths.append(os.path.join(root, name))
    return shp_paths


def data_centre(dst_dir:str, counter:int, shp_data:GeoDataFrame):
    # Bounds of whole shapefile
    bounds = shp_data.total_bounds
    # Rename and save shapefile to new dst
    shp_dst_fname = f"bb_{counter}.shp"
    shp_data.to_file(os.path.join(dst_dir, shp_dst_fname))
    # Mean coordinates
    mean_lat = (bounds[1]+bounds[3]) / 2
    mean_lon = (bounds[0]+bounds[2]) / 2
    return mean_lat, mean_lon



def bm_rgb_img(lat, lon, **kargs):
    z = kargs['z']
    h = kargs['h']
    w = kargs['w']
    # Image
    url_image=f"https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/{lat},{lon}/{z}?mapSize={w},{h}&key={bm_apikey}"
    response = requests.get(url_image)
    str2img = BytesIO(response.content)
    image = Image.open(str2img).convert('RGB')
    imgArray = np.array(image)
    imgArray=np.moveaxis(imgArray,-1,0)
    return imgArray


def bm_img_bbox(lat, lon, **kargs):
    z = kargs['z']
    h = kargs['h']
    w = kargs['w']
    # Image bounding box
    url_image=f"https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/{lat},{lon}/{z}?mapSize={w},{h}&mmd=1&key={bm_apikey}"
    metadata = urlopen(url_image).read()
    metadata = json.loads(metadata)
    bbox = metadata['resourceSets'][0]['resources'][0]['bbox']
    return bbox

def _clip_logo(imgArray, minus_pixels, **kargs):
    return imgArray[:, 0:kargs['h']-minus_pixels, 0:kargs['w']-minus_pixels]


def trans_after_logo_clipping(old_trans, clipped_imgArray):
    # Use old transformation to gain the new transformation
    # ul = old_trans * (0, 0)
    dl = old_trans * (clipped_imgArray.shape[1], 0)
    ur = old_trans * (0, clipped_imgArray.shape[2])
    new_trans = rasterio.transform.from_bounds(
        ur[0], ur[1], dl[0], dl[1], clipped_imgArray.shape[1], clipped_imgArray.shape[2])
    return new_trans


def rasterize_annots(dst_dir, counter, rgb_ref_array, rgb_ref_meta, shp_data:GeoDataFrame):
    # Create iterable of (geometry, value) pairs
    l = [[row.geometry, row.id] for _, row in shp_data.iterrows()]
    # Burn
    lb_img = features.rasterize(
            l,
            out_shape = (rgb_ref_array.shape[1], rgb_ref_array.shape[2]),
            all_touched = False, # pixels whose center is within the polygon
            transform = rgb_ref_meta['transform'])
    # Update dst metadata
    rgb_ref_meta.update(dtype=lb_img.dtype, count=1)
    # Write result as image
    lb_dst_fpath = os.path.join(dst_dir, f"lb_{counter}.tif")
    with rasterio.open(lb_dst_fpath, 'w', **rgb_ref_meta) as out:
        out.write_band(1, lb_img)
    return 0