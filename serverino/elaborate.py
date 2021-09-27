import rasterio

dataset = rasterio.open('AwsData/32TQM,2021-09-02,0/B10.jp2')

roma_1850 = "58950.tif"
dataset_1850 = rasterio.open(roma_1850)

datasets = [dataset, dataset_1850]
for dataset in datasets:
    print(dataset.colorinterp)
    print(dir(dataset))

print(type(dataset.read(1)))
print(dir(dataset_1850.read(1)))