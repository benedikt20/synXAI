import xarray as xr
import numpy as np

def extract_bottom_features(ds, bathy, output_path=None):
    """
    Extract bottom layer features from oceanographic data.
    
    Parameters:
    - ds: xarray Dataset with oceanographic data
    - bathy: xarray Dataset with bathymetry data (must have 'deptho' variable)
    - output_path: Optional path to save the result
    
    Returns:
    - xarray Dataset with bottom features
    """
    
    # Build a "target depth" per (lat, lon)
    min_resolvable = float(ds.depth.min())
    max_resolvable = float(ds.depth.max())
    # Interpolate bathymetry to the dataset grid to avoid size mismatches
    target_depth = (
        bathy.deptho
        .interp(latitude=ds.latitude, longitude=ds.longitude, method='linear')
        .clip(min=min_resolvable, max=max_resolvable)
        .rename("target_depth")
        .reset_coords(drop=True)
    )

    
    # Check first day to identify problematic points and adjust target_depth
    print("Checking first day to adjust target depths...")
    first_day_var = list(ds.data_vars.values())[0].isel(time=0)

    # Ensure coords exactly match the variable we index into (defensive)
    target_depth = target_depth.assign_coords(
        latitude=first_day_var.latitude, longitude=first_day_var.longitude
    )
    test_result = first_day_var.sel(depth=target_depth.fillna(float(ds.depth.min())), method='pad')

    
    # Find points that result in NaN but have valid surface data
    nan_mask = test_result.isnull()
    surface_valid = ~first_day_var.sel(depth=first_day_var.depth.min()).isnull()
    problematic_points = nan_mask & surface_valid
    
    if problematic_points.any():
        print(f"Adjusting {problematic_points.sum().values} problematic points...")
        valid_data = first_day_var.notnull()
        depth_indices = xr.where(valid_data,
                               xr.DataArray(range(len(first_day_var.depth)), dims='depth'),
                               -1)
        deepest_idx = depth_indices.max('depth').compute()
        deepest_valid_depth = first_day_var.depth.isel(depth=deepest_idx)
        target_depth = target_depth.where(~problematic_points, deepest_valid_depth)
    
    # Remove any time coordinate that may have been added
    if 'time' in target_depth.coords:
        target_depth = target_depth.drop_vars('time')
    
    # Handle land/NaN cells
    shallowest = float(ds.depth.min())
    safe_target_depth = target_depth.fillna(shallowest)
    
    def pick_bottom(da):
        """Return da at deepest layer ≤ target_depth, for every lat/lon."""
        return da.sel(depth=target_depth, method='pad')
    
    print("Processing variables to extract bottom layers...")
    bottom_vars = {f"{name}": pick_bottom(var)              # Variable name (var_bot or just var)
                   for name, var in ds.data_vars.items()}
    bottom_ds = xr.Dataset(bottom_vars)
    
    # Remove the now-redundant depth coord
    bottom_ds = bottom_ds.drop_vars('depth')
    
    if output_path:
        print("Saving to netCDF...")
        bottom_ds.to_netcdf(output_path)
        print(f"Bottom features saved to {output_path}")
    
    return bottom_ds