import os, h5py, yaml, pprint, textwrap
import numpy as np
from PIL import Image as PILImage
from scipy.ndimage import zoom
from datetime import datetime, timezone
from .file_picker import *
from .data_objects import *
from typing import Literal
from collections.abc import Sequence
Numeric = float | int | complex | np.integer | np.floating



class File(h5py.File):
    def __init__(self, path: str = "", mode: Literal["w", "r", "a"] = "r", existsok: bool = False, creator: str = "spmh5", nsid_version: str = "0.0.4", driver = None, libver = None, userblock_size = None, swmr = False, rdcc_nslots = None, rdcc_nbytes = None, rdcc_w0 = None, track_order = None, fs_strategy = None, fs_persist = False, fs_threshold = 1, fs_page_size = None, page_buf_size = None, min_meta_keep = 0, min_raw_keep = 0, locking = None, alignment_threshold = 1, alignment_interval = 1, meta_block_size = None, *, track_times = False, **kwds):
        if not path:
            if mode in {"w", "a"}: path = get_file_path_from_dialog(extensions = ["h5", "hdf5"], io = "save")
            else: path = get_file_path_from_dialog(extensions = ["h5", "hdf5"], io = "load")
        
        if os.path.isfile(path):
            if mode in {"w"} and existsok: print(f"Warning: file {path} already exists. Overwriting")
            if mode in {"w"} and not existsok: raise OSError(f"Error: file {path} already exists. Aborting")
        else:
            if mode in {"r", "a"}: raise IOError(f"Error: file {path} does not exist.")
        
        super().__init__(path, mode, driver, libver, userblock_size, swmr, rdcc_nslots, rdcc_nbytes, rdcc_w0, track_order, fs_strategy, fs_persist, fs_threshold, fs_page_size, page_buf_size, min_meta_keep, min_raw_keep, locking, alignment_threshold, alignment_interval, meta_block_size, track_times = track_times, **kwds)
        
        # Set the default attributes when writing the file
        if mode in {"w"}:
            self.set_creator(creator = creator)
            self.set_iso_timestamp(path)
            self.set_datetime()
            self.set_NSID_tag(nsid_version = nsid_version)
            self.set_NeXus_tag()
            self.create_attributes(attributes = {"filename": os.path.basename(path)})



    # References to old methods
    def create_bare_group(self, name: Any):
        return super().create_group(name)
    
    def create_bare_dataset(self, name: Any, shape: Any | None = None, dtype: Any | None = None, data: Any | None = None, **kwds: Any):
        return super().create_dataset(name, shape, dtype, data, **kwds)



    # Extract/filter/find specific h5py types
    def get_attributes(self, h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None) -> dict:
        if not isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset): return get_attributes(self)
        else: return get_attributes(h5object)

    def get_groups(self, root_or_group: File | h5py.File | h5py.Group | None = None) -> dict:
        if not isinstance(root_or_group, File | h5py.File | h5py.Group): return get_groups(self)
        else: return get_groups(root_or_group)

    def get_datasets(self, root_or_group: File | h5py.File | h5py.Group | None = None) -> dict:
        if not isinstance(root_or_group, File | h5py.File | h5py.Group): return get_datasets(self)
        else: return get_groups(root_or_group)

    def get_items(self, root_or_group: File | h5py.File | h5py.Group | None = None) -> dict:
        if not isinstance(root_or_group, File | h5py.File | h5py.Group): return get_items(self)
        else: return get_items(root_or_group)

    def get_root(self) -> File:
        return self

    def get_NeXus_tag(self, h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None) -> str:
        if not isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset): return get_NeXus_tag(self)
        else: return get_NeXus_tag(h5object)



    # Attributes
    def create_attributes(self, h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, attributes: dict = {}) -> None:
        if not isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset): create_attributes(self, attributes)
        else: create_attributes(h5object, attributes)

    def set_datetime(self, h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, date_convention: Literal["US", "world"] = "US", overwrite: bool = False) -> dict[str, str]:
        if isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset): dt_attrs = set_datetime(h5object, date_convention = date_convention, overwrite = overwrite)
        else: dt_attrs = set_datetime(self, date_convention = date_convention, overwrite = overwrite)
        return dt_attrs

    def set_iso_timestamp(self, path: str = "", h5object: h5py.File | h5py.Group | h5py.Dataset | None = None, overwrite: bool = False) -> dict[str, str]:
        creation_timestamp = os.path.getctime(path)
        creation_datetime = datetime.fromtimestamp(creation_timestamp, tz = timezone.utc)
        datetime_iso_8601 = creation_datetime.isoformat()
        dt_attrs = {"file_time": datetime_iso_8601}
        
        if isinstance(h5object, h5py.File | h5py.Group | h5py.Dataset):
            attributes = get_attributes(h5object)
            if "file_time" in attributes.keys() and not overwrite: return dt_attrs
            else: create_attributes(h5object, dt_attrs)
        return dt_attrs

    def set_creator(self, h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, creator: str = "", overwrite: bool = False) -> dict[str, str]:
        if isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset): creator_attrs = set_creator(h5object, creator, overwrite)
        else: creator_attrs = set_creator(self, creator, overwrite)
        return creator_attrs

    def set_NSID_tag(self, h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, nsid_version: str = "", overwrite: bool = False) -> dict[str, str]:
        if isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset): nsid_attrs = set_NSID_tag(h5object, nsid_version, overwrite)
        else: nsid_attrs = set_NSID_tag(self, nsid_version, overwrite)
        return nsid_attrs

    def set_NeXus_tag(self, h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, NeXus_class: str = "", overwrite: bool = False) -> dict[str, str]:
        if isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset): nsid_attrs = set_NeXus_tag(h5object, NeXus_class, overwrite)
        else: nsid_attrs = set_NeXus_tag(self, "NXroot", overwrite)
        return nsid_attrs



    # Make groups
    def create_group(self, name: str = "", root_or_group: File | h5py.File | h5py.Group | None = None, attributes: dict = {}) -> h5py.Group:
        if isinstance(root_or_group, File | h5py.File | h5py.Group): return create_group(root_or_group, name, attributes)
        else: return create_group(self, name, attributes)

    def get_entry_group(self, name: str = "Measurement_000", verbose: bool = False) -> h5py.Group:
        """Finds the entry group in an HDF5 file, first by searching for the default tag at the root, then by trying to find the NXentry tags in the groups at the root level. If the entry group does not exist, it is created.

        Args:
            root (h5py.File): HDF5 file
            name (str, optional): Name of the entry group: only relevant when creating a new group. Defaults to "Measurement_000".
            verbose (bool, optional): Whether to output messages. Defaults to False.

        Returns:
            h5py.Group: The entry group
        """
        return get_entry_group(self, name, verbose)

    def create_data_group(self, name: str = "", root_or_group: File | h5py.File | h5py.Group | None = None, attributes: dict = {}) -> h5py.Group:
        if isinstance(root_or_group, File | h5py.File | h5py.Group): return create_data_group(root_or_group, name, attributes)
        else: return create_data_group(self, name, attributes)

    def create_instrument(self, name: str = "", long_name: str = "", vendor: str = "", attributes: dict = {}) -> h5py.Group:
        return create_instrument(self, name, long_name, vendor, attributes)



    # General and main datasets
    def create_dataset(self, name: str = "", units: str = "", root_or_group: File | h5py.File | h5py.Group | None = None, attributes: dict = {}, data: np.ndarray | None = None,
                       dtype: np.typing.DTypeLike | None = None, shape: tuple | None = None, resizable_axes: int | np.integer | tuple[int] | list[int] | None = None, maxshape: tuple | int | None = None, **kwargs) -> h5py.Dataset:
        if isinstance(root_or_group, File | h5py.File | h5py.Group): return create_dataset(root_or_group, name, units, attributes, data, dtype, shape, resizable_axes, maxshape)
        else: return create_dataset(self, name, units, attributes, data, dtype, shape, resizable_axes, maxshape)

    def append_values(self, dataset: h5py.Dataset, values: float | int | list | np.ndarray, axis: int = -1) -> None:
        return append_values(dataset, values, axis)

    def create_main_dataset(self, dataset: Dataset | None = None, name: str = "", units: str = "", existsok: bool = True, modality: str = "SPM", make_default: bool = True, attributes: dict = {},
                            data: np.ndarray | None = None, dtype: np.typing.DTypeLike | None = None, shape: tuple | None = None, resizable_axes: int | np.integer | tuple[int] | list[int] | None = None,
                            maxshape: tuple | int | None = None, image_version: str = "1.2", gwyddion_class: str = "IMAGE", verbose: bool = False) -> h5py.Dataset:
        """Create a main dataset
        
        Args:
            dataset (spmh5.Dataset, optional): Dataset object. If provided, use it to set up the ancillary dataset. If not, use the kwargs below.
            name (str, optional): Dataset name. Defaults to "".
            existsok (bool, optional): Allow overwriting. Defaults to True.
            modality (str, optional): Modality tag. Defaults to "SPM".
            units (str, optional): Units. Defaults to "".
            attributes (dict, optional): Custom attributes. Defaults to {}.
            data (np.ndarray | None, optional): Data. Defaults to None.
            make_default (bool, optional): Whether to tag this dataset to be the most important or default dataset (H5Web opens to the default). Defaults to True.
            dtype (np.typing.DTypeLike | None, optional): Data type. Defaults to None.
            shape (tuple | None, optional): Shape of dataset. Defaults to None. Passing shape and maxshape instead of data will trigger chunking.
            resizable_axes (Numeric | Sequence | None, optional): Integer or tuple of integers pointing to which axes may be resized. Defaults to None (static).
            maxshape (tuple | int | None, optional): Maximum shape. Defaults to None.
            verbose (bool, optional): Whether to output details to terminal. Defaults to False.

        Returns:
            h5py.Dataset: The dataset
        """
        return create_main_dataset(self, dataset, name, units, existsok, modality, make_default, attributes, data, dtype, shape, resizable_axes, maxshape, image_version, gwyddion_class, verbose)

    def create_datagrid(self, datagrid: Datagrid) -> tuple[h5py.Dataset, list[h5py.Dataset]]:
        return create_datagrid(self, datagrid)

    def set_default(self, main_dataset: h5py.Dataset):
        return set_default(main_dataset)

    def set_default_slice(self, main_dataset: h5py.Dataset, axes: int | tuple[int] | list[int] | None = None, indices: int | tuple[int] | list[int] | None = None):
        return set_default_slice(main_dataset, axes, indices)

    def find_dataset(self, name: str = "") -> h5py.Dataset:
        entry_group = get_entry_group(self)
        
        # Strict matching
        for group_name, group in get_groups(entry_group).items():
            for dataset_name, dataset in get_datasets(group).items():
                if name.lower() == dataset_name.lower(): return dataset
        
        # Loose matching
        for group_name, group in get_groups(entry_group).items():
            for dataset_name, dataset in get_datasets(group).items():
                if name.lower() in dataset_name.lower(): return dataset
        raise KeyError("Group \"{name}\" not found.")



    # Ancillary / Axis datasets
    def create_ancillary_dataset(self, dataset: Dataset | None = None, name: str = "", units: str = "", existsok: bool = True, attributes: dict = {},
                                 data: np.ndarray | None = None, dtype: np.typing.DTypeLike | None = None, shape: tuple | None = None, verbose: bool = False) -> h5py.Dataset:
        """Create a dataset that will become an axis to a main dataset. It is stored by default in the Ancillary Group, and Softlinked to the main dataset group upon calling attach_axis. Ancillary datasets are 1D and resizable by default.

        Args:
            dataset (spmh5.Dataset, optional): Dataset object. If provided, use it to set up the ancillary dataset. If not, use the kwargs below.
            name (str, optional): Dataset name. Defaults to "".
            existsok (bool, optional): Allow overwriting. Defaults to True.
            units (str, optional): Units. Defaults to "".
            attributes (dict, optional): Custom attributes. Defaults to {}.
            data (np.ndarray | None, optional): Data. Defaults to None.
            dtype (np.typing.DTypeLike | None, optional): Data type. Defaults to None.
            shape (tuple | None, optional): Shape of dataset. Defaults to None. Passing shape and maxshape instead of data will trigger chunking.
            maxshape (tuple | int | None, optional): Maximum shape. Defaults to None.
            verbose (bool, optional): Whether to output details to terminal. Defaults to False.

        Returns:
            h5py.Dataset: The dataset
        """
        return create_ancillary_dataset(self, dataset, name, units, existsok, attributes, data, dtype, shape, verbose)

    def attach_axis(self, main_dataset: h5py.Dataset, ancillary_dataset: h5py.Dataset, axis: int = 0) -> None:
        return attach_axis(main_dataset, ancillary_dataset, axis)

    def create_linear_axis(self, main_dataset: h5py.Dataset, axis: int = 0, name: str = "", limits: Sequence = (0, 1), units: str = "", existsok: bool = True, attributes: dict = {}, include_boundary: bool = False, verbose: bool = False) -> h5py.Dataset:
        return create_linear_axis(main_dataset, axis, name, limits, units, existsok, attributes, include_boundary, verbose)

    def create_axes_from_frame(self, main_dataset: h5py.Dataset, frame: CoordinateFrame, names: list = ["x", "y", "z", "a"], include_boundaries: bool | list[bool] = False) -> list[h5py.Dataset]:
        return create_axes_from_frame(main_dataset, frame, names, include_boundaries)

    def update_axis(self, ancillary_dataset: h5py.Dataset) -> None:
        return update_axis(ancillary_dataset)



    # Thumbnail
    def calculate_thumbnail(self, main_dataset: h5py.Dataset | None = None, axes: int | tuple[int] | list[int] | None = None, indices: int | tuple[int] | list[int] | None = None, thumbnail_size: int = 256) -> np.ndarray:
        return calculate_thumbnail(self, main_dataset, axes, indices, thumbnail_size)

    def set_thumbnail(self, main_dataset: h5py.Dataset | None = None, axes: int | tuple[int] | list[int] | None = None, indices: int | tuple[int] | list[int] | None = None, thumbnail_size: int = 256) -> tuple[h5py.Group, h5py.Dataset]:
        return set_thumbnail(self, main_dataset, axes, indices, thumbnail_size)

    def get_thumbnail(self) -> np.ndarray:
        return get_thumbnail(self)



# Standalone functions: pass the h5 object or file root as an argument when using these
# File reading
def get_file_dict(root: File | h5py.File, extract_datasets: bool = False) -> dict[str, dict[str, dict[str, object]]]:
    """
    Generates a nested dict describing the file, sorted by object types.
    The top layer describes the object types, with keys \"main_datasets\", \"axis_datasets\", \"other_datasets\", \"groups\" and \"instruments\".
    The second layer are the paths of the individual objects belonging to that type.
    The third layer is the data for that individual object.
    

    Args:
        root (h5py.File): Reference to a HDF5 file.
        extract_datasets (bool, False): Whether to explicitly extract datasets and store them as Dataset objects.

    Returns:
        dict: Nested dictionary.
    """
    output_dict: dict[str, dict[str, dict[str, object]]] = {"groups": {}, "main_datasets": {}, "axis_datasets": {}, "other_datasets": {}, "instruments": {}}
    
    group_dict: dict[str, dict[str, object]] = {}
    instruments_dict: dict[str, dict[str, object]] = {}
    main_datasets_dict: dict[str, dict[str, object]] = {}
    axis_datasets_dict: dict[str, dict[str, object]] = {}
    other_datasets_dict: dict[str, dict[str, object]] = {}
    
    root_data: dict[str, object] = {}
    entry_group_data: dict[str, object] = {}
    ancillary_group_data: dict[str, object] = {}
    
    axis_dataset_names: dict[str, str] = {} # Convenience dict for finding the path from a name later



    # Parse the root
    root_attrs = get_attributes(root)
    root_groups = get_groups(root)
    root_data.update({"path": "./", "name": "root", "attrs": root_attrs, "child_groups": [group_name for group_name in root_groups.keys()], "object_type": "root"})
    group_dict.update({"./": root_data})
    output_dict["groups"].update(group_dict)



    # Find and then parse the entry group
    entry_path = root_attrs.get("default", "")
    if not entry_path: # No default found
        if len(root_groups) < 1: # No groups at all
            print("No groups found in this file!")
            return output_dict
        else: # There are groups
            for group_name, group in root_groups.items(): # Parse the individual groups for NX_class keys
                group_attrs = get_attributes(group)
                str_values = [value for value in group_attrs.values() if isinstance(value, str)]
                
                if "NXentry" in str_values:
                    entry_path = group_name # NXentry key found
                    break
            if not entry_path: # NXentry not found
                if len(root_groups) == 1: # Only a single group present
                    print("Warning! No entry group was found in this HDF5 file.\nPlease tag the entry group by adding the attribute \"default\": [group_name] to the root attributes.\nI did however, find a single group under the root and I will assume that it is the entry group.")
                    entry_path = list(root_groups.keys())[0]
                else: # Multiple groups but no tagged NXentry. Ambiguous
                    print("This file contains multiple groups, but no group is tagged as the entry group. Aborting file read")
                    return output_dict
    
    entry_group = root[entry_path]
    assert isinstance(entry_group, h5py.Group)
    entry_group_attrs = get_attributes(entry_group)
    entry_subgroups = get_groups(entry_group)
    entry_datasets = get_datasets(entry_group)
    
    entry_group_data.update({"path": entry_path, "attrs": entry_group_attrs, "parent_group": "./", "child_groups": [entry_path + "/" + group_name for group_name in entry_subgroups.keys()], "object_type": "group"})
    if len(entry_datasets) > 0: entry_group_data.update({"datasets": [dataset_name for dataset_name in entry_datasets.keys()]})
    group_dict.update({entry_path: entry_group_data})
    output_dict["groups"].update(group_dict)



    # Parse the ancillary group
    if "Ancillary" in entry_subgroups.keys():
        ancillary_group = entry_group["Ancillary"]
        ancillary_path = entry_path + "/Ancillary"
        assert isinstance(ancillary_group, h5py.Group)
        ancillary_group_attrs = get_attributes(ancillary_group)
        axis_datasets = get_datasets(ancillary_group)
        
        ancillary_group_data.update({"path": ancillary_path, "attrs": ancillary_group_attrs, "parent_group": entry_path, "object_type": "group", "datasets": [ancillary_path + "/" + dataset_name for dataset_name in axis_datasets.keys()]})
        group_dict.update({ancillary_path: ancillary_group_data})
        
        for dataset_name, dataset in axis_datasets.items():
            dset_attrs = get_attributes(dataset)
            
            shape = list(getattr(dataset, "shape", []))
            [dset_attrs.pop(key, None) for key in ["REFERENCE_LIST", "DIMENSION_LIST"]]
            units = dset_attrs.get("units", "")
            dset_path = ancillary_path + "/" + dataset_name
            
            axis_datasets_dict.update({dset_path: {"path": dset_path, "name": dataset_name, "parent_group": ancillary_path, "object_type": "axis dataset", "units": units, "attrs": dset_attrs, "shape": shape}})
            axis_dataset_names.update({dataset_name: dset_path}) # Convenience dict for finding the path from a name later
        
        output_dict["groups"].update(group_dict)
        output_dict["axis_datasets"].update(axis_datasets_dict)



    # Parse the remaining subgroups in the entry group (assumed to hold the main datasets)
    for group_name, group in entry_subgroups.items():
        if group_name.lower() == "ancillary": continue
        
        group_path = entry_path + "/" + group_name
        group_attrs = get_attributes(group)
        group_subgroups = get_groups(group)
        group_datasets = get_datasets(group)
        str_values = [value for value in group_attrs.values() if isinstance(value, str)]
        
        if "NXinstrument" in str_values: # The group is an instrument
            instruments_dict.update({group_path: {"path": group_path, "name": group_name, "parent_group": entry_path, "attrs": group_attrs, "object_type": "instrument group"}})
            if len(group_datasets) > 0: instruments_dict[group_path].update({"datasets": [group_path + "/" + dataset_name for dataset_name in group_datasets.keys()]})
            if len(group_subgroups) > 0: instruments_dict[group_path].update({"child_groups": [group_path + "/" + group_name for group_name in group_subgroups.keys()]})
            output_dict["instruments"].update(instruments_dict)
            continue    
        
        group_dict.update({group_path: {"path": group_path, "attrs": group_attrs, "parent_group": entry_path, "object_type": "group", "datasets": [group_path + "/" + dataset_name for dataset_name in group_datasets.keys()]}})
        output_dict["groups"].update(group_dict)
        
        if len(group_datasets) < 1: continue # The group has no dataset
        
        for dataset_name, dataset in group_datasets.items():
            dset_attrs = get_attributes(dataset)
            if dset_attrs.get("NX_class", "") == "NXaxis": continue # This tag signifies the dataset is an axis dataset
            
            shape = list(getattr(dataset, "shape", []))
            [dset_attrs.pop(key, None) for key in ["REFERENCE_LIST", "DIMENSION_LIST"]]
            
            cleaned_attrs = {}
            for key, value in dset_attrs.items():
                if isinstance(value, Sequence) and not isinstance(value, str): cleaned_attrs.update({key: list(value)})
                elif isinstance(value, int | np.integer): cleaned_attrs.update({key: int(value)}) # type: ignore
                elif isinstance(value, Numeric): cleaned_attrs.update({key: float(value)}) # type: ignore
                else: cleaned_attrs.update({key: value})
            
            slice_axes = [int(value) for value in cleaned_attrs.get("default_slice_axes", ())]
            slice_indices = [int(value) for value in cleaned_attrs.get("default_slice_indices", ())]
            
            axes = list(group_attrs.get("axes", [])) # Substitute paths for names of the axis datasets
            for axis_index, axis_name in enumerate(axes):
                axis_path = axis_dataset_names.get(axis_name, axis_name)
                axes[axis_index] = axis_path
            
            units = dset_attrs.get("units", "")
            dset_path = group_path + "/" + dataset_name
            
            main_datasets_dict.update({dset_path: {"path": dset_path, "name": dataset_name, "parent_group": group_path, "object_type": "main dataset", "axes": axes, "units": units, "attrs": cleaned_attrs, "shape": shape, "slice_indices": slice_indices, "slice_axes": slice_axes}})
            output_dict["main_datasets"].update(main_datasets_dict)



    # Parse the remaining groups at the root level
    for group_name, group in root_groups.items():
        if group == entry_group: continue
        
        group_path = group_name
        group_attrs = get_attributes(group)
        group_subgroups = get_groups(group)
        group_datasets = get_datasets(group)
        str_values = [value for value in group_attrs.values() if isinstance(value, str)]
        
        if "NXinstrument" in str_values: # The group is an instrument
            instruments_dict.update({group_path: {"path": group_path, "name": group_name, "parent_group": "./", "attrs": group_attrs, "object_type": "instrument group"}})
            if len(group_datasets) > 0: instruments_dict[group_path].update({"datasets": [group_path + "/" + dataset_name for dataset_name in group_datasets.keys()]})
            if len(group_subgroups) > 0: instruments_dict[group_path].update({"child_groups": [group_path + "/" + group_name for group_name in group_subgroups.keys()]})
            output_dict["instruments"].update(instruments_dict)
            continue    
        
        group_dict.update({group_path: {"path": group_path, "attrs": group_attrs, "parent_group": entry_path, "object_type": "group", "datasets": [group_path + "/" + dataset_name for dataset_name in group_datasets.keys()]}})
        output_dict["groups"].update(group_dict)
        
        if len(group_datasets) < 1: continue # The group has no dataset
        
        for dataset_name, dataset in group_datasets.items():
            dset_attrs = get_attributes(dataset)
            shape = list(getattr(dataset, "shape", []))
            [dset_attrs.pop(key, None) for key in ["REFERENCE_LIST", "DIMENSION_LIST"]]
            if dset_attrs.get("NX_class", "") == "NXaxis": continue # This tag signifies the dataset is an axis dataset
            
            cleaned_attrs = {}
            for key, value in dset_attrs.items():
                if isinstance(value, Sequence) and not isinstance(value, str): cleaned_attrs.update({key: list(value)})
                elif isinstance(value, int | np.integer): cleaned_attrs.update({key: int(value)}) # type: ignore
                elif isinstance(value, Numeric): cleaned_attrs.update({key: float(value)}) # type: ignore
            
            axes = list(group_attrs.get("axes", [])) # Substitute paths for names of the axis datasets
            for axis_index, axis_name in enumerate(axes):
                axis_path = axis_dataset_names.get(axis_name, axis_name)
                axes[axis_index] = axis_path
            
            units = dset_attrs.get("units", "")
            dset_path = group_path + "/" + dataset_name
            
            other_datasets_dict.update({dset_path: {"path": dset_path, "name": dataset_name, "parent_group": group_path, "object_type": "main dataset", "axes": axes, "units": units, "attrs": cleaned_attrs, "shape": shape}})
            output_dict["other_datasets"].update(other_datasets_dict)

    if not extract_datasets: return output_dict

    
    
    # Extract the datasets to spmh5 Dataset object if desired
    for index, target in enumerate([axis_datasets_dict, main_datasets_dict, other_datasets_dict]):
        for dataset_path, dataset in target.items():
            try:
                dataset_data = root[dataset_path][:] # type: ignore
                dataset_name = dataset.get("name", "")
                dataset_units = dataset.get("units", "")
                dataset_attrs = dataset.get("attrs", {})
                slice_axes = dataset.get("slice_axes")
                slice_indices = dataset.get("slice_indices")
                
                if isinstance(dataset_data, np.ndarray) and isinstance(dataset_attrs, dict) and isinstance(dataset_units, str) and isinstance(dataset_name, str):
                    dataset_object = Dataset(name = dataset_name, data = dataset_data, attrs = dataset_attrs, units = dataset_units, slice_axes = slice_axes, slice_indices = slice_indices)
                    if index == 0: axis_datasets_dict[dataset_path].update({"dataset_object": dataset_object})
                    if index == 1: main_datasets_dict[dataset_path].update({"dataset_object": dataset_object})
                    if index == 2: other_datasets_dict[dataset_path].update({"dataset_object": dataset_object})
                else:
                    print(f"Warning: Could not convert dataset {dataset_path} to an SPMH5 dataset")
            except:
                raise Exception(f"Failed to read data from HDF5 file at path {dataset_path}")
    return output_dict

def get_data_grids(root: File | h5py.File) -> tuple[dict[str, dict[str, dict[str, object]]], list[Datagrid]]:
    """Reads the file, extracts the datasets and constructs Datagrid objects from them. The datagrids are returned alongside the nested file dictionary (see get_file_dict)
    """
    output = get_file_dict(root, extract_datasets = True)
    main_datasets = output["main_datasets"]
    axis_datasets = output["axis_datasets"]
    groups = output["groups"]
    
    datagrids = []
    for main_dataset_path, main_dataset in main_datasets.items():
        main_object = main_dataset.get("dataset_object")
        if not isinstance(main_object, Dataset): break
        
        parent_group_path = main_dataset.get("parent_group", "")
        if not isinstance(parent_group_path, str) or not parent_group_path in groups.keys():
            print(f"Warning: Could not read the parent group of a dataset at {parent_group_path}.")
            parent_group_attrs = {}
        else:
            parent_group = groups[parent_group_path]
            parent_group_attrs = parent_group.get("attrs", {})
            assert isinstance(parent_group_attrs, dict)
        
        axes = main_dataset.get("axes", [])
        if not isinstance(axes, list) or len(axes) < 1: continue
        
        axis_objects = []
        for dim, axis in enumerate(axes):
            if not axis in axis_datasets.keys():
                print(f"Warning: Failed to find axis dataset {axis}")
                continue
            
            axis_dataset = axis_datasets[axis]
            axis_object = axis_dataset.get("dataset_object")
            if isinstance(axis_object, Dataset): axis_objects.append(axis_object)
        
        datagrids.append(Datagrid(dataset = main_object, axes = axis_objects, attrs = parent_group_attrs))
    return output, datagrids

def get_file(file_path: str = ""):
    return Datacollection.from_file(file_path)



# Extract/filter/find specific h5py types
def get_attributes(h5object: File | h5py.File | h5py.Group | h5py.Dataset) -> dict:
    return {key: value for key, value in h5object.attrs.items()}

def get_groups(root_or_group: File | h5py.File | h5py.Group) -> dict:
    return {key: value for key, value in root_or_group.items() if isinstance(value, h5py.Group)}

def get_datasets(root_or_group: File | h5py.File | h5py.Group) -> dict:
    return {key: value for key, value in root_or_group.items() if isinstance(value, h5py.Dataset)}

def get_items(root_or_group: File | h5py.File | h5py.Group) -> dict:
    return {key: value for key, value in root_or_group.items()}

def get_root(h5object: File | h5py.Group | h5py.Dataset | h5py.File) -> h5py.Group:
    try:
        if isinstance(h5object, h5py.File): return h5object
        possible_root = h5object
        
        for _ in range(6):
            if possible_root.name == '/':
                assert isinstance(possible_root, h5py.Group)
                return possible_root
            possible_root = possible_root.parent
        raise Exception(f"Could not locate the HDF5 file root from object {h5object}")
    except Exception as e:
        raise Exception(f"Problem finding the HDF5 file root: {e}")

def get_NeXus_tag(h5object: File | h5py.File | h5py.Group | h5py.Dataset) -> str:
    attrs = get_attributes(h5object)
    tag = attrs.get("NX_class", "")
    return tag



# Attributes
def create_attributes(h5object: File | h5py.File | h5py.Group | h5py.Dataset, attributes: dict = {}) -> None:
    for key, value in attributes.items():
        try:
            if isinstance(value, str): h5object.attrs.create(key, value, dtype = h5py.string_dtype(encoding = "utf-8"))
            else: h5object.attrs[key] = value
        except: pass
    return

def set_datetime(h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, date_convention: Literal["US", "world"] = "US", overwrite: bool = False) -> dict[str, str]:
    dt = datetime.now()
    date_str = dt.strftime(f"%m/%d/%Y (US)") if date_convention == "US" else dt.strftime(f"%d/%m/%Y (world)")
    time_str = dt.strftime(f"%H:%M:%S")
    dt_attrs = {"creation_date": date_str, "creation_time": time_str}
    
    if isinstance(h5object, h5py.File | h5py.Group | h5py.Dataset):
        attributes = get_attributes(h5object)
        if "creation_date" in attributes.keys() and not overwrite: return dt_attrs
        else: create_attributes(h5object, dt_attrs)
    return dt_attrs

def set_iso_timestamp(path: str = "", h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, overwrite: bool = False) -> dict[str, str]:
    creation_timestamp = os.path.getctime(path)
    creation_datetime = datetime.fromtimestamp(creation_timestamp, tz = timezone.utc)
    datetime_iso_8601 = creation_datetime.isoformat()
    dt_attrs = {"file_time": datetime_iso_8601}
    
    if isinstance(h5object, h5py.File | h5py.Group | h5py.Dataset):
        attributes = get_attributes(h5object)
        if "file_time" in attributes.keys() and not overwrite: return dt_attrs
        else: create_attributes(h5object, dt_attrs)
    return dt_attrs

def set_creator(h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, creator: str = "", overwrite: bool = False) -> dict[str, str]:
    creator_attr = {"creator": creator}
    if creator and isinstance(h5object, File | h5py.File | h5py.Group | h5py.Dataset):
        attributes = get_attributes(h5object)
        if "creator" in attributes.keys() and not overwrite: return creator_attr
        else: create_attributes(h5object, creator_attr)
    return creator_attr

def set_NSID_tag(h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, nsid_version: str = "", overwrite: bool = False) -> dict[str, str]:
    attributes = {"data_model": "NSID", "version": nsid_version, "nsid_version": nsid_version}
    if nsid_version and isinstance(h5object, h5py.File | h5py.Group | h5py.Dataset):
        attributes = get_attributes(h5object)
        if "creator" in attributes.keys() and not overwrite: return attributes
        else: create_attributes(h5object, attributes)
    return attributes

def set_NeXus_tag(h5object: File | h5py.File | h5py.Group | h5py.Dataset | None = None, NeXus_class: str = "", overwrite: bool = False) -> dict[str, str]:    
    if not NeXus_class: return {}
    
    if not NeXus_class.startswith("NX"): NeXus_class = "NX" + NeXus_class
    NXattribute = {"NX_class": NeXus_class}
    if isinstance(h5object, h5py.File | h5py.Group | h5py.Dataset):
        attributes = get_attributes(h5object)
        if "NX_class" in attributes.keys() and not overwrite: return attributes
        else: create_attributes(h5object, NXattribute)
    return attributes



# Make groups
def create_group(root_or_group: File | h5py.File | h5py.Group, name: str = "", attributes: dict = {}) -> h5py.Group:
    try:
        if isinstance(root_or_group, File): new_group = root_or_group.create_bare_group(name)
        else: new_group = root_or_group.create_group(name)
        create_attributes(new_group, attributes)
        return new_group
    except:
        raise Exception(f"Error encountered while attempting to create a new h5py group called {name} under {root_or_group}")

def get_entry_group(root: File | h5py.File, name: str = "Measurement_000", verbose: bool = False) -> h5py.Group:
    """Finds the entry group in an HDF5 file, first by searching for the default tag at the root, then by trying to find the NXentry tags in the groups at the root level. If the entry group does not exist, it is created.

    Args:
        root (h5py.File): HDF5 file
        name (str, optional): Name of the entry group: only relevant when creating a new group. Defaults to "Measurement_000".
        verbose (bool, optional): Whether to output messages. Defaults to False.

    Returns:
        h5py.Group: The entry group
    """
    try:
        root_attributes = get_attributes(root)
        root_groups = get_groups(root)
        
        if "default" in root_attributes.keys(): # Cases where the root has the default attribute that is supposed to point to an entry group
            entry_group_name = root_attributes["default"]
            
            if verbose: print(f"Entry group {entry_group_name} was found from the 'default' tag at the root.")
            if entry_group_name in root_groups.keys(): # Case 1: The default attribute in the root points to a valid entry group
                entry_group = root_groups[entry_group_name]
                if verbose: print(f"Entry group is valid ({entry_group = }).")
                set_NeXus_tag(entry_group, "entry")
                return entry_group
            else:
                if verbose: print(f"Entry group is invalid.")
        
        for group_name, group in root_groups.items():
            group_attrs = get_attributes(group)
            group_class = group_attrs.get("NX_class", "")
            if group_class == "NXentry":
                entry_group = group
                if verbose: print(f"Entry group {group_name} was found from its NX_class tag.")
                create_attributes(root, {"default": group_name})
                if verbose: print(f"The 'default' tag was added to the root to point to the entry group.")
                return entry_group

        if verbose: print(f"No valid entry group was found. Creating a new entry group")
        create_attributes(root, {"default": name})
        entry_group = create_group(root, name)
        set_NeXus_tag(entry_group, "entry")        
        return entry_group
    
    except Exception as e:
        raise Exception(f"Error encountered while finding or creating an entry group: {e}")

def create_data_group(root_or_group: File | h5py.File | h5py.Group, name: str = "", attributes: dict = {}) -> h5py.Group:
    try:
        new_group = create_group(root_or_group, name, attributes = attributes)
        set_NeXus_tag(new_group, "data")
        return new_group
    except:
        raise Exception(f"Error encountered while attempting to create a new h5py group called {name} under {root_or_group}")

def create_instrument(root: File | h5py.File, name: str = "", long_name: str = "", vendor: str = "", attributes: dict = {}) -> h5py.Group:
    try:
        if vendor: attributes.update({"vendor": vendor})
        if long_name: attributes.update({"long_name": long_name})
        
        instrument_group = create_group(root, name, attributes = attributes)
        set_NeXus_tag(instrument_group, "instrument")
        return instrument_group
    except Exception as e:
        raise Exception(f"Error encountered while attempting to create a new h5py group called {name} under {root}: {e}")



# General and Main datasets
def create_dataset(root_or_group: File | h5py.File | h5py.Group, name: str = "", units: str = "", attributes: dict = {}, data: np.ndarray | None = None,
                   dtype: np.typing.DTypeLike | None = None, shape: tuple | None = None, resizable_axes: int | np.integer | tuple[int] | list[int] | None = None, maxshape: tuple | int | None = None, **kwargs) -> h5py.Dataset:
    try:
        if dtype is None and isinstance(data, np.ndarray): parsed_dtype = data.dtype
        else: parsed_dtype = np.dtype(dtype)
        
        match parsed_dtype.kind:
            case "U":
                char_len = parsed_dtype.itemsize // 4
                target_dtype = h5py.string_dtype(encoding = "utf-8", length = char_len if char_len > 0 else None)
            case "S" | "O":
                target_dtype = h5py.string_dtype(encoding = "utf-8")
            case "i" | "u" | "f" | "b" | "c":
                target_dtype = parsed_dtype
            case _:
                raise TypeError(f"Unsupported data type family for h5py: {parsed_dtype}")
        
        if isinstance(data, np.ndarray): # Data is passed explicitly. Resizable axes may be provided instead of maxshape for easier declaration.
            shape = data.shape
            
            # Check if resizable axes are provided
            if isinstance(resizable_axes, int | np.integer): resizable_axes = (int(resizable_axes),)
            if isinstance(resizable_axes, Sequence):
                new_maxshape = []
                for dim, axis_length in enumerate(shape):
                    new_maxshape.append(None) if dim in resizable_axes else new_maxshape.append(axis_length)
                maxshape = tuple(new_maxshape)            
            
            if parsed_dtype.kind == "U":
                if isinstance(maxshape, tuple):
                    if isinstance(root_or_group, File): dataset = root_or_group.create_bare_dataset(name, shape = shape, dtype = target_dtype, chunks = True, maxshape = maxshape, **kwargs)
                    else: dataset = root_or_group.create_dataset(name, shape = shape, dtype = target_dtype, chunks = True, maxshape = maxshape, **kwargs)
                else:
                    if isinstance(root_or_group, File): dataset = root_or_group.create_bare_dataset(name, shape = shape, dtype = target_dtype, **kwargs)
                    dataset = root_or_group.create_dataset(name, shape = shape, dtype = target_dtype, **kwargs)
                dataset[...] = data.astype("O")
            else:
                if isinstance(maxshape, tuple):
                    if isinstance(root_or_group, File): dataset = root_or_group.create_bare_dataset(name, data = data, dtype = target_dtype, chunks = True, maxshape = maxshape, **kwargs)
                    else: dataset = root_or_group.create_dataset(name, data = data, dtype = target_dtype, chunks = True, maxshape = maxshape, **kwargs)
                else:
                    if isinstance(root_or_group, File): dataset = root_or_group.create_bare_dataset(name, data = data, dtype = target_dtype, **kwargs)
                    else: dataset = root_or_group.create_dataset(name, data = data, dtype = target_dtype, **kwargs)
        else: # No data is passed, but a shape is provided. Since there is no data to infer a shape from, maxshape must be provided
            if isinstance(root_or_group, File): dataset = root_or_group.create_bare_dataset(name, dtype = target_dtype, shape = shape, chunks = True, maxshape = maxshape, *kwargs)
            else: dataset = root_or_group.create_dataset(name, dtype = target_dtype, shape = shape, chunks = True, maxshape = maxshape, *kwargs)
        
        dimension_type, quantity = infer_quantity_from_units(units)
        attributes.update({"title": name, "long_name": name, "units": units, "dimension_type": dimension_type, "quantity": quantity})
        create_attributes(dataset, attributes)
        return dataset
    except Exception as e:
        raise Exception(f"Error encountered while attempting to create a new h5py dataset called {name} under {root_or_group}: {e}")

def append_values(dataset: h5py.Dataset, values: float | int | list | np.ndarray, axis: int = -1) -> None:
    try:
        if isinstance(values, float | int): values = [values]
        if isinstance(values, list): values = np.array(values)
        
        dset_shape = dataset.shape
        if not axis in range(dataset.ndim):
            resizable_axes = np.where(np.array(dataset.maxshape) == None)[0]
            axis = resizable_axes[0]
        
        values_shape = values.shape
        
        axis_length = dset_shape[axis]
        values_length = values_shape[axis]
        new_axis_length = axis_length + values_length
        
        dataset.resize(new_axis_length, axis = axis)
        match axis:
            case 0: dataset[axis_length:] = values
            case 1: dataset[:, axis_length:] = values
            case 2: dataset[:, :, axis_length:] = values
            case _: raise Exception(f"Unsupported axis {axis}")
        
        dset_attrs = get_attributes(dataset)
        if dset_attrs.get("NX_class") == "NXaxis": update_axis(dataset)
        
    except Exception as e:
        try:
            raise Exception(f"Failed to add a data chunk of shape {values_shape} to a dataset of shape {dset_shape} along axis {axis}: {e}") # type: ignore
        except:
            raise Exception(f"Failed to add a data chunk {values} to dataset {dataset} along axis {axis}: {e}")
    return

def create_main_dataset(root: File | h5py.File, dataset: Dataset | None = None, name: str = "", units: str = "", existsok: bool = True, modality: str = "SPM", make_default: bool = True, attributes: dict = {},
                        data: np.ndarray | None = None, dtype: np.typing.DTypeLike | None = None, shape: tuple | None = None, resizable_axes: int | np.integer | tuple[int] | list[int] | None = None,
                        maxshape: tuple | int | None = None, image_version: str = "1.2", gwyddion_class: str = "IMAGE", NeXus_compliant: bool = True, nsid_compliant: bool = True,
                        default_slice_axes: int | tuple[int] | list[int] | None = None, default_slice_indices: int | tuple[int] | list[int] | None = None, verbose: bool = False) -> h5py.Dataset:
    """Create a main dataset
    
    Args:
        root (h5py.File): Root.
        dataset (spmh5.Dataset, optional): Dataset object. If provided, use it to set up the ancillary dataset. If not, use the kwargs below.
        name (str, optional): Dataset name. Defaults to "".
        existsok (bool, optional): Allow overwriting. Defaults to True.
        modality (str, optional): Modality tag. Defaults to "SPM".
        units (str, optional): Units. Defaults to "".
        attributes (dict, optional): Custom attributes. Defaults to {}.
        data (np.ndarray | None, optional): Data. Defaults to None.
        make_default (bool, optional): Whether to tag this dataset to be the most important or default dataset (H5Web opens to the default). Defaults to True.
        dtype (np.typing.DTypeLike | None, optional): Data type. Defaults to None.
        shape (tuple | None, optional): Shape of dataset. Defaults to None. Passing shape and maxshape instead of data will trigger chunking.
        resizable_axes (Numeric | Sequence | None, optional): Integer or tuple of integers pointing to which axes may be resized. Defaults to None (static).
        maxshape (tuple | int | None, optional): Maximum shape. Defaults to None.
        verbose (bool, optional): Whether to output details to terminal. Defaults to False.

    Returns:
        h5py.Dataset: The dataset
    """
    try:
        # Find or create the entry group
        entry_group = get_entry_group(root, name = "Measurement_000", verbose = verbose)
        entry_subgroups = get_groups(entry_group)
        
        # If an SPMH5 Dataset is provided explicitly, use the values attached to it to create the h5py dataset
        if isinstance(dataset, Dataset):
            name = dataset.name
            data = dataset.data
            shape = dataset.shape
            units = dataset.units
            ds_attrs = dataset.attrs
            resizable_axes = dataset.resizable_axes
            maxshape = dataset.maxshape
            dtype = dataset.dtype
            
            default_slice_axes = dataset.slice_axes
            default_slice_indices = dataset.slice_indices
            
            attributes.update(ds_attrs)
        
        if name in entry_subgroups.keys():
            if existsok:
                print(f"Warning: A dataset with the same name ({name}) was already found in this HDF5 file. Overwriting.")
                data_group = entry_subgroups[name]
                del(data_group[name])
            else:
                raise Exception(f"Error: A dataset with the same name ({name}) was already found in this HDF5 file. Aborting.")
        else:
            data_group_attrs = {"signal": name, "units": units}
            data_group = create_group(entry_group, name, attributes = data_group_attrs)
            if NeXus_compliant: set_NeXus_tag(data_group, "data")
        
        data_type = "2D_image"
        if isinstance(data, np.ndarray): rank = data.ndim
        elif isinstance(shape, tuple): rank = len(shape)
        else: raise Exception("Neither data nor shape were provided when attempting to create a dataset")
        
        if rank > 2: data_type = "image_stack"
        elif rank < 2: data_type = "graph"
        
        # Create the dataset attributes
        root_attrs = get_attributes(root)
        nsid_version = root_attrs.get("nsid_version", "0.0.4")
        dset_attributes = {"units": units, "data_type": data_type, "modality": modality} | attributes
        if nsid_compliant: dset_attributes.update({"CLASS": gwyddion_class, "IMAGE_VERSION": image_version, "nsid_version": nsid_version})
        
        
        
        # Create the dataset
        if isinstance(data, np.ndarray): # Data is passed explicitly
            dataset_out = create_dataset(data_group, name, data = data, resizable_axes = resizable_axes, dtype = dtype, units = units, attributes = dset_attributes)
        elif isinstance(shape, tuple): # The dataset is instantiated with a certain shape            
            dataset_out = create_dataset(data_group, name, shape = shape, maxshape = maxshape, dtype = dtype, units = units, attributes = dset_attributes)
        else:
            raise Exception("Neither data nor shape were provided when attempting to create a dataset")

        set_default_slice(dataset_out, default_slice_axes, default_slice_indices)
        if make_default: set_default(dataset_out)
        
        return dataset_out
    
    except Exception as e:
        raise Exception(f"Error encountered while attempting to create a new h5py dataset called {name}: {e}")

def create_datagrid(root: File | h5py.File, datagrid: Datagrid) -> tuple[h5py.Dataset, list[h5py.Dataset]]:
    axis_datasets = []    
    
    main_ds = create_main_dataset(root, dataset = datagrid.dataset)
    for axis_index, axis_ds in enumerate(datagrid.axes):
        axis_ds_out = create_ancillary_dataset(root, dataset = axis_ds)
        attach_axis(main_ds, axis_ds_out, axis_index)
        axis_datasets.append(axis_ds_out)
    
    entry_group = get_entry_group(root)
    create_attributes(entry_group, datagrid.attrs)
    return main_ds, axis_datasets

def set_default(main_dataset: h5py.Dataset) -> None:
    measurement_group = main_dataset.parent
    entry_group = measurement_group.parent
    create_attributes(entry_group, {"default": measurement_group.name})
    return

def set_default_slice(main_dataset: h5py.Dataset, axes: int | tuple[int] | list[int] | None = None, indices: int | tuple[int] | list[int] | None = None) -> None:
    measurement_group = main_dataset.parent
    rank = main_dataset.ndim
    
    if not axes: axes = tuple([index for index in range(rank - 2)])
    if not indices: indices = tuple([0 for _ in range(rank - 2)])
    
    if isinstance(axes, int): axes = [axes]
    if isinstance(indices, int): indices = [indices]
    
    if not len(axes) == rank - 2: raise Exception(f"Wrong number of slice axes ({len(axes)}). Expected number to create a 2D slice: {rank - 2}")
    if not len(indices) == rank - 2: raise Exception(f"Wrong number of slice indices ({len(indices)}). Expected number to create a 2D slice: {rank - 2}")
    
    found = False
    default_slice = []
    for axis_index in range(rank):
        for axis, index in zip(axes, indices):
            if axis == axis_index:
                found = True
                default_slice.append(str(index))
                break
        if found:
            found = False
            continue
        else:
            default_slice.append(":")
    
    create_attributes(main_dataset, {"default_slice_axes": axes, "default_slice_indices": indices, "default_slice": default_slice})
    create_attributes(measurement_group, {"default_slice_axes": axes, "default_slice_indices": indices, "default_slice": default_slice})
    return

def find_dataset(root: File | h5py.File, name: str = "") -> h5py.Dataset:
    entry_group = get_entry_group(root)
    
    for group in get_groups(entry_group).values():        
        for dataset_name, dataset in get_datasets(group).items():
            if name.lower() == dataset_name.lower(): return dataset
    
    # Loose matching
    for group in get_groups(entry_group).values():
        for dataset_name, dataset in get_datasets(group).items():
            if name.lower() in dataset_name.lower(): return dataset
    raise KeyError("Group \"{name}\" not found.")



# Ancillary / Axis datasets
def create_ancillary_dataset(root: File | h5py.File, dataset: Dataset | None = None, name: str = "", units: str = "", existsok: bool = True, attributes: dict = {},
                             data: np.ndarray | None = None, dtype: np.typing.DTypeLike | None = None, shape: tuple | None = None, NeXus_compliant: bool = True, verbose: bool = False) -> h5py.Dataset:
    """Create a dataset that will become an axis to a main dataset. It is stored by default in the Ancillary Group, and Softlinked to the main dataset group upon calling attach_axis. Ancillary datasets are 1D and resizable by default.

    Args:
        root (h5py.File): Root.
        dataset (spmh5.Dataset, optional): Dataset object. If provided, use it to set up the ancillary dataset. If not, use the kwargs below.
        name (str, optional): Dataset name. Defaults to "".
        existsok (bool, optional): Allow overwriting. Defaults to True.
        units (str, optional): Units. Defaults to "".
        attributes (dict, optional): Custom attributes. Defaults to {}.
        data (np.ndarray | None, optional): Data. Defaults to None.
        dtype (np.typing.DTypeLike | None, optional): Data type. Defaults to None.
        shape (tuple | None, optional): Shape of dataset. Defaults to None. Passing shape and maxshape instead of data will trigger chunking.
        maxshape (tuple | int | None, optional): Maximum shape. Defaults to None.
        verbose (bool, optional): Whether to output details to terminal. Defaults to False.

    Returns:
        h5py.Dataset: The dataset
    """
    try:
        # Find or create the entry group
        entry_group = get_entry_group(root, name = "Measurement_000", verbose = verbose)
        entry_subgroups = get_groups(entry_group)
        
        # If an SPMH5 Dataset is provided explicitly, use the values attached to it to create the h5py dataset
        if isinstance(dataset, Dataset):
            name = dataset.name
            data = dataset.data
            shape = dataset.shape
            units = dataset.units
            ds_attrs = dataset.attrs
            dtype = dataset.dtype
            
            attributes.update(ds_attrs)
        
        # Find or create the Ancillary group (The group that stores the axes)
        if "Ancillary" in entry_subgroups.keys():
            ancillary_group = entry_subgroups["Ancillary"]
        else:
            ancillary_group = create_group(entry_group, name = "Ancillary")
            if NeXus_compliant: set_NeXus_tag(ancillary_group, "axes")
        
        ancillary_datasets = get_datasets(ancillary_group)
        
        if name in ancillary_datasets.keys():
            if existsok:
                existing_ds = ancillary_datasets[name]
                assert isinstance(existing_ds, h5py.Dataset)
                if not existing_ds.shape == shape:
                    raise Exception(f"Error: While creating a dataset with the name {name}, another dataset with the same name but different shape was found in this HDF5 file.")
                else:
                    if verbose: print(f"Warning! A dataset with the name {name} already exists.")
                    create_attributes(existing_ds, attributes = attributes)
                    return existing_ds
            else:
                raise Exception(f"Error: A dataset with the same name ({name}) was already found in this HDF5 file. Aborting.")

        # Create the dataset
        if isinstance(data, np.ndarray):
            dataset_out = create_dataset(ancillary_group, name, data = data, maxshape = (None,), dtype = dtype, units = units, attributes = attributes)
            set_NeXus_tag(dataset_out, "axis")
        elif isinstance(shape, tuple):
            dataset_out = create_dataset(ancillary_group, name, shape = shape, maxshape = (None,), dtype = dtype, units = units, attributes = attributes)
            set_NeXus_tag(dataset_out, "axis")
        else: raise Exception("Neither data nor shape were provided when attempting to create a dataset")
        
        return dataset_out
    
    except Exception as e:
        raise Exception(f"Error encountered while attempting to create a new h5py dataset called {name}: {e}")

def attach_axis(main_dataset: h5py.Dataset, ancillary_dataset: h5py.Dataset, axis: int = 0) -> None:
    try:
        # Extract all the information from the main dataset and its parent group
        main_dataset_path = main_dataset.name
        main_dataset_group = main_dataset.parent
        assert isinstance(main_dataset_path, str) and isinstance(main_dataset_group, h5py.Group | h5py.File)
        main_dataset_name = os.path.basename(main_dataset_path)
        main_dataset_group_attrs = get_attributes(main_dataset_group)
        main_dataset_rank = main_dataset.ndim
        
        # Extract all the information from the axis dataset and its parent group
        axis_dataset_path = ancillary_dataset.name
        axis_dataset_group = ancillary_dataset.parent
        assert isinstance(axis_dataset_path, str) and isinstance(axis_dataset_group, h5py.Group | h5py.File)
        axis_name = os.path.basename(axis_dataset_path)
        axis_attrs = get_attributes(ancillary_dataset)
        
        axis_units = axis_attrs.get("units", "none")
        axis_dtype = ancillary_dataset.dtype
        axis_data = ancillary_dataset[:]
        axis_dpoints = len(axis_data)
        axis_is_strings = (axis_dtype.kind in ('O', 'S', 'U')) or (h5py.check_string_dtype(axis_dtype) is not None)

        # Check if the target name already exists in the destination group (even if it's a broken soft link)
        if axis_name in main_dataset_group: del main_dataset_group[axis_name]

        # Put the axis dataset in the main dataset group in the form of a soft link to its origin in the Ancillary group
        main_dataset_group[axis_name] = h5py.SoftLink(axis_dataset_path)
        local_axis_ds = main_dataset_group[axis_name]
        assert isinstance(local_axis_ds, h5py.Dataset)
        
        # Attach it directly for NSID compliance
        local_axis_ds.make_scale(axis_name) # h5py's make_scale automatically creates attributes 'CLASS' and 'NAME'
        main_dataset.dims[axis].attach_scale(local_axis_ds) # h5py's attach_scale automatically creates attributes 'REFERENCE_LIST' and 'DIMENSION_LIST'
        main_dataset.file.flush()
        
        # Find the declared axes (NeXus) attribute in the main dataset group and update it with the name of the axis dataset
        main_dataset_axes = main_dataset_group_attrs.get("axes", None)
        if not isinstance(main_dataset_axes, list | np.ndarray) or not len(main_dataset_axes) == main_dataset_rank: main_dataset_axes = ["." for _ in range(main_dataset_rank)]
        
        if axis_is_strings:
            main_dataset_axes[axis] = "." # NeXus/H5Web compliance: Provide "." as the axis placeholder so it renders as numeric indices
            create_attributes(main_dataset_group, {f"{axis_name}_indices": [axis], "axes": main_dataset_axes}) # Add NeXus attributes
        else:
            main_dataset_axes[axis] = axis_name
            create_attributes(main_dataset_group, {"axes": main_dataset_axes}) # Add NeXus attributes
            
            if axis_dpoints < 2: axis_range = np.zeros(shape = (2,), dtype = axis_dtype) # Empty axis
            else: axis_range = np.array([axis_data[0], axis_data[-1]], dtype = axis_dtype)

            # Attributes for Gwyddion compatibility
            match axis:
                case 0: range_units_attrs = {"X Range": axis_range, "X Units": axis_units, "X No": axis_dpoints}
                case 1: range_units_attrs = {"Y Range": axis_range, "Y Units": axis_units, "Y No": axis_dpoints}
                case 2: range_units_attrs = {"Z Range": axis_range, "Z Units": axis_units, "Z No": axis_dpoints}
                case _: range_units_attrs = {"A Range": axis_range, "A Units": axis_units, "A No": axis_dpoints}
                
            [create_attributes(target, range_units_attrs) for target in [main_dataset, main_dataset_group]]
            create_attributes(ancillary_dataset, {"axis": axis, "main_dataset_path": main_dataset_path})
        
    except Exception as e:
        try:
            print(f"Failed to attach dataset {axis_name} to axis {axis} of {main_dataset_name}: {e}")
        except Exception as e:
            print(f"Failed to attach dataset {ancillary_dataset} to axis {axis} of {main_dataset}: {e}")
    return

def create_linear_axis(main_dataset: h5py.Dataset, axis: int = 0, name: str = "", limits: Sequence = (0, 1), units: str = "", existsok: bool = True, attributes: dict = {}, include_boundary: bool = False, verbose: bool = False) -> h5py.Dataset:
    try:
        root = get_root(main_dataset)
        n_elements = main_dataset.shape[axis]
        
        if include_boundary:
            values = np.linspace(limits[0], limits[1], n_elements)
        else:
            point_size = (limits[1] - limits[0]) / n_elements
            values = np.linspace(limits[0] + point_size / 2, limits[1] - point_size / 2, n_elements)
        
        axis_ds = create_ancillary_dataset(root, name = name, units = units, data = values, existsok = existsok, attributes = attributes, verbose = verbose) # type: ignore
        attach_axis(main_dataset, axis_ds, axis = axis)        
    except Exception as e:
        raise Exception(f"Could not create a linear dataset attached to {main_dataset}: {e}")
    return axis_ds

def create_axes_from_frame(main_dataset: h5py.Dataset, frame: CoordinateFrame, names: list = ["x", "y", "z", "a"], include_boundaries: bool | list[bool] = False) -> list[h5py.Dataset]:
    if not main_dataset.ndim == frame.rank: raise Exception(f"Rank of dataset ({main_dataset.ndim}) does not match dimensionality of frame ({frame.rank})")
    if isinstance(include_boundaries, bool): include_boundaries = [include_boundaries for _ in range(main_dataset.ndim)]
    
    dataset_list = []
    for dim, (limits, units, name, include_boundary) in enumerate(zip(frame.ranges, frame.units, names, include_boundaries)):
        ds = create_linear_axis(main_dataset, axis = dim, name = name, limits = limits, units = units, include_boundary = include_boundary) # type: ignore
        dataset_list.append(ds)
    return dataset_list

def update_axis(ancillary_dataset: h5py.Dataset) -> None:
    try:
        root = ancillary_dataset.file
        
        axis_attrs = get_attributes(ancillary_dataset)
        
        axis_dtype = ancillary_dataset.dtype
        axis_is_strings = (axis_dtype.kind in ('O', 'S', 'U')) or (h5py.check_string_dtype(axis_dtype) is not None)
        
        axis_data = ancillary_dataset[:]
        axis_dpoints = len(axis_data)
        
        if axis_is_strings or axis_dpoints < 2: axis_range = np.empty(shape = (2,), dtype = axis_dtype) # Empty axis
        else: axis_range = np.array([axis_data[0], axis_data[1]], dtype = axis_dtype)
        
        main_dataset_path = axis_attrs.get("main_dataset_path", "")
        axis_of_main_dataset = int(axis_attrs.get("axis", 0))
        
        if main_dataset_path:
            main_dataset = root[main_dataset_path]
            main_dataset_group = main_dataset.parent
            assert isinstance(main_dataset, h5py.Dataset) and isinstance(main_dataset_group, h5py.Group)
            
            match axis_of_main_dataset:
                case 0: range_attrs = {"X Range": axis_range, "X No": axis_dpoints}
                case 1: range_attrs = {"Y Range": axis_range, "Y No": axis_dpoints}
                case 2: range_attrs = {"Z Range": axis_range, "Z No": axis_dpoints}
                case _: range_attrs = {"A Range": axis_range, "A No": axis_dpoints}
            
            [create_attributes(target, range_attrs) for target in [main_dataset, main_dataset_group]]
    
    except Exception as e:
        print(f"Failed to update dataset {ancillary_dataset}: {e}")
    return



# Thumbnail
def calculate_thumbnail(root: File | h5py.File, main_dataset: h5py.Dataset | None = None, axes: int | tuple[int] | list[int] | None = None, indices: int | tuple[int] | list[int] | None = None, thumbnail_size: int = 256) -> np.ndarray:
    if not isinstance(main_dataset, h5py.Dataset):
        entry_group = get_entry_group(root)
        eg_attrs = get_attributes(entry_group)
        default = eg_attrs.get("default", "")        
        main_ds_group = root.get(default, None)
        
        if not isinstance(main_ds_group, h5py.Group): raise Exception("Could not find the default dataset in this file. Please earmark it using \"set_default(dataset)\".")
        mdg_attrs = get_attributes(main_ds_group)
        main_ds_name = mdg_attrs.get("signal", "")
        main_dataset = main_ds_group[main_ds_name]
    
    if not isinstance(main_dataset, h5py.Dataset): raise Exception("No dataset to extract a thumbnail from.")
    main_ds_data = main_dataset[:]    
    main_ds_rank = main_ds_data.ndim
    
    match main_ds_rank:
        case 1:
            raise NotImplementedError("I don't know yet how to create a thumbnail from a 1D dataset")
        case 2:
            sliced_data = np.stack([main_ds_data for _ in range(3)], axis = -1)
        case 3 | 4 | 5 | 6 | 7:
            
            main_dataset_attrs = get_attributes(main_dataset)
            ds_axes = main_dataset_attrs.get("default_slice_axes", None)
            ds_indices = main_dataset_attrs.get("default_slice_indices", None)

            if not isinstance(axes, list | np.ndarray | tuple) or not len(axes) == main_ds_rank - 2:
                if not isinstance(ds_axes, list | np.ndarray | tuple): raise Exception("Invalid slice axes for this dataset")
                else: axes = ds_axes
            if not isinstance(indices, list | np.ndarray | tuple) or not len(indices) == main_ds_rank - 2:
                if not isinstance(ds_indices, list | np.ndarray | tuple): raise Exception("Invalid slice axes for this dataset")
                else: indices = ds_indices
            
            slice_list = [slice(None) for _ in range(main_ds_rank)]
            for axis, index in zip(axes, indices):
                slice_list[axis] = index
            sliced_data = main_ds_data[tuple(slice_list)]
        case _:
            raise Exception("Invalid dimensionality for dataset")
    
    assert isinstance(sliced_data, np.ndarray)
    if np.issubdtype(sliced_data.dtype, np.complexfloating): array = complex_to_rgba(sliced_data)
    else: array = sliced_data
    
    scale = thumbnail_size / max(array.shape)
    if array.ndim == 3: slice_resized = zoom(array, (scale, scale, 1), order = 1)
    else: slice_resized = zoom(array, (scale, scale), order = 1)
    [min_val, max_val] = [slice_resized.min(), slice_resized.max()]

    if not max_val > min_val: return np.zeros(slice_resized.shape, dtype = np.uint8)
    
    normalized = (slice_resized - min_val) / (max_val - min_val) * 255.0
    return np.round(normalized).astype(np.uint8)

def set_thumbnail(root: File | h5py.File, main_dataset: h5py.Dataset | None = None, axes: int | tuple[int] | list[int] | None = None, indices: int | tuple[int] | list[int] | None = None, thumbnail_size: int = 256) -> tuple[h5py.Group, h5py.Dataset]:
    thumbnail = calculate_thumbnail(root, main_dataset, axes, indices, thumbnail_size)
    
    existing_groups = get_groups(root)
    if "thumbnail" in existing_groups.keys(): thumbnail_group = root["thumbnail"]
    else: thumbnail_group = create_group(root, "thumbnail")
    
    set_NeXus_tag(thumbnail_group, "data")
    
    thumbnail_datasets = get_datasets(thumbnail_group)
    if "thumbnail" in thumbnail_datasets.keys():
        thumbnail_ds = thumbnail_group["thumbnail"]
        thumbnail_ds.resize(thumbnail.shape)
        thumbnail_ds[:] = thumbnail
    else: thumbnail_ds = create_dataset(thumbnail_group, name = "thumbnail", units = "none", data = thumbnail, resizable_axes = [0, 1, 2])
    
    create_attributes(thumbnail_group, {"signal": "thumbnail"})
    create_attributes(thumbnail_ds, {"interpretation": "rgba-image"})
    return thumbnail_group, thumbnail_ds

def get_thumbnail(root: File | h5py.File) -> np.ndarray:
    groups = get_groups(root)
    if not "thumbnail" in groups.keys():
        try:
            set_thumbnail(root)
        except Exception as e:
            raise Exception(f"Failed to get thumbnail. Try setting if manually by using set_thumbnail while the file is in append mode. {e}")
    
    groups = get_groups(root)
    try:
        thumbnail = root["thumbnail/thumbnail"]
    except:
        raise Exception(f"Unable to extract thumbnail from file")
    return thumbnail[:]



# Misc
def infer_quantity_from_units(units: str = "") -> tuple[str, str]:
    quantity = ""
    dimension_type = "spectral"
    
    if units in {"m", "dm", "cm", "mm", "um", "nm", "pm", "Ang"}:
        quantity = "Length"
        dimension_type = "spatial"
    if units in {"m-1", "dm-1", "cm-1", "mm-1", "um-1", "nm-1", "pm-1", "Ang-1", "/m", "/dm", "/cm", "/mm", "/um", "/nm", "/pm", "/Ang"}:
        quantity = "Length"
        dimension_type = "reciprocal"
    if units in {"eV", "J", "kcal"}:
        quantity = "Energy"
    if units in {"Hz", "s-1", "/s"}:
        quantity = "Frequency"
    if units in {"A", "mA", "uA", "nA", "pA", "fA"}:
        quantity = "Current"
    if units in {"V", "mV", "uV", "nV", "pV", "fV"}:
        quantity = "Voltage"
    if units in {"S", "mS", "uS", "nS", "pS", "fS"}:
        quantity = "Conductance"
    if units in {"F", "mF", "uF", "nF", "pF", "fF"}:
        quantity = "Capacitance"

    return dimension_type, quantity

def print_dict(dictionary: dict = {}, indent: int = 4, global_indent: int = 0):
    try:
        yaml.add_representer(Dataset, lambda dumper, data: dumper.represent_scalar("tag:yaml.org,002:str", repr(data)))
        yaml.add_representer(np.ndarray, lambda dumper, data: dumper.represent_sequence("tag:yaml.org,2002:seq", data.tolist()))
        yaml.add_multi_representer(np.floating, lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:float", str(data.item())))
        yaml.add_multi_representer(np.integer, lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:int", str(data.item())))
        
        indent_string = "".join([" " for _ in range(global_indent)])
        yaml_string = yaml.dump(dictionary, default_flow_style = False, sort_keys = False, indent = indent, Dumper = IndentDumper)
        print(textwrap.indent(yaml_string, indent_string))
    except Exception as e:
        pprint.pprint(dictionary)
        print(f"Cannot print this dictionary using pyyaml: {e}")
    return

def file_summary(root_or_path: h5py.File | str = "", focus: Literal["structure", "datasets"] = "datasets"):
    if isinstance(root_or_path, h5py.File):
        file_dict = get_file_dict(root_or_path)
    elif isinstance(root_or_path, str):
        with File(path = root_or_path, mode = "r") as root:
            file_dict = get_file_dict(root)
    
    group_data = file_dict.get("groups", {})
    main_datasets = file_dict.get("main_datasets", {})
    axis_datasets = file_dict.get("axis_datasets", {})
    
    root_data = group_data.get("./", {})
    
    if focus == "structure":
        print(f"Structure summary of HDF5 file {root_data.get("filename", "unknown")}, containing {len(main_datasets)} main datasets and {len(axis_datasets)} ancillary datasets, created on {root_data.get("creation_date", "unknown")} at {root_data.get("creation_time", "unknown")}.\n")
        print_dict(file_dict)
        return
    
    print(f"Dataset summary of HDF5 file {root_data.get("filename", "unknown")}, containing {len(main_datasets)} main datasets and {len(axis_datasets)} ancillary datasets, created on {root_data.get("creation_date", "unknown")} at {root_data.get("creation_time", "unknown")}.\n")
    
    for main_dataset in main_datasets.values():
        print(f"\n\n    Info for main dataset {main_dataset.get("name", "unknown")}:\n")
        print_dict(main_dataset, global_indent = 4)
        
        main_dataset_axes = main_dataset.get("axes", [])
        assert isinstance(main_dataset_axes, list)
        
        print("        Attached to this dataset are the following axis datasets:\n")
        for axis_index, axis in enumerate(main_dataset_axes):
            axis_dataset = axis_datasets.get(axis, {})            
            print_dict({f"axis {axis_index}: {axis_dataset.get("name", "unknown")}": axis_dataset}, global_indent = 8)
    return



# Reading
def get_object(root_or_path: str | h5py.File | h5py.Group, internal_path: str = "") -> h5py.Group | h5py.Dataset | h5py.Datatype | np.ndarray | None:
    should_close = isinstance(root_or_path, str)
    
    if should_close: root = h5py.File(root_or_path, "r")
    elif isinstance(root_or_path, h5py.File | h5py.Group): root = root_or_path
    else:
        print(f"Invalid type {type(root_or_path)} provided to get_dataset")
        return None
    
    try:
        obj = root.get(internal_path, None)
        if obj == None:
            print(f"Path {internal_path} not found in HDF5 file")
            return None
        
        elif isinstance(obj, h5py.Dataset): return obj[()]
        return obj # type: ignore
    
    except Exception as e:
        print(f"Could not retrieve object from file using internal path {internal_path}")
    
    finally:
        if should_close:
            assert isinstance(root, h5py.File)
            root.close()
    return



class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super(IndentDumper, self).increase_indent(flow, indentless = False)



class Datacollection:
    """Class containing a collection of datagrids, instruments, and other file data
    """
    def __init__(self, name: str = "unknown", creator: str = "unknown", date: str = "unknown", time: str = "unknown", thumbnail: np.ndarray = np.zeros((12, 12, 3), dtype = np.uint8),
                 groups: dict = {}, instruments: dict = {}, other_datasets: dict = {}, attrs: dict = {}, data_grids: list[Datagrid] = [], default: str | Datagrid = ""):
        self.name = name
        self.creator = creator
        self.date = date
        self.time = time
        self.groups = groups
        self.instruments = instruments
        self.other_datasets = other_datasets
        self.attrs = attrs
        self.data_grids = data_grids
        self.default = default
        self.thumbnail = thumbnail
        
        for data_grid in data_grids:
            if data_grid.dataset.name == os.path.basename(self.default):
                self.default = data_grid
                break

    def __repr__(self) -> str:
        return f"SPMH5 Datacollection \"{self.name}\" created by {self.creator} on {self.date} at {self.time}, containing {len(self.data_grids)} data grids. Use .info() for more information"

    def __getitem__(self, key) -> Datagrid:        
        return self.data_grids[key]
    
    def __len__(self) -> int:
        return len(self.data_grids)

    def info(self) -> None:
        print(f"SPMH5 Datacollection \"{self.name}\" created by {self.creator} on {self.date} at {self.time}, containing {len(self.data_grids)} data grids.\n\n")
        if len(self.data_grids) > 0:
            print("Data grids (self.data_grids):\n")
            [print(data_grid) for data_grid in self.data_grids]
        if len(self.default) > 0:
            print(f"Default dataset (self.default):\n")
            print(self.default)
        if len(self.instruments) > 0:
            print(f"Instruments (self.instruments):\n")
            print_dict(self.instruments)
        if len(self.groups) > 0:
            print(f"Groups (self.groups):\n")
            print_dict(self.groups)
        if len(self.attrs) > 0:
            print(f"File attributes (self.attrs):\n")
            print_dict(self.attrs)
        if len(self.other_datasets) > 0:
            print(f"Other datasets (self.other_datasets):\n")
            print_dict(self.other_datasets)
        return

    @classmethod
    def from_file(cls, file_path: str = ""):
        with File(path = file_path, mode = "r") as root:
            file_dict, data_grids = get_data_grids(root)
            groups = file_dict["groups"]
            root_group = groups.get("./", {})
            if not isinstance(root_group, dict): raise Exception(f"Invalid root group type {type(root_group)}. Expected a dict")
            
            default = ""
            root_attrs = get_attributes(root)
            assert isinstance(root_attrs, dict)
            [filename, creator, file_time, file_date, default] = [root_attrs.get(key, "unknown") for key in ["filename", "creator", "creation_time", "creation_date", "default"]]
            if not filename: filename = os.path.basename(file_path)
            
            entry_group = {}
            if default != "unknown":
                entry_group = groups[default]
            else:
                for group_path, group_info in groups.items():
                    if "NXentry" in group_info.values():
                        entry_group = groups[group_path]
                        break
            
            if entry_group:
                eg_attrs = entry_group.get("attrs", {})
                assert isinstance(eg_attrs, dict)
                default = eg_attrs.get("default", "")
            
            other_datasets = file_dict["other_datasets"]
            tn_ds = None
            if "thumbnail/thumbnail" in other_datasets.keys():
                tn_ds = other_datasets["thumbnail/thumbnail"].get("dataset_object")
            
            if isinstance(tn_ds, Dataset): thumbnail = tn_ds[:]
            else: thumbnail = np.zeros((12, 12, 4), dtype = np.uint8)
            
        return cls(name = filename, creator = creator, date = file_date, time = file_time, groups = groups, instruments = file_dict["instruments"], other_datasets = other_datasets,
                   attrs = root_attrs, thumbnail = thumbnail, data_grids = data_grids, default = default)

    def to_file(self, file_path: str = ""):
        raise NotImplementedError()


