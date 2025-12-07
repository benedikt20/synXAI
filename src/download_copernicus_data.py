from datetime import datetime, timedelta
from logging import config
import os
from glob import glob
import xarray as xr
from src.make_bot_ds import extract_bottom_features
import shutil
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import copernicusmarine
copernicusmarine.login(username="bfadel", password="Makrill22$", check_credentials_valid=True)


def download_copernicus_data(config, datasets=None, output_file_name=None):
        
    # Config
    #==============================================
    # Coordinates setup
    lon_min = config.get('boundary_box', {}).get('lon_min', -30)
    lon_max = config.get('boundary_box', {}).get('lon_max', -10)
    lat_min = config.get('boundary_box', {}).get('lat_min', 61)
    lat_max = config.get('boundary_box', {}).get('lat_max', 68)
    depth_min = config.get('boundary_box', {}).get('depth_min', 20)
    depth_max = config.get('boundary_box', {}).get('depth_max', 500)
    #future_days = config.get('date_range', {}).get('days_ahead', 10)

    # Paths 
    DATA_DIR = config.get('directories', {}).get('data_dir', 'datafiles')
    TEMP_DIR = config.get('directories', {}).get('temp_dir', 'temporary_download_dir')
    #OUTPUT_FILE_NAME = config.get('directories', {}).get('output_file_name', 'bottom_features.nc')
    OUTPUT_FILE_NAME = output_file_name if output_file_name else config.get('directories', {}).get('output_file_name', 'bottom_features.nc')
    #==============================================



    # Download days
    date_min = config.get('date_range', {}).get('start_date')
    date_max = config.get('date_range', {}).get('end_date')
        
    logger.info(f"Downloading data from {date_min} to {date_max}")

    # Create directories if they don't exist
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


    # Datasets to download
    # datasets = {
    #     "cmems_mod_glo_phy-thetao_anfc_0.083deg_PT6H-i": ["thetao"], # temperature
    #     #"cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i": ["uo", "vo"], # currents 
    #     #"cmems_mod_glo_phy-so_anfc_0.083deg_PT6H-i": ["so"], # salinity
    # }
    if datasets is None:
        raise ValueError("No datasets specified'")


    # check if the dataset is already downloaded and if not, download it
    for dataset_id in datasets:
        if os.path.exists(f"temporary_download_dir/{dataset_id}_lat{lat_min}_{lat_max}_lon{lon_min}_{lon_max}_depths_{date_min}_{date_max}.nc"):
            logger.info(f"Dataset {dataset_id} already downloaded")
            continue
        else:
            logger.info(f"Dataset {dataset_id} not downloaded, downloading...")

            # download each dataset
            #for dataset_id in datasets:
            print(f"Downloading {dataset_id}... with variables {datasets[dataset_id]}")
            dataset = copernicusmarine.subset(
                dataset_id=dataset_id,
                variables=datasets[dataset_id],
                minimum_longitude=lon_min,
                maximum_longitude=lon_max,
                minimum_latitude=lat_min,
                maximum_latitude=lat_max,
                start_datetime=date_min,
                end_datetime=date_max,
                minimum_depth=depth_min,
                maximum_depth=depth_max,
                output_filename = f"{TEMP_DIR}/{dataset_id}_lat{lat_min}_{lat_max}_lon{lon_min}_{lon_max}_depths_{date_min}_{date_max}.nc"
            )

    #pattern = f"{TEMP_DIR}/cmems_mod_glo_phy-*_lat{lat_min}_{lat_max}_lon{lon_min}_{lon_max}_depths_{date_min}_{date_max}.nc"
    pattern = f"{TEMP_DIR}/cmems_mod_glo*_lat{lat_min}_{lat_max}_lon{lon_min}_{lon_max}_depths_{date_min}_{date_max}.nc"
    files_to_merge = sorted(glob(pattern))

    if not files_to_merge:
        print("No files found to merge.")
        #raise FileNotFoundError("Files not found")
        
    # elif len(files_to_merge) == 1:
    #     logger.info(f"Single file found: {files_to_merge[0]}")
    #     merged_ds = xr.open_dataset(files_to_merge[0])
    else:
        logger.info(f"Merging files...")
        merged_ds = xr.open_mfdataset(files_to_merge, combine="by_coords")

    merged_output_path = (
        f"{TEMP_DIR}/copernicus_data.nc"
    )
    # delete file if exists
    if os.path.exists(merged_output_path):
        os.remove(merged_output_path)

    merged_ds.to_netcdf(merged_output_path)
    #merged_ds.close()
    print(f"Merged dataset saved to {merged_output_path}")

    # Download bathymetry if not already downloaded
    if not os.path.exists(f"{DATA_DIR}/bathy.nc"):
        raise FileNotFoundError("Bathy file not found, need to get the GEBCO bathymetry file")

        # copernicusmarine.subset(
        # dataset_id="cmems_mod_glo_phy_anfc_0.083deg_static",
        # dataset_part="bathy",
        # variables=["deptho"],       # ["deptho", "mask"]
        # minimum_longitude=lon_min,
        # maximum_longitude=lon_max,
        # minimum_latitude=lat_min,
        # maximum_latitude=lat_max,
        # output_filename = f"{DATA_DIR}/bathy.nc"
        # )
        # bathy = xr.open_dataset(f"{DATA_DIR}/bathy.nc")
    else:
        bathy = xr.open_dataset(f"{DATA_DIR}/bathy.nc")

    # generate bottom feature dataset using make_bot_ds.py
    bottom_features = extract_bottom_features(merged_ds, bathy)

    if os.path.exists(f"{DATA_DIR}/{OUTPUT_FILE_NAME}"):
        os.remove(f"{DATA_DIR}/{OUTPUT_FILE_NAME}")

    print (f"Saving bottom features to {DATA_DIR}/{OUTPUT_FILE_NAME}")
    bottom_features.to_netcdf(f"{DATA_DIR}/{OUTPUT_FILE_NAME}")
    logger.info(f"Bottom features saved to {DATA_DIR}/{OUTPUT_FILE_NAME}")

    # delete files to merge (raw downloaded files)
    # for file in files_to_merge:
    #     os.remove(file)

    # delete temporary download directory
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        logger.info(f"Temporary directory {TEMP_DIR} deleted.")


if __name__ == "__main__":
    download_copernicus_data()

