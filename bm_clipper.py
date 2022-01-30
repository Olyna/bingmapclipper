r"""
First of all you need a key based on your google account.
https://dmitryrogozhny.com/blog/getting-static-map-bing-image

Download image from bing maps, using a center point of a
shapefile having a small spatial extend.
Each shapefile will result in a 'chip' image, ready
to use for machine/deep learning algorithms.

All results will be saved in 'results' directory.
All results have common CRS 4326.


Usage:
python3 bm_clipper.py -srcpth /home/olyna/Documents/RSLab/dimitris_mangos_ships/by_mangos/ships_dataset_v4/ships_ORIG_classes/ships_raw_data -zoom 18 -im_h 430 -im_w 670
"""
import os
import rasterio
import geopandas as gpd
from argparse import ArgumentParser
import utils


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
        imgArray = utils.bm_rgb_img(lat, lon, **k_args)

        # Retrieve image bounding box
        bbox = utils.bm_img_bbox(lat, lon, **k_args)

        # Transformation of original downloaded image
        old_trans = rasterio.transform.from_bounds(bbox[1], bbox[0], bbox[3], bbox[2], args.im_w, args.im_h)

        # # Save original downloaded rgb image (with Microsoft logo)
        # with rasterio.open(
        #     'blas_orig_dowloaded.tif',
        #     'w',
        #     driver='GTiff',
        #     height=h,
        #     width=w,
        #     count=3,
        #     dtype=imgArray.dtype,
        #     crs=4326,
        #     transform=old_trans,
        #     ) as dst:
        #         dst.write(imgArray)

        ## Clip Microsoft logo from original downloaded image, create new transformation and over-write
        clipped_imgArray = utils._clip_logo(imgArray, minus_pixels, **k_args)

        # New transformation after clipped logo
        new_trans = utils.trans_after_logo_clipping(old_trans, clipped_imgArray)

        # Save final RGB image (without Microsoft logo)
        im_dst_fname = os.path.join(dst_path, f"im_{counter}.tif")
        with rasterio.open(
            im_dst_fname,
            'w',
            driver='GTiff',
            height=clipped_imgArray.shape[1],
            width=clipped_imgArray.shape[2],
            count=3,
            dtype=clipped_imgArray.dtype,
            crs=4326,
            transform=new_trans,
            ) as dst:
                dst.write(clipped_imgArray)
                rgb_ref_meta = dst.meta

        # Burn vector annotations fron shp to label georeferenced raster
        utils.rasterize_annots(dst_path, counter, clipped_imgArray, rgb_ref_meta, shp_data)

        # Augment counter
        counter = counter + 1

    # Save all annotations as one geodataframe
    all_annots.to_file(os.path.join(dst_path, 'all_annots.shp'), crs=shp_data.crs)