import re, os, h5py, inspect
import numpy as np
from datetime import datetime, timezone
from .file_picker import get_file_path_from_dialog



def get_raw_header(file_path: str = "", end_tag: str = ":SCANIT_END:") -> list:
    if not file_path: file_path = get_file_path_from_dialog(extensions = ["sxm"], io = "load")
    if not os.path.isfile(file_path): raise Exception("Invalid file selected.")
    raw_header = []
    
    try:
        with open(file_path, "rb") as file:
            for line in file:
                decoded = line.decode().split()
                
                raw_header.append(decoded)
                if end_tag in decoded: break
    except Exception as e: raise Exception(f"Unable to retrieve raw sxm header: {e}")
    return raw_header

def get_header(file_path: str = "", end_tag: str = ":SCANIT_END:") -> dict:
    raw_header = get_raw_header(file_path, end_tag)
    
    tag_substitutions = {":NANONIS_VERSION:": "version", ":REC_DATE:": "creation_date", ":REC_TIME:": "creation_time", ":REC_TEMP:": "temperature"}

    header_dict = {}
    for index, line in enumerate(raw_header):
        if len(line) < 1 or not isinstance(line[0], str): continue
        
        if line[0] in tag_substitutions.keys():
            value = raw_header[index + 1]
            if len(value) == 1: value = value[0]
            if not isinstance(value, str): continue
            if value.isnumeric(): value = float(value)
            header_dict.update({tag_substitutions[line[0]]: value})

    return header_dict

def read_header_full(self, file_path: str) -> tuple[np.ndarray, dict]:
    try:
        (header_array, sct_dict) = self.read_header(file_path)
        [pixels, lines] = [int(sct_dict.get("grid_size", [1, 1])[i]) for i in range(2)]
        sct_dict.update({"pixels": pixels, "lines": lines})
        
        frame = self.parent.convert_to_sct_frame(sct_dict)
        sct_dict.update({"frame": frame})
    except Exception as e:
        print(f"Problem reading the SXM file header: {e}")
    
    # Z_controller
    try:
        z_controller_index = np.where(header_array == ":Z-CONTROLLER:\n")[0][0]
        z_controller_data = header_array[z_controller_index + 2].split("\t")
        [_, z_controller_name, feedback, setpoint, p_gain, i_gain, t_const] = z_controller_data
        sct_dict.update({"z_controller": {"name": z_controller_name, "feedback": bool(feedback), "setpoint": setpoint, "p_gain": p_gain, "i_gain": i_gain, "t_const": t_const}})
    except Exception as e:
        print(f"Problem retrieving z-controller data from .sxm file: {e}")

    # Channels
    try:
        channel_data_index = np.where(header_array == ":DATA_INFO:\n")[0][0]
        channel_names = []
        for channel_index in range(100):
            channel_data = header_array[channel_data_index + 2 + channel_index].split()
            if len(channel_data) < 1: break
            [channel_index, quantity, unit, direction, calibration, offset] = channel_data
            channel_names.append(" ".join((quantity, f"({unit})")))
        
        sct_dict.update({"channels": channel_names})
    except Exception as e:
        print(f"Problem retrieving channel data from .sxm file: {e}")
    return (header_array, sct_dict)



# Misc
def split_physical_quantity(self, text: str) -> tuple:
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

def get_scientific_numbers(text: str) -> list:
    pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
    matches = re.findall(pattern, text)
    numbers = [float(x) for x in matches]
    return numbers

def get_next_indexed_filename(folder_path, base_name, extension) -> str:
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
