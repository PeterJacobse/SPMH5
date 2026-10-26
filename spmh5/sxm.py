import re, os, h5py, inspect
import numpy as np
from datetime import datetime, timezone
from .file_picker import get_file_path_from_dialog
from .h5 import Dataset, Datagrid, Datacollection, CoordinateFrame, File



# SXM files: headers
def get_raw_header(file_path: str = "", end_tag: str = ":SCANIT_END:") -> tuple[list, int]:
    if not file_path: file_path = get_file_path_from_dialog(extensions = ["sxm"], io = "load")
    if not os.path.isfile(file_path): raise Exception("Invalid file selected.")
    raw_header: list = []
    end_tag_position: int = 0
    
    try:
        with open(file_path, "rb") as file:
            while True:
                current_pos = file.tell()
                
                line = file.readline()
                if not line: break
                decoded = line.decode('utf-8').split()
                raw_header.append(decoded)
                
                if end_tag in decoded:
                    # The binary data starts exactly where the NEXT line begins
                    end_tag_position = file.tell()
                    break
    except Exception as e: raise Exception(f"Unable to retrieve raw sxm header: {e}")
    return raw_header, end_tag_position

def get_header(file_path: str = "", end_tag: str = ":SCANIT_END:") -> tuple[dict, int]:
    raw_header, end_tag_position = get_raw_header(file_path, end_tag)
    
    tag_substitutions = {":NANONIS_VERSION:": "Nanonis_version", ":SCANIT_TYPE:": "data_type", ":REC_DATE:": "creation_date", ":REC_TIME:": "creation_time", ":REC_TEMP:": "temperature (K)", ":SCAN_RANGE:": "domain (nm)", ":ACQ_TIME:": "scan_duration (s)", ":SCAN_FILE:": "file_path",
                         ":COMMENT:": "comment", ":Z-CONTROLLER:": "z_controller", ":SCAN_ANGLE:": "angle (deg)", ":SCAN_OFFSET:": "offset (nm)", ":SCAN_PIXELS:": "shape", ":SCAN_DIR:": "scan_up", ":BIAS:": "V (V)", ":DATA_INFO:": "data"}

    header_dict = {}
    for index, line in enumerate(raw_header):
        if len(line) < 1 or not isinstance(line[0], str): continue
                
        if line[0] in tag_substitutions.keys():
            sct_tag = tag_substitutions[line[0]]
            
            value_line = raw_header[index + 1]
            if len(value_line) < 1: continue
            if len(value_line) == 1: value_line = value_line[0]
            
            value_line_as_floats = extract_numbers(value_line, nest = False, return_string_if_fails = True)            
            if len(value_line_as_floats) == 1: value_line_as_floats = value_line_as_floats[0]

            processed_value_line = []
            match sct_tag:
                case "Nanonis_version": processed_value_line.append(value_line_as_floats)
                case "data_type": processed_value_line.append([value.lower() for value in value_line])
                case "temperature": processed_value_line.append(value_line_as_floats)
                case "creation_date": processed_value_line.append("/".join(value_line.split(".")))
                case "scan_duration (s)": processed_value_line.append(value_line_as_floats)
                case "domain (nm)":
                    assert isinstance(value_line_as_floats, list)
                    processed_value_line.append([1E9 * dim for dim in value_line_as_floats])
                case "offset (nm)":
                    assert isinstance(value_line_as_floats, list)
                    processed_value_line.append([1E9 * dim for dim in value_line_as_floats])
                case "shape": processed_value_line.append([int(value) for value in value_line_as_floats])
                case "angle (deg)": processed_value_line.append(value_line_as_floats)
                case "scan_up": processed_value_line.append(bool(value_line_as_floats == "up"))
                case "V (V)": processed_value_line.append(value_line_as_floats)
                case "z_controller":
                    value_line2 = extract_numbers(raw_header[index + 2], return_string_if_fails = True)
                    if not isinstance(value_line2, list) or len(value_line2) < 1: continue
                    header_dict.update({sct_tag: [value_line, value_line2]})
                    continue
                case "data":
                    description_line = [entry.lower() for entry in value_line]
                    
                    for channel_index in range(100):
                        value_line = raw_header[index + 2 + channel_index]
                        if len(value_line) < 1: break
                        value_line = extract_numbers(value_line, nest = False, return_string_if_fails = True)
                        processed_value_line.append({description_line[entry]: value_line[entry] for entry in range(min(len(description_line), len(value_line)))})
                        
                case _: processed_value_line.append(value_line)
            
            if len(processed_value_line) == 1: header_dict.update({sct_tag: processed_value_line[0]})
            elif len(processed_value_line) > 1: header_dict.update({sct_tag: processed_value_line})
    
    return header_dict, end_tag_position

def get_file(file_path: str = "", header_end_tag: str = ":SCANIT_END:") -> Datacollection:
    if not file_path: file_path = get_file_path_from_dialog(extensions = ["sxm"], io = "load")
    if not os.path.isfile(file_path): raise Exception("Invalid file selected.")
    
    header_dict, end_tag_position = get_header(file_path, end_tag = header_end_tag)
    domain = header_dict.pop("domain (nm)", [])
    offset = header_dict.pop("offset (nm)", [0, 0])
    angle = header_dict.pop("angle (deg)", 0.)
    
    data_info: dict | list[dict] = header_dict.pop("data", [])
    if isinstance(data_info, dict): data_info = [data_info]
    array_shape: list[int] = header_dict.pop("shape", [])    
    n_bytes: int = int(4 * np.prod(array_shape))
    dt = np.dtype(">f4")
    
    channel_list: list[Dataset] = []
    
    # Extract Datasets
    with open(file_path, mode = "rb") as file:
        file.seek(end_tag_position + 4)
        
        for channel in data_info:
            name = channel.pop("name", "").lower()
            units = channel.pop("unit", "")
            direction = channel.pop("direction", "")
            channel_index = int(channel.pop("channel", 0))
            
            dset_attrs = channel.copy()
            dset_attrs.update({"channel_index": channel_index})
            
            multiplication_factor = 1
            if units == "m":
                units = "nm"
                multiplication_factor = 1E9
            if units == "A":
                units = "pA"
                multiplication_factor = 1E12
            
            raw_bytes = file.read(n_bytes)
            array = np.astype(np.flipud(np.frombuffer(raw_bytes, dtype = dt).reshape(array_shape).copy() * multiplication_factor), np.float32)
            
            if direction == "both":
                channel_list.append(Dataset(name = f"{name} [fwd]", units = units, data = array, attrs = channel))
                
                raw_bytes = file.read(n_bytes)
                array = np.astype(np.flipud(np.fliplr(np.frombuffer(raw_bytes, dtype = dt).reshape(array_shape).copy()) * multiplication_factor), np.float32)
                
                channel_list.append(Dataset(name = f"{name} [bwd]", units = units, data = array, attrs = channel))
            else:
                channel_list.append(Dataset(name = name, units = units, data = array, attrs = channel))



    # To Datagrids
    try: frame = CoordinateFrame(x_range = domain[0], y_range = domain[1], units = "nm", anchor = [.5, .5], angle_units = "degree", offset = offset, angles = [angle, 0.])
    except Exception as e: raise Exception(f"Failed to create CoordinateFrame object: {e}")
    
    data_grids = [Datagrid.from_frame(dataset, frame, axes_names = ["x", "y"], include_boundaries = False) for dataset in channel_list]



    # To Datacollection
    file_name = os.path.basename(header_dict.pop("file_path", ""))
    date = header_dict.pop("creation_date", "")
    time = header_dict.pop("creation_time", "")

    dc = Datacollection(name = file_name, creator = "Nanonis", date = date, time = time, attrs = header_dict, data_grids = data_grids)
    return dc

def convert_to_h5(file_path: str = "", output_path: str = "", existsok = False) -> None:
    if not file_path: file_path = get_file_path_from_dialog(extensions = ["sxm"])
    dc = get_file(file_path)
    
    if not output_path:
        folder = os.path.dirname(file_path)
        file_basename = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(folder, file_basename) + ".h5"
    
    with File(output_path, mode = "w", existsok = existsok) as root: root.create_datacollection(dc)
    return



# Misc
def split_physical_quantity(text: str) -> tuple:
    error = False
    quantity = None
    unit = None
    backward = False
    first_bracket_index = None
    
    try:
        split_text = text.split()
        for index, text_item in enumerate(split_text):
            if text_item.startswith("(") | text_item.startswith("["):
                if not first_bracket_index: first_bracket_index = index
                if text_item[1:-1] in {"bwd", "backward"}: backward = True
                if text_item[1:-1] not in {"fwd", "forward", "bwd", "backward"}: unit = text_item[1:-1]
        quantity = " ".join(split_text[:first_bracket_index])

        return (quantity, unit, backward, error)
    except:
        error = True
    
    return (quantity, unit, backward, error)

def convert_data_to_unit(data: np.ndarray, quantity: str, target_unit: str | None = None) -> str:
    """
    This function converts data (in np.ndarray form) from a certain physical quantity to a different quantity.
    The np.ndarray is changes in place, while the funciton exports the new quantity with the new unit attached to it.
    """
    output_quantity = quantity
    input_multiplier = 1
    target_multiplier = 1
    
    try:
        (input_quantity, input_unit, backward, error) = split_physical_quantity(quantity)
        
        if not target_unit:
            match input_unit[-1]:
                case "A": target_unit = "pA"
                case "m": target_unit = "nm"
                case "S": target_unit = "nS"
                case "V": target_unit = "V"
                case _: target_unit = input_unit
        
        input_prefix = input_unit[0] # Try to get the prefix
        if input_prefix == "/": # Convert reciprocal notation, e.g. /nm to nm-1
            input_unit = input_unit[1:] + "-1"
            input_prefix = input_unit[0] # Reset the input prefix now that the division sign is removed
        
        if input_prefix in {"f", "p", "n", "u", "m", "c", "k", "M", "G"} and not input_unit in {"m", "m-1"}:
            if input_unit[-1] == "1": # Unit is of reciprocal type, like nm-1 or pA-1
                match input_prefix:
                    case "f": input_multiplier = 1E15
                    case "p": input_multiplier = 1E12
                    case "n": input_multiplier = 1E9
                    case "u": input_multiplier = 1E6
                    case "m": input_multiplier = 1E3
                    case "c": input_multiplier = 1E2
                    case "k": input_multiplier = 1E-3
                    case "M": input_multiplier = 1E-6
                    case "G": input_multiplier = 1E-9
                    case _: pass
            else: # Unit is of real type, like s or mV
                match input_prefix:
                    case "f": input_multiplier = 1E-15
                    case "p": input_multiplier = 1E-12
                    case "n": input_multiplier = 1E-9
                    case "u": input_multiplier = 1E-6
                    case "m": input_multiplier = 1E-3
                    case "c": input_multiplier = 1E-2
                    case "k": input_multiplier = 1E3
                    case "M": input_multiplier = 1E6
                    case "G": input_multiplier = 1E9
                    case _: pass
        
        target_prefix = target_unit[0] # Try to get the prefix
        if target_prefix == "/": # Convert reciprocal notation, e.g. /nm to nm-1
            target_unit = target_unit[1:] + "-1"
            target_prefix = target_unit[0] # Reset the input prefix now that the division sign is removed
        
        if target_prefix in {"f", "p", "n", "u", "m", "c", "k", "M", "G"} and not target_unit in {"m", "m-1"}:
            if target_unit[-1] == "1": # Unit is of reciprocal type, like nm-1 or pA-1
                match target_prefix:
                    case "f": target_multiplier = 1E-15
                    case "p": target_multiplier = 1E-12
                    case "n": target_multiplier = 1E-9
                    case "u": target_multiplier = 1E-6
                    case "m": target_multiplier = 1E-3
                    case "c": target_multiplier = 1E-2
                    case "k": target_multiplier = 1E3
                    case "M": target_multiplier = 1E6
                    case "G": target_multiplier = 1E9
                    case _: pass
            else:
                match target_prefix:
                    case "f": target_multiplier = 1E15
                    case "p": target_multiplier = 1E12
                    case "n": target_multiplier = 1E9
                    case "u": target_multiplier = 1E6
                    case "m": target_multiplier = 1E3
                    case "c": target_multiplier = 1E2
                    case "k": target_multiplier = 1E-3
                    case "M": target_multiplier = 1E-6
                    case "G": target_multiplier = 1E-9
                    case _: pass
        
        data *= (input_multiplier * target_multiplier)
        output_quantity = " ".join((input_quantity, f"({target_unit})"))
    except Exception as e:
        print(f"Error encountered while trying to convert data ({quantity}) to unit {target_unit}: {e}")
    return output_quantity

def extract_numbers(text: str | list[str], nest: bool = False, return_string_if_fails: bool = False, reduce_to_integers: bool = False) -> list | str:
    pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
    
    if isinstance(text, str):
        matches = re.findall(pattern, text)
        if len(matches) < 1:
            if return_string_if_fails: return text
            else: return []
        numbers = [float(x) for x in matches]
        if reduce_to_integers: numbers = [int(number) for number in numbers if number.is_integer()]
        return numbers

    return_list = []
    for entry in text:
        if not isinstance(entry, str): continue
        
        matches = re.findall(pattern, entry)
        if len(matches) < 1:
            if return_string_if_fails: return_list.append(entry)
            else: return_list.append([])
        else:
            numbers = [float(x) for x in matches]
            if reduce_to_integers: numbers = [int(number) for number in numbers if number.is_integer()]
            return_list.append(numbers)

    def flatten_shallow(iterable: list | tuple):
        for item in iterable:
            if isinstance(item, list | tuple): yield from item
            else: yield item

    if not nest: return_list = list(flatten_shallow(return_list))
    return return_list

def get_next_indexed_filename(folder_path, base_name, extension) -> list[str, str]:
    # Pattern to match files with the base name and exactly 3 digits for the index
    # \d{3} matches exactly three digits
    pattern = rf"^{re.escape(base_name)}_(\d{{3}}){re.escape(extension)}$"
    
    # List all files in the directory
    try:
        files = os.listdir(folder_path)
    except FileNotFoundError:
        # If the folder doesn't exist, the first file will be index 000
        return f"{base_name}_000{extension}"

    matching_indices = []
    for filename in files:
        match = re.match(pattern, filename)
        if match: matching_indices.append(int(match.group(1)))

    max_index = 0
    next_index = 0
    if matching_indices:
        # If files were found, find the highest index
        max_index = max(matching_indices)
        next_index = max_index + 1
        
    # Format the next index to be a 3-digit string with leading zeros if necessary
    current_formatted_index = f"{max_index:03d}"
    next_formatted_index = f"{next_index:03d}"
    
    return [f"{base_name}_{current_formatted_index}{extension}", f"{base_name}_{next_formatted_index}{extension}"]

def trace_attributes(obj: object, object_name: str = "", visited = None, depth: int = 0, max_depth: int = 4) -> list:
    if visited is None: visited = set()
    
    if depth > max_depth: return []
    obj_id = id(obj)
    if obj_id in visited: return []
    visited.add(obj_id)
    
    attributes = [object_name] if object_name else []
    obj_cls = obj.__class__
    
    for attribute_name in dir(obj):
        if attribute_name.startswith("_"): continue
        
        try: attribute = getattr(obj, attribute_name)
        except AttributeError: continue

        # Check if the attribute is defined locally (on the instance or the specific class)
        is_instance_attr = hasattr(obj, "__dict__") and attribute_name in obj.__dict__
        is_class_attr = attribute_name in obj_cls.__dict__
        
        # Skip if it's inherited from any parent class
        if not (is_instance_attr or is_class_attr):
            continue

        full_path = f"{object_name}.{attribute_name}" if object_name else attribute_name
        has_dict_or_slots = hasattr(attribute, "__dict__") or hasattr(attribute, "__slots__")
        
        if has_dict_or_slots and not inspect.isroutine(attribute):
            if depth < max_depth:
                subattributes = trace_attributes(attribute, full_path, visited = visited, depth = depth + 1, max_depth = max_depth)
                attributes.extend(subattributes)
            else:
                attributes.append(full_path)
        else:
            attributes.append(full_path)
    return attributes

