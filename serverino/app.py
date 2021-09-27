__version__ = '0.1.0'

import os

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Any, Union

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
    title="serverino",
    description="""
    asdasdas
    asdaf
    asfasdfasdf
    """,
    openapi_tags = tag_metadata
)

FILE = os.environ.get('FILE', 'nnb_osservazioniweb_point_v2.csv')
DEBUG = os.environ.get('DEBUG') is not None

osservazioni = pd.read_csv(FILE)
geo_osservazioni = gpd.GeoDataFrame(osservazioni, 
            geometry=gpd.points_from_xy(osservazioni.lon, osservazioni.lat))
           
@app.get('/')
async def index():
    """documentazione"""
    return ""

@app.get('/columns', tags=["meta"], response_model=List[str])
async def columns():
    """Lista delle colonne
    siamo sempre nel commento
    
    * caso a
    * caso b
      * caso b1
      * caso b2

    1. caso 1 
    2. caso 2


    e nella documentazione"""
    return osservazioni.columns.tolist()

class ColDescriptor(BaseModel):
    """Descrittore di colonne"""
    column: str
    items: int
    values: Union[bool, List[Union[int, float, str]]]

@app.get('/columns/{column}', tags=["meta"], response_model=ColDescriptor)
async def column(column: str):
    col = osservazioni[column].unique()
    return ColDescriptor(**{
        "column": column,
        "items": col.size,
        "values": False if col.size > 105 else json.loads(json.dumps(col.tolist()).replace('NaN, ',''))
    })

@app.get('/data', tags=["data"])
async def data(h: int= -1):
    if h > 0:
        return json.loads(osservazioni.head(h).to_json(orient='index',default_handler=str))
    return {"head": h}

@app.get('/data.geojson', tags=["data", "geo"])
async def data_geo(w:int = -180, s: int= -90,e:int= 180, n:int= 90):
    if DEBUG:
        import pdb; pdb.set_trace()
    p1 = Point(w,n)
    p2 = Point(e,n)
    p3 = Point(e,s)
    p4 = Point(w,s)

    np1 = (p1.coords.xy[0][0], p1.coords.xy[1][0])
    np2 = (p2.coords.xy[0][0], p2.coords.xy[1][0])
    np3 = (p3.coords.xy[0][0], p3.coords.xy[1][0])
    np4 = (p4.coords.xy[0][0], p4.coords.xy[1][0])

    #bb_polygon = Polygon([np1, np2, np3, np4])
    bb_series = gpd.GeoSeries([p1, p2, p3, p4])
    df2 = gpd.GeoDataFrame(gpd.GeoSeries(bb_series), columns=["geometry"])
    result = geo_osservazioni.sindex.intersection(df2.total_bounds)

    #result = gpd.overlay(df2, geo_osservazioni, how='intersection')
#
    print(result.shape)

    return json.loads(df2.to_json())

#print(osservazioni)
#print(osservazioni.nome_scientifico.unique())

