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

class DataItem(BaseModel):
    FID: str
    phylum: str
    class_value: str
    ordo: str
    family: str
    genus: str
    nome_scientifico: str
    unit_id: Optional[int]
    anno: Optional[float]
    lat: float
    lon: float
    geom: str
    usagekey: int
    canonicalname: str
    ds_id: int
    banca_dati: str
    provider: str
    cod_habitat: str
    geometry: Optional[str]

    class Config:
        fields = {'class_value': 'class'}


@app.get('/data', tags=["data"], response_model=List[DataItem])
async def data(h: int= -1):
    if h > 0:
        ret = json.loads(osservazioni.head(h).to_json(orient='index', default_handler=str))
        return list(ret.values())
    return {"head": h}

class pPoint(BaseModel):
    type: str
    coordinates: List[float]

class Feature(BaseModel):
    type: str
    properties: DataItem
    geometry: pPoint

class FeatureCollection(BaseModel):
    type: str
    features: List[Feature]


@app.get('/data.geojson', tags=["data", "geo"], response_model=FeatureCollection)
async def data_geo(w:float = -180, s: float= -90,e:float= 180, n:float= 90):
    if DEBUG:
        import pdb; pdb.set_trace()
    go = geo_osservazioni
    go = go[(go['lat']<n) & (go['lat'] > s) & (go['lon'] > w) & (go['lon'] < e)].sample(10)
    return json.loads(go.to_json())

class dPolygon(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

@app.post('/data.geojson', response_model= FeatureCollection)
async def filter_data(body: str):
    shp = json.loads(body)
    is_valid = dPolygon(**shp)
    poly = shape(shp)
    mask = geo_osservazioni['geometry'].within(poly)
    ret = geo_osservazioni[mask]
    return json.loads(ret.to_json())

#print(osservazioni)
#print(osservazioni.nome_scientifico.unique())

