__version__ = '0.1.0'

import os

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.geometry import shape
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Any, Union, Dict, Optional

import rasterio
import rasterio.mask

import json

tag_metadata = [{
    "name": "meta",
    "description": "Metadati sul csv"
}, {
    "name": "data",
    "description": "Dati"
}, {
    "name": "geo",
    "description": "Geodati"
}]

app = FastAPI(
    title="raster operations",
    openapi_tags = tag_metadata
)

FILE = os.environ.get('FILE', 'nnb_osservazioniweb_point_v2.csv')
DEBUG = os.environ.get('DEBUG') is not None


@app.get('/')
async def index():
    """documentazione"""
    return ""

class dPolygon(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

class pPoint(BaseModel):
    type: str
    coordinates: List[float]

class Feature(BaseModel):
    type: str
    properties: Any
    geometry: pPoint

class FeatureCollection(BaseModel):
    type: str
    features: List[Feature]




    
import uuid
from fastapi.responses import FileResponse
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio import Affine as A


@app.post('/{date}/clouds.geojson')
async def filter_data_2(date:str, body: str):
    shp = json.loads(body)
    is_valid = dPolygon(**shp)
    poly = shape(shp)

    clouds = gpd.read_file('AwsData/32TQM,{},0/qi/MSK_CLOUDS_B00.gml'.format(date))
    clouds.to_crs('EPSG:4326', inplace=True)
    print(clouds.count())
    clouds = clouds[clouds['geometry'].is_valid]
    print(clouds.count())
    clouds['geom2'] = clouds['geometry'].intersection(poly)
    ret = clouds[~clouds['geom2'].is_empty]
    ret = ret.drop('geom2',axis=1)
    return json.loads(ret.to_json())


@app.post('/{date}/{band}/data.geotiff', response_class=FileResponse)
async def filter_data_2(date: str, band: str, body: str):
    shp = json.loads(body)
    is_valid = dPolygon(**shp)
    poly = shape(shp)
    dst_crs = 'EPSG:4326'

    if not os.path.exists('AwsData/32TQM,{},0/{}.wgs84.tif'.format(date, band)):
        with rasterio.open("AwsData/32TQM,{},0/{}.jp2".format(date, band)) as src:

            transform, width, height = calculate_default_transform(
                    src.crs, dst_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open('AwsData/32TQM,{},0/{}.wgs84.tif'.format(date, band), 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)

    with rasterio.open("AwsData/32TQM,{},0/{}.wgs84.tif".format(date, band)) as src:

        out_image, out_transform = rasterio.mask.mask(src, [poly], crop=True)
        out_meta = src.meta
        out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})

        fname = str(uuid.uuid4())
        with rasterio.open("{}.tif".format(fname), "w", **out_meta) as dest:
            dest.write(out_image)
    return FileResponse("{}.tif".format(fname))

    
    