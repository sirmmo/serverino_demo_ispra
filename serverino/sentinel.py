from sentinelhub import SHConfig, BBox, CRS, DataCollection, WebFeatureService

config = SHConfig()

config.instance_id = '4b6cd191-7d54-4fee-b33d-598bcc0720c7'
config.sh_client_id = 'cf3a36b2-9a8c-4ca1-b80a-875101582295'
config.sh_client_secret = 'gGR#?}79<<rUlBlH42zh@vK~H@odRzU,CKv3[Cn,'

config.aws_access_key_id = 'AKIA2LAQOYYZOREAMSZ7'
config.aws_secret_access_key = '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'

config.save()

from sentinelhub import SentinelHubCatalog

catalog = SentinelHubCatalog(config=config)

collections = catalog.get_collections()

collections = [collection for collection in collections if not collection['id'].startswith(('byoc', 'batch'))]

bbox = BBox([12.472959,41.907228,12.494974,41.921599], crs=CRS.WGS84)
time_interval = '2021-09-02', '2021-09-20'

search_iterator = catalog.search(
    DataCollection.SENTINEL2_L2A,
    bbox=bbox,
    time=time_interval,
    query={
        "eo:cloud_cover": {
            "lt": 5
        }
    },
    fields={
        "include": [
            "id",
            "properties.datetime",
            "properties.eo:cloud_cover"
        ],
        "exclude": []
    }

)


results = list(search_iterator)
print('Total number of results:', len(results))

print(results)

from sentinelhub import SentinelHubRequest, filter_times, bbox_to_dimensions, \
    MimeType, SentinelHubDownloadClient

import datetime as dt

time_difference = dt.timedelta(hours=1)

all_timestamps = search_iterator.get_timestamps()
unique_acquisitions = filter_times(all_timestamps, time_difference)

print(unique_acquisitions)



false_color_evalscript = """
    //VERSION=3

    function setup() {
        return {
            input: [{
                bands: ["B03", "B04", "B08"]
            }],
            output: {
                bands: 3
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B08, sample.B04, sample.B03];
    }
"""


process_requests = []

for timestamp in unique_acquisitions:
    request = SentinelHubRequest(
        evalscript=false_color_evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(timestamp - time_difference, timestamp + time_difference)
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.PNG)
        ],
        bbox=bbox,
        size=bbox_to_dimensions(bbox, 100),
        config=config
    )
    process_requests.append(request)
#

#client = SentinelHubDownloadClient(config=config)

#download_requests = [request.download_list[0] for request in process_requests]

#data = client.download(download_requests)
#print(type(data))
#print(len(data))
#print(type(data[0]))
#print(data[0].size)
#
#for i,d in enumerate(data):
#    d.as_csv('data_{}.csv', i)


from sentinelhub import AwsTile
from sentinelhub import AwsTileRequest

search_bbox = bbox
search_time_interval = time_interval


wfs_iterator = WebFeatureService(
    search_bbox,
    search_time_interval,
    data_collection=DataCollection.SENTINEL2_L1C,
    maxcc=1.0,
    config=config
)

for tile_info in wfs_iterator:
    print(tile_info)
    
    tile_id = tile_info['properties']['id']
    tile_name, time, aws_index = AwsTile.tile_id_to_tile(tile_id)
    print(tile_id, tile_name, time, aws_index)

    bands = ['B8A', 'B10']
    metafiles = ['tileInfo', 'preview', 'qi/MSK_CLOUDS_B00']
    data_folder = './AwsData'

    request = AwsTileRequest(
        tile=tile_name,
        time=time,
        aws_index=aws_index,
        bands=bands,
        metafiles=metafiles,
        data_folder=data_folder,
        data_collection=DataCollection.SENTINEL2_L1C
    )

    request.save_data()