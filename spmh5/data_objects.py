import matplotlib.figure as plt_fig
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from numpy.typing import NDArray
from typing import Any, Literal, TypeVar
from collections.abc import Sequence
Numeric = float | int | complex | np.integer | np.floating
T = TypeVar("T", bound = float | int | complex | np.integer | np.floating)
NPSequence = Sequence[T] | NDArray[T] # type: ignore
NestedNPSequence = Sequence[Sequence[T]] | Sequence[NDArray[T]] | NDArray[T] # type: ignore



def complex_to_rgba(input_array: np.ndarray = np.zeros((2, 2)), phase_shift: float = 0., alpha: float = 1.) -> np.ndarray:
    phase = np.angle(input_array) + phase_shift
    hue = (phase + np.pi) / (2 * np.pi) % 1
    mag = np.abs(input_array)
    
    flat_order = np.argsort(mag, axis = None)
    rows, cols = np.unravel_index(flat_order, mag.shape)
    sorted = np.array(list(zip(rows, cols)))
    maximum = np.sum([mag[sorted[-idx, 0], sorted[-idx, 1]] for idx in range(1, 120)]) / 120
    for idx in range(1, 120): mag[sorted[-idx, 0], sorted[-idx, 1]] = maximum
    
    value = mag / maximum # np.max(mag)
    saturation = np.ones_like(hue)
    hsv = np.stack((hue, saturation, value), axis = -1)
    rgb = np.clip(mcolors.hsv_to_rgb(hsv), 0, 1)
    rgba = np.concatenate((rgb, np.full_like(rgb, alpha)), axis = 2)[:, :, :4]
    return rgba

def complex_plot(array: np.ndarray, figsize: tuple = (4, 4), title: str = "", phase_shift: float = 0., extent: tuple | None = None, origin: Literal["lower", "upper"] = "lower", x_label: str = "", y_label: str = "") -> plt_fig.Figure:
    """Convenience function for plotting a complex array

    Args:
        array (np.ndarray): Numpy array
        phase_shift (float, optional): Phase shift. Defaults to 0..
    """
    rgba_array = complex_to_rgba(array, phase_shift = phase_shift)
    fig, ax = plt.subplots(figsize = figsize)
    if title: ax.set_title(title)
    ax.imshow(rgba_array.T, extent = extent, origin = origin)
    if x_label: ax.set_xlabel(x_label)
    if y_label: ax.set_ylabel(y_label)
    return fig

def represent_as_cube(array: np.ndarray | None = None, ranges: np.ndarray | None = None, axis_names: list[str] = ["x", "y", "z"], axis_units: list[str] = ["", "", ""], anchor: np.ndarray | None = None,
                      title: str = "", figsize = (4, 4),
                      background_color: str = "#000000", axis_colors: list[str] = ["#ffff00", "#00ffff", "#ff00ff"], edge_color: str = "#ffffff", anchor_color: str = "#a0a0a0") -> plt_fig.Figure:    
    fig = plt.figure(figsize = figsize, facecolor = background_color)
    ax = fig.add_subplot(111, projection = "3d", facecolor = background_color)
    if title: ax.set_title(title)

    unit_vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
    if not isinstance(ranges, np.ndarray): ranges = np.array([[0, 1], [0, 1], [0, 1]])

    mins = ranges[:, 0]
    scales = ranges[:, 1] - ranges[:, 0]
    vertices = unit_vertices * scales + mins
    faces = [[vertices[index] for index in face_indices] for face_indices in [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]]

    if isinstance(array, np.ndarray):
        match array.dtype.kind:
            case "c": face_color = "#ffa070"
            case "f": face_color = "#89b4fa"
            case "i": face_color = "#a0a0a0"
            case _: face_color = "#f0a0f0"
    else:
        face_color = "#000000"
    for face in faces:
        ax.plot_surface(np.array([[face[0][0], face[1][0]], [face[3][0], face[2][0]]]),
                        np.array([[face[0][1], face[1][1]], [face[3][1], face[2][1]]]),
                        np.array([[face[0][2], face[1][2]], [face[3][2], face[2][2]]]),
                        color = face_color, edgecolor = edge_color, linewidth = 2, alpha = 0.6)

    ax.xaxis.pane.fill = False # type: ignore
    ax.yaxis.pane.fill = False # type: ignore
    ax.zaxis.pane.fill = False
    
    # Anchor location is understood to be in fractional coordinates
    if isinstance(anchor, np.ndarray):
        anchor_cartesian = [anchor[dim] * ranges[dim, 1] + (1 - anchor[dim]) * ranges[dim, 0] for dim in range(3)]
        ax.scatter(anchor_cartesian[0], anchor_cartesian[1], anchor_cartesian[2], marker = "+", color = anchor_color, s = 300, linewidths = 3.5, zorder = 100)

    # Color ticks, labels, and axis lines individually
    ax.tick_params(colors = "#ffffff", which = "both", labelsize = 10)
    
    axes_labels = [f"{name} ({unit})" if unit else f"{name}" for name, unit in zip(axis_names, axis_units)]

    ax.set_xlabel(axes_labels[0], color = axis_colors[0], labelpad = 10, fontsize = 12)
    ax.set_ylabel(axes_labels[1], color = axis_colors[1], labelpad = 10, fontsize = 12)
    ax.set_zlabel(axes_labels[2], color = axis_colors[2], labelpad = 10, fontsize = 12)
    ax.invert_xaxis()
    
    #ax.text(0, 1.5, 0, f"dtype: {array.dtype}", color = "#ffffff")
    [axis.line.set_color(color) for axis, color in zip ([ax.xaxis, ax.yaxis, ax.zaxis], axis_colors)] # type: ignore
    return fig



class CoordinateFrame:
    """Class describing a rectilinear coordinate frame with ranges in the x (and potentially y, z, a) dimensions expressed in its own coordinate system.
    An anchor expressed in fractional coordinates (self.anchor) defines the origin of the local coordinate system around which rotations (self.angles) and translations (self.offset) are defined relative to a global coordinate system this frame may be placed in. 
    """
    def __init__(self, x_range: Numeric | NPSequence | None = None, y_range: Numeric | NPSequence | None = None,
                 z_range: Numeric | NPSequence | None = None, a_range: Numeric | NPSequence | None = None,
                 ranges: NPSequence | None = None,
                 units: str | list[str] = "nm", offset: Numeric | NPSequence = 0, angles: Numeric | NPSequence = 0, angle_units: Literal["degree", "rad"] = "degree",
                 anchor: NPSequence | Numeric = 0.):
        self.rank: int = 0
        
        self.x_range = None
        self.y_range = None
        self.z_range = None
        self.a_range = None
        
        if ranges: self.set_range(ranges, anchor = anchor)
        if x_range: self.set_range(x_range, axis = 0, anchor = anchor)
        if y_range: self.set_range(y_range, axis = 1, anchor = anchor)
        if z_range: self.set_range(z_range, axis = 2, anchor = anchor)
        if a_range: self.set_range(a_range, axis = 3, anchor = anchor)
        
        self.setup_transformation_attributes()
        self.set_angle_units(angle_units)
        
        self.set_units(units)
        self.set_offset(offset)
        self.set_angle(angles)
        self.set_anchor(anchor)

    def __repr__(self) -> str:
        output_str_0 = f"{self.ndim}-dimensional rectilinear frame with ranges "
        ranges_strs = ", ".join([f"[{float(axis_range[0]):.4f} {axis_dim} to {float(axis_range[1]):.4f} {axis_dim}]" for axis_range, axis_dim in zip(self.ranges, self.units)])
        return output_str_0 + ranges_strs



    def set_range(self, value: Numeric | NPSequence | NestedNPSequence, axis: int = -1, anchor: NPSequence | Numeric | None = None) -> None:
        """self.ranges are expressed in local coordinates (disregarding any offset)
        """
        if isinstance(value, Numeric):
            if isinstance(anchor, Numeric): value = [-value * anchor, value * (1 - anchor)]
            elif isinstance(anchor, list | tuple | np.ndarray) and len(anchor) > axis: value = [-value * anchor[axis], value * (1 - anchor[axis])]
            elif hasattr(self, "nachor") and isinstance(self.anchor, list | tuple | np.ndarray) and len(self.anchor) > axis: value = [-value * self.anchor[axis], value * (1 - self.anchor[axis])]
            else: value = [0, value]
        if isinstance(value[0], list | tuple | np.ndarray): self.ranges = list(value)
        
        if isinstance(value[0], Numeric):
            if hasattr(self, "ranges") and axis > -1:
                assert isinstance(self.ranges, list)
                if axis > len(self.ranges) - 1: self.ranges.append([value[0], value[1]]) # type: ignore
                else: self.ranges[axis] = [value[0], value[1]]
            else: self.ranges = [[value[0], value[1]]]
        
        if not hasattr(self, "ranges"): return
        for dim, values in enumerate(self.ranges):
            if dim == 0: self.x_range = values
            if dim == 1: self.y_range = values
            if dim == 2: self.z_range = values
            if dim == 3: self.a_range = values
        
        self.rank = len(self.ranges)
        self.ndim = self.rank
        return

    def setup_transformation_attributes(self):
        if not hasattr(self, "units"): self.units = ["" for _ in range(self.rank)]
        if not hasattr(self, "offset"): self.offset = [0 for _ in range(self.rank)]
        if not hasattr(self, "angles"): self.angles = [0 for _ in range(self.rank * (self.rank - 1))]
        if not hasattr(self, "anchor"): self.anchor = [0 for _ in range(self.rank)]
        return

    def set_units(self, value: str | list[str], axis: int = -1) -> None:
        if isinstance(value, str):
            if axis > -1 and axis < self.rank: self.units[axis] = value
            else: self.units = [value for _ in range(self.rank)]
            return
        if isinstance(value, list | tuple | np.ndarray): self.units = list(value)
        return
    
    def set_offset(self, value: Numeric | NPSequence, axis: int = -1) -> None:
        if isinstance(value, Numeric) and axis > -1 and axis < self.rank: self.offset[axis] = value # type: ignore
        if isinstance(value, list | tuple | np.ndarray): self.offset = list(value)
        return

    def set_angle(self, value: Numeric | NPSequence, axis: int = -1) -> None:
        if isinstance(value, Numeric) and axis > -1 and axis < self.rank * (self.rank - 1): self.angles[axis] = value # type: ignore
        if isinstance(value, list | tuple | np.ndarray): self.angles = list(value)
        return
        
    def set_angle_units(self, value: Literal["degree", "rad"]) -> None:
        self.angle_units = value
        return

    def set_anchor(self, anchor: NPSequence | Numeric = 0., axis: int = -1) -> None:
        """self.anchor is expressed in fractional coordinates"""
        if not hasattr(self, "ndim"):
            if isinstance(anchor, Numeric): anchor = [anchor]
            if not isinstance(anchor, list | tuple | np.ndarray):
                raise Exception(f"Invalid type {type(anchor)} for anchor passed to CoordinateFrame. The anchor is supposed to represent the rotation/translation point of the frame in fractional coordinates.")
            self.anchor = np.array(anchor)
            self.ndim = self.anchor.ndim
        elif isinstance(anchor, Numeric):
            self.anchor = np.zeros(shape = self.ndim)
            if axis < 0: self.anchor[0] = anchor
            else: self.anchor[axis] = anchor
        else:
            self.anchor = np.zeros(shape = self.ndim)
            self.anchor[:len(anchor)] = anchor
        return

    def visualize(self) -> plt_fig.Figure:
        match self.rank:
            case 3:
                fig = represent_as_cube(title = repr(self), ranges = np.array(self.ranges), axis_names = [f"axis[{index}]" for index in range(len(self.ranges))],
                                        axis_units = self.units, anchor = np.array(self.anchor), edge_color = "#ff0000")
            case _:
                raise Exception(f"Visualize is not yet implemented for {self.rank}-dimensional CoordinateFrame objects")
        return fig



class Dataset:
    """Container class mirroring h5py.Dataset, with numpy data stored at self.data, along with units (self.units), a name (self.name), and attributes (self.attributes).
    This class can be used outside of the context of HDF5 files.
    """
    def __init__(self, name: str = "", units: str = "", data: list | np.ndarray | None = None, shape: tuple[int] | None = None, dtype: np.dtype | None = None,
                 resizable_axes: int | tuple[int] | None = None, maxshape: tuple[int] | None = None, slice_axes: tuple | list | None = None, slice_indices: tuple | list | None = None, attributes: dict = {}):
        self.set_name(name)
        
        if isinstance(data, list):
            if dtype: data = np.array(data, dtype)
            else: data = np.array(data, dtype = np.float32)
        
        if not isinstance(data, np.ndarray):
            if not isinstance(shape, tuple): raise Exception("Neither data nor a shape were passed to Dataset. Dataset cannot be created.")
            if dtype: data = np.empty(shape = shape, dtype = dtype)
            else: data = np.empty(shape = shape, dtype = np.float32)
        
        self.set_data(data)
        self.set_attributes(attributes)
        self.set_units(units)
        
        self.shape = self.data.shape
        self.rank = self.data.ndim
        self.ndim = self.rank
        self.dtype = self.data.dtype
        self.resizable_axes = resizable_axes
        self.maxshape = maxshape
        
        match self.dtype.kind:
            case "i": self.dkind = "integer"
            case "c": self.dkind = "complex"
            case "f": self.dkind = "real"
            case _: self.dkind = "unknown"
        self.get_data_range()
        
        self.slice_axes = [index for index in range(self.rank - 2)]
        self.slice_indices = [0 for _ in range(self.rank - 2)]
        self.remaining_axes = []
        
        self.set_slice(slice_axes, slice_indices)        

    def __getitem__(self, key) -> np.ndarray:
        return self.data[key]

    def __repr__(self) -> str:
        output_str_0 = f"SPMH5 dataset \"{self.name}\" holding a rank-{self.rank} numpy array of shape {self.shape}, dtype numpy.{self.dtype},"
        output_str_1 = f" with values in the range [{self.min:.4f} {self.units} to {self.max:.4f} {self.units}],"
        output_str_2 = f" and {len(self.attributes)} attributes stored at self.attributes"
        if self.units: return output_str_0 + output_str_1 + output_str_2
        else: return output_str_0 + output_str_2



    def set_name(self, name: str) -> None:
        self.name = name
        return
    
    def set_data(self, data: list | np.ndarray) -> None:
        if isinstance(data, list): self.data = np.array(data)
        else: self.data = data
        return
    
    def del_data(self) -> None:
        self.data = np.empty((0,), dtype = np.float32)
        return
    
    def set_attributes(self, attributes: dict) -> None:
        self.attributes = attributes
        return
    
    def del_attributes(self) -> None:
        self.attributes = {}
        return
    
    def add_attributes(self, attributes: dict) -> None:
        self.attributes.update(attributes)
        return
    
    def set_units(self, units: str) -> None:
        self.units = units

    def get_data_range(self) -> tuple[float, float] | tuple[complex, complex] | tuple[np.dtypes.VoidDType, np.dtypes.VoidDType]:
        arr = np.asarray(self.data)
        
        if arr.dtype.kind in {'U', 'S', 'O'}:
            try:
                if any('j' in str(x).lower() for x in arr.ravel()):
                    arr = arr.astype(np.complex128)
                else:
                    arr = arr.astype(np.float64)
            except ValueError as e:
                self.min = np.nan
                self.max = np.nan
                self.data_range = [self.min, self.max]
                return np.nan, np.nan    
        
        if np.issubdtype(arr.dtype, np.inexact) and np.all(np.isnan(arr)):
            self.min = np.nan
            self.max = np.nan
            self.data_range = [self.min, self.max]
            return np.nan, np.nan

        if np.issubdtype(arr.dtype, np.complexfloating):
            magnitudes = np.abs(arr)
            min_idx_flat = np.nanargmin(magnitudes)
            max_idx_flat = np.nanargmax(magnitudes)
            
            flat_arr = arr.ravel()
            self.min = complex(flat_arr[min_idx_flat])
            self.max = complex(flat_arr[max_idx_flat])
            self.data_range = [self.min, self.max]
            return [self.min, self.max]

        else:
            self.min = float(np.nanmin(arr))
            self.max = float(np.nanmax(arr))
            self.data_range = [self.min, self.max]
            return [self.min, self.max]

    def is_linear(self, rtol: float = 1e-5, atol: float = 1e-8) -> bool:
        arr = self.data
        if arr.ndim > 1: return False
        
        try: diffs = np.diff(arr)
        except: return False # If the data is non-numeric, it is also not linear
        return np.allclose(diffs, diffs[0], rtol = rtol, atol = atol)



    def set_slice(self, slice_axes: int | tuple | list | np.ndarray | None = None, indices: int | tuple | list | np.ndarray | None = None) -> None:
        self.set_slice_axes(slice_axes)
        self.set_slice_indices(indices)
        return

    def set_slice_axes(self, axes: int | tuple | list | np.ndarray | None = None) -> None:
        if isinstance(axes, int): axes = [axes]
        if not isinstance(axes, tuple | list | np.ndarray): return
        
        if not len(axes) == len(self.slice_axes):
            print(f"Warning: invalid slice axes. Axes {axes} on rank-{self.rank} dataset will not generate a 2D slice.")
        if np.any(np.array(axes)) > self.rank - 1:
            print(f"Warning: invalid slice axes. Axes {axes} exceed the rank ({self.rank}) of the dataset.")
        
        self.slice_axes = list(axes)
        for axis_index, axis in enumerate(axes): # Reset the slice indices if they extend past the dataset end in the new slice orientation
            axis_length = self.shape[axis]
            if self.slice_indices[axis_index] > axis_length - 1: self.slice_indices = [0 for _ in range(self.rank - 2)]
    
        self.remaining_axes = [axis_index for axis_index in range(self.rank) if not axis_index in self.slice_axes]
        return

    def set_slice_indices(self, indices: int | tuple | list | np.ndarray | None = None) -> None:
        if isinstance(indices, int): indices = (indices,)
        if not isinstance(indices, tuple | list | np.ndarray): return
        
        if not len(indices) == len(self.slice_axes):
            print(f"Warning: invalid number ({len(indices)}) of slice indices. Expected {len(self.slice_indices)}.")
        
        self.slice_indices = list(indices)
        for axis, index in zip(self.slice_axes, self.slice_indices):
            axis_length = self.shape[axis]
            if index > axis_length - 1:
                print(f"Cannot set slice index to {index} for axis {axis} with length {axis_length}")
                self.slice_indices = [0 for _ in range(len(self.slice_indices))]
                break
        return

    def get_slice(self, data: np.ndarray | None = None, slice_axes: int | tuple | list | None = None, indices: int | tuple | list | None = None, transpose: bool = False) -> tuple[np.ndarray, dict[str, object]]:
        if isinstance(slice_axes, int): slice_axes = (slice_axes,)
        if isinstance(indices, int): indices = (indices,)
        
        if not isinstance(indices, tuple | list): indices = self.slice_indices
        if not isinstance(slice_axes, tuple | list): slice_axes = self.slice_axes
        if not isinstance(data, np.ndarray): data = self.data.copy()
        
        remaining_axes = []
        match data.ndim:
            case 1:
                sliced_data = data
            case 2:
                sliced_data = data
            case _:
                slice_list = [slice(None) for _ in range(self.rank)]
                for axis, index in zip(slice_axes, indices):
                    slice_list[axis] = index
                sliced_data = data[tuple(slice_list)]
                
                remaining_axes = [axis_index for axis_index in range(data.ndim) if not axis_index in slice_axes]
        
        if transpose:
            sliced_data = sliced_data.transpose()
            remaining_axes.reverse()
        
        slice_info = {"slice_axes": slice_axes, "slice_indices": indices, "remaining_axes": remaining_axes}
        return sliced_data, slice_info

    def show_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), title: str = "", x_range: list | tuple | np.ndarray | None = None, y_range: list | tuple | np.ndarray | None = None,
                  cmap: str = "Greys_r", transpose: bool = False, slice_axes: tuple | list | None = None, indices: tuple | list | None = None, phase: float = .3, x_label: str = "", y_label: str = "") -> plt_fig.Figure:
        data_slice, slice_info = self.get_slice(data, slice_axes, indices, transpose)
        
        if self.dkind == "complex": fig = self.show_complex_data(data = data_slice, figsize = figsize, title = title, x_range = x_range, y_range = y_range, phase = phase, x_label = x_label, y_label = y_label)
        else: fig = self.show_real_data(data = data_slice, figsize = figsize, title = title, x_range = x_range, y_range = y_range, cmap = cmap, x_label = x_label, y_label = y_label)
        return fig

    def show_real_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), title: str = "", x_range: list | tuple | np.ndarray | None = None, y_range: list | tuple | np.ndarray | None = None,
                       cmap: str = "Greys_r", x_label: str = "", y_label: str = "") -> plt_fig.Figure:
        array = data.copy() if isinstance(data, np.ndarray) else self.data.copy()
        fig, ax = plt.subplots(figsize = figsize)
        ax.set_title(title)
        
        if isinstance(x_range, tuple | list): x_range = np.array(x_range)
        if isinstance(y_range, tuple | list): y_range = np.array(y_range)
        if not (x_range.dtype.kind in ("f", "i", "u") and np.isfinite(x_range).all()): x_range = None
        if not (y_range.dtype.kind in ("f", "i", "u") and np.isfinite(y_range).all()): y_range = None
        if isinstance(x_range, np.ndarray): x_values = np.linspace(x_range[0], x_range[1], array.shape[0])
        else: x_values = np.arange(array.shape[0])

        match array.ndim:
            case 1:
                ax.plot(x_values, array)
                ax.set_xlabel(x_label)
            case 2:
                if isinstance(y_range, np.ndarray): y_values = np.linspace(y_range[0], y_range[1], array.shape[1])
                else: y_values = np.arange(array.shape[1])
                #ax.imshow(array.T, extent = (x_range[0], x_range[1], y_range[0], y_range[1]), origin = "lower", cmap = cmap)
                ax.pcolormesh(x_values, y_values, array.T, cmap = cmap, shading = "nearest")
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
            case _:
                raise Exception(f"Rank-{array.ndim} data array cannot be shown")
        return fig

    def show_complex_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), title: str = "", x_range: list | tuple | np.ndarray | None = None, y_range: list | tuple | np.ndarray | None = None,
                          phase: float = .3, x_label: str = "", y_label: str = "") -> plt_fig.Figure:
        array = data.copy() if isinstance(data, np.ndarray) else self.data.copy()

        if isinstance(x_range, tuple | list): x_range = np.array(x_range)
        if isinstance(y_range, tuple | list): y_range = np.array(y_range)
        if not (x_range.dtype.kind in ("f", "i", "u") and np.isfinite(x_range).all()): x_range = None
        if not (y_range.dtype.kind in ("f", "i", "u") and np.isfinite(y_range).all()): y_range = None
        if isinstance(x_range, np.ndarray): x_values = np.linspace(x_range[0], x_range[1], array.shape[0])
        else: x_values = np.arange(array.shape[0])

        match array.ndim:
            case 1:
                fig = plt.figure(figsize = figsize)
                ax = fig.add_subplot(projection = "3d")
                ax.set_title(title)
                ax.set_xlabel(x_label)
                ax.plot3D(x_values, np.real(array), np.imag(array))
            case 2:              
                if isinstance(y_range, np.ndarray): y_values = np.linspace(y_range[0], y_range[1], array.shape[1])
                else: y_values = np.arange(array.shape[1])
                fig = complex_plot(array, title = title, figsize = figsize, phase_shift = phase, extent = (x_values[0], x_values[-1], y_values[0], y_values[-1]), origin = "lower", x_label = x_label, y_label = y_label) # type: ignore
            case _:
                raise Exception(f"Rank-{array.ndim} data array cannot be shown")
        return fig

    def visualize(self) -> plt_fig.Figure:
        title = f"SPMH5 Dataset \"{self.name}\" holding a {self.dkind}-valued numpy array\nwith values in the range [{self.min:.4f} {self.units} to {self.max:.4f} {self.units}]"
        match self.rank:
            case 3:
                fig = represent_as_cube(title = title, array = self.data, ranges = np.array([[0, 0, 0], list(self.shape)]).T,
                                        axis_names = [f"axis[{index}] [{self.shape[index]} pts]" for index in range(3)], edge_color = "#ffffff")
            case _:
                raise Exception(f"Visualize is not yet implemented for {self.rank}-dimensional Dataset objects")
        return fig



class Datagrid:
    """Compound class containing several Dataset objects. One Dataset object is the \"main\" dataset, and can be n-dimensional. Its name, units, shape, etc. can be retrieved at the top level.
    Attached to the axes of the main dataset are ancillary datasets. These are stored in a list as self.axes. The data of the individual ancillary datasets can be retrieved by selecting the axis from self.axes.
    """
    def __init__(self, dataset: Dataset, axes: list[Dataset] = [], anchor: np.ndarray | list | tuple | None = None, angles: np.ndarray | list | tuple | None = None,
                 angle_units: Literal["degree", "rad"] = "degree", offset: np.ndarray | list | tuple | None = None, attributes: dict = {}):
        self.set_dataset(dataset)
        self.set_axes(axes)
        self.set_attributes(attributes)
        
        # Inherit attributes from the main dataset (create aliases)
        self.name = self.dataset.name
        self.units = self.dataset.units
        self.shape = self.dataset.shape
        self.rank = self.dataset.rank
        self.dtype = self.dataset.dtype
        self.ndim = self.rank
        self.data_range = self.dataset.data_range
        self.data = self.dataset.data
        self.min = self.dataset.min
        self.max = self.dataset.max
        
        self.slice_axes = self.dataset.slice_axes
        self.slice_indices = self.dataset.slice_indices        
        self.remaining_axes = self.dataset.remaining_axes
        
        # Attributes from the axes
        self.axis_names = [axis.name for axis in self.axes]
        self.axis_units = [axis.units for axis in self.axes]
        self.axis_ranges = [[axis.min, axis.max] for axis in self.axes]
        self.axes_are_linear = all([axis.is_linear() for axis in self.axes])
        
        # Attributes to map between local and global coordinates
        self.anchor = [0 for _ in range(len(self.axes))]
        self.angles = [0 for _ in range(len(self.axes) * (len(self.axes) - 1))]
        self.angle_units = "degree"
        self.offset = [0 for _ in range(len(self.axes))]
        
        self.set_anchor(anchor)
        self.set_angles(angles)
        self.set_offset(offset)
        self.set_angle_units(angle_units)        

    def __len__(self) -> int:
        return len(self.axes) + 1

    def __getitem__(self, key) -> Dataset:
        if key == 0: return self.dataset
        else: return self.axes[key - 1]

    def __repr__(self) -> str:
        axis_dataset_names = ", ".join([axis.name for axis in self.axes])
        output_str_0 = f"SPMH5 datagrid \"{self.name}\" holding a rank-{self.rank} numpy array of shape {self.shape}, dtype numpy.{self.dtype},"
        output_str_1 = f" with values in the range [{self.min:.4f} {self.units} to {self.max:.4f} {self.units}],"
        output_str_2 = f" {len(self.attributes)} attributes stored at self.attributes and {len(self.dataset.attributes)} attributes stored at self.dataset.attributes.\n"
        output_str_3 = f"Attached to this datagrid are {len(self.axes)} datasets ({axis_dataset_names}) representing the axes:\n"
        axis_strings = "\n".join(["    " + repr(axis) for axis in self.axes])
        if self.units: return output_str_0 + output_str_1 + output_str_2 + output_str_3 + axis_strings + "\n"
        else: return output_str_0 + output_str_2 + axis_strings + "\n"

    @classmethod
    def from_frame(cls, dataset: Dataset, frame: CoordinateFrame = CoordinateFrame(), axes_names: list[str] = [], include_boundaries: bool | Sequence[bool] = True, attributes: dict = {}) -> Datagrid:
        dset_shape = dataset.shape
        axis_ds_list = []
        
        if not isinstance(include_boundaries, Sequence): include_boundaries = [include_boundaries for _ in range(len(dset_shape))]
        
        for dim, (points, limits, units, name, include_boundary) in enumerate(zip(dset_shape, frame.ranges, frame.units, axes_names, include_boundaries)):
            if include_boundary:
                values = np.linspace(limits[0], limits[1], points)
            else:
                point_size = (limits[1] - limits[0]) / points
                values = np.linspace(limits[0] + point_size / 2, limits[1] - point_size / 2, points)        
            axis_ds_list.append(Dataset(data = values, name = name, units = units))

        return cls(dataset = dataset, axes = axis_ds_list, anchor = frame.anchor, angles = frame.angles, angle_units = frame.angle_units, offset = frame.offset, attributes = attributes)



    # Datasets and axes
    def set_dataset(self, dataset: Dataset) -> None:
        self.dataset = dataset
        return
    
    def set_axes(self, axes: list[Dataset]) -> None:
        self.axes = axes
        return
    
    def set_attributes(self, attributes: dict) -> None:
        self.attributes = attributes
        return

    def get_frame(self, anchor: NPSequence | None = None) -> CoordinateFrame:
        if not isinstance(anchor, list | np.ndarray): anchor = np.zeros(shape = len(self.axes))
        else: anchor = np.array(anchor)
        
        if not self.axes_are_linear: print("Warning! Non-linear axes found in Datagrid. The extracted \"frame\" object may be unphysical.")
        frame = CoordinateFrame(ranges = self.axis_ranges, anchor = anchor, units = self.axis_units)
        return frame



    # Mapping between local and global coordinates
    def set_anchor(self, anchor: tuple | list | np.ndarray | None = None) -> None:
        if not isinstance(anchor, tuple | list | np.ndarray): return
        if not len(anchor) == len(self.anchor): return
        self.anchor = list(anchor)
        return

    def set_offset(self, offset: tuple | list | np.ndarray | None = None) -> None:
        if not isinstance(offset, tuple | list | np.ndarray): return
        if not len(offset) == len(self.offset): return
        self.offset = list(offset)
        return

    def set_angles(self, angles: tuple | list | np.ndarray | None = None) -> None:
        if not isinstance(angles, tuple | list | np.ndarray): return
        if not len(angles) == len(self.angles): return
        self.angles = list(angles)
        return

    def set_angle_units(self, angle_units: Literal["degree", "rad"] = "degree") -> None:
        self.angle_units = angle_units
        return



    # Slicing and data extraction hooks
    def set_slice(self, slice_axes: int | tuple | list | None = None, indices: int | tuple | list | None = None) -> None:
        self.dataset.set_slice(slice_axes, indices)
        self.slice_axes = self.dataset.slice_axes
        self.slice_indices = self.dataset.slice_indices
        self.remaining_axes = self.dataset.remaining_axes
        return

    def set_slice_axes(self, axes: int | tuple | list | None = None) -> None:
        self.dataset.set_slice_axes(axes)
        self.slice_axes = self.dataset.slice_axes
        self.slice_indices = self.dataset.slice_indices
        self.remaining_axes = self.dataset.remaining_axes
        return

    def set_slice_indices(self, indices: int | tuple | list | None = None) -> None:
        self.dataset.set_slice_indices(indices)
        self.slice_axes = self.dataset.slice_axes
        self.slice_indices = self.dataset.slice_indices
        self.remaining_axes = self.dataset.remaining_axes
        return

    def get_slice(self, data: np.ndarray | None = None, slice_axes: int | tuple | list | None = None, indices: int | tuple | list | None = None, transpose: bool = False) -> tuple[np.ndarray, dict[str, object]]:
        if isinstance(slice_axes, int): slice_axes = (slice_axes,)
        if isinstance(indices, int): indices = (indices,)
        
        if not isinstance(slice_axes, tuple | list): slice_axes = self.slice_axes
        if not isinstance(indices, tuple | list): indices = self.slice_indices
        
        slice_data, slice_info = self.dataset.get_slice(data, slice_axes, indices)
        remaining_axes = slice_info.get("remaining_axes")
        assert isinstance(remaining_axes, list)
        
        slice_axis_names = []
        slice_axis_values = []
        slice_axis_units = []
        
        for axis, index in zip(slice_axes, indices):
            axis_ds: Dataset = self.axes[axis]
            slice_axis_values.append(axis_ds.data[index])
            slice_axis_names.append(axis_ds.name)
            slice_axis_units.append(axis_ds.units)
        slice_axis_values = [entry.decode("utf-8") if isinstance(entry, bytes) else entry for entry in slice_axis_values]
        
        new_slice_info = {"slice_axes": slice_axis_names, "slice_indices": list(indices), "slice_values": slice_axis_values, "slice_units": slice_axis_units}
        
        if transpose:
            slice_data = slice_data.transpose()
            remaining_axes = remaining_axes
            remaining_axes.reverse()
        
        for index, axis in enumerate(remaining_axes):
            axis_ds: Dataset = self.axes[axis]
            axis_name = axis_ds.name
            axis_units = axis_ds.units
            axis_range = axis_ds.data_range

            if index == 0: new_slice_info.update({"x_axis_name": axis_name, "x_axis_units": axis_units, "x_axis_range": axis_range}) # type: ignore
            else: new_slice_info.update({"y_axis_name": axis_name, "y_axis_units": axis_units, "y_axis_range": axis_range}) # type: ignore
        
        return slice_data, new_slice_info # type: ignore

    def show_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), cmap: str = "Greys_r", transpose: bool = False,
                  slice_axes: tuple | list | None = None, indices: tuple | list | None = None, phase: float = .3, x_label: str = "", y_label: str = "") -> plt_fig.Figure:
        slice_data, slice_info = self.get_slice(data, slice_axes = slice_axes, indices = indices, transpose = transpose)
        
        x_units = slice_info.get("x_axis_units")
        y_units = slice_info.get("y_axis_units")
        x_label = f"{slice_info.get("x_axis_name", "")} ({x_units})" if x_units else f"{slice_info.get("x_axis_name", "")}"
        y_label = f"{slice_info.get("y_axis_name", "")} ({y_units})" if y_units else f"{slice_info.get("y_axis_name", "")}"
        x_range = slice_info.get("x_axis_range", None)
        y_range = slice_info.get("y_axis_range", None)
        
        [axes, values, units] = [slice_info.get(key, "") for key in ["slice_axes", "slice_values", "slice_units"]]        
        if isinstance(axes, list) and isinstance(values, list) and isinstance(units, list): title = f"data slice at (" + "".join([f"{name} = {value} {unit})" for name, value, unit in zip(axes, values, units)]) 
        
        fig = self.dataset.show_data(data = data, slice_axes = slice_axes, indices = indices, x_range = x_range, y_range = y_range, figsize = figsize, title = title, cmap = cmap, transpose = transpose, phase = phase, x_label = x_label, y_label = y_label)
        return fig

    def visualize(self) -> plt_fig.Figure:
        title_0 = f"SPMH5 Datagrid \"{self.name}\" holding a {self.dataset.dkind}-valued numpy array of shape {self.shape}\nwith values in the range [{self.min:.4f} {self.units} to {self.max:.4f} {self.units}]\n"
        title_1 = f"and {len(self.axes)} axis datasets"
        match self.rank:
            case 3:
                fig = represent_as_cube(title = title_0 + title_1, array = self.dataset.data, ranges = np.array(self.axis_ranges),
                                        axis_names = self.axis_names, axis_units = self.axis_units, edge_color = "#ffffff")
            case _:
                raise Exception(f"Visualize is not yet implemented for {self.rank}-dimensional Dataset objects")
        return fig

