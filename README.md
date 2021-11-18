# bingmapclipper
Clip Bing Maps backgound as RGB geotif image using center-point from vector data of a shapefile and Bing Maps zoom. Also, rasterize shapefile vectors as corresponding label image.



First of all you need a key based on your google account.

Download image from bing maps, using a center point of a
shapefile having a small spatial extend.
Each shapefile will result in a 'chip' image, ready
to use for machine/deep learning algorithms.

All results will be saved in 'results' directory.
All results have common CRS 4326.

Usage:
python3 test_retrieve_mangos_ims.py -srcpth /src/of/shapefiles/ -zoom 18 -im_h 430 -im_w 670