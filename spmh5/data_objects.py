import matplotlib.figure as plt_fig
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from typing import Any, Literal
from collections.abc import Sequence
NPSequence = Sequence | np.ndarray
Numeric = float | int | complex | np.integer | np.floating



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

def complex_plot(array: np.ndarray, figsize: tuple = (4, 4), phase_shift: float = 0., extent: tuple | None = None, origin: Literal["lower", "upper"] = "lower") -> plt_fig.Figure:
    """Convenience function for plotting a complex array

    Args:
        array (np.ndarray): Numpy array
        phase_shift (float, optional): Phase shift. Defaults to 0..
    """
    rgba_array = complex_to_rgba(array, phase_shift = phase_shift)
    fig, ax = plt.subplots(figsize = figsize)
    ax.imshow(rgba_array, extent = extent, origin = origin)
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

    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
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
    [axis.line.set_color(color) for axis, color in zip ([ax.xaxis, ax.yaxis, ax.zaxis], axis_colors)]
    return fig



class CoordinateFrame:
    """Class describing a rectilinear coordinate frame with ranges in the x (and potentially y, z, a) dimensions expressed in its own coordinate system.
    An anchor with the same dimensionality defines rotations (self.angles) and translations (self.offset) with respect to a global coordinate system this frame may be placed in. 
    """
    def __init__(self, x_range: Numeric | NPSequence[Numeric] | None = None, y_range: Numeric | NPSequence[Numeric] | None = None,
                 z_range: Numeric | NPSequence[Numeric] | None = None, a_range: Numeric | NPSequence[Numeric] | None = None,
                 ranges: NPSequence[Numeric] | NPSequence[NPSequence[Numeric]] | None = None,
                 units: str | NPSequence[str] = "nm", offset: Numeric | NPSequence[Numeric] = 0, angles: Numeric | NPSequence[Numeric] = 0, angle_units: Literal["degree", "rad"] = "degree",
                 anchor: NPSequence[Numeric] | Numeric = 0.):
        self.rank: int = 0
        
        self.x_range = None
        self.y_range = None
        self.z_range = None
        self.a_range = None
        self.set_anchor(anchor)
        
        if ranges: self.set_range(ranges)
        if x_range: self.set_range(x_range, axis = 0)
        if y_range: self.set_range(y_range, axis = 1)
        if z_range: self.set_range(z_range, axis = 2)
        if a_range: self.set_range(a_range, axis = 3)
        
        self.set_units(units)
        self.set_offset(offset)
        self.set_angle(angles)
        self.set_angle_units(angle_units)
    
    def __repr__(self) -> str:
        output_str_0 = f"{self.ndim}-dimensional rectilinear frame with ranges "
        ranges_strs = ", ".join([f"[{float(axis_range[0]):.4f} {axis_dim} to {float(axis_range[1]):.4f} {axis_dim}]" for axis_range, axis_dim in zip(self.ranges, self.units)])
        return output_str_0 + ranges_strs


    
    def set_range(self, value: Numeric | NPSequence[Numeric] | NPSequence[NPSequence[Numeric]], axis: int = -1) -> None:
        """self.ranges are expressed in local coordinates (disregarding any offset)
        """
        if isinstance(value, Numeric): value = [-value * self.anchor[axis], value * (1 - self.anchor[axis])]
        if isinstance(value[0], NPSequence): self.ranges = list(value)
        
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
        if not hasattr(self, "units"): self.units = ["" for _ in range(self.rank)]
        if not hasattr(self, "offset"): self.offset = [0 for _ in range(self.rank)]
        if not hasattr(self, "angles"): self.angles = [0 for _ in range(self.rank)]
        return
    
    def set_units(self, value: str | NPSequence[str], axis: int = -1) -> None:
        if isinstance(value, str):
            if axis > -1 and axis < self.rank: self.units[axis] = value
            else: self.units = [value for _ in range(self.rank)]
            return
        if isinstance(value, list | tuple | np.ndarray): self.units = list(value)
        return
    
    def set_offset(self, value: Numeric | NPSequence[Numeric], axis: int = -1) -> None:
        if isinstance(value, Numeric) and axis > -1 and axis < self.rank: self.offset[axis] = value # type: ignore
        if isinstance(value, NPSequence): self.offset = list(value)
        return

    def set_angle(self, value: Numeric | NPSequence[Numeric], axis: int = -1) -> None:
        if isinstance(value, Numeric) and axis > -1 and axis < self.rank: self.angles[axis] = value # type: ignore
        if isinstance(value, NPSequence): self.angles = list(value)
        return
        
    def set_angle_units(self, value: Literal["degree", "rad"]) -> None:
        self.angle_units = value
        return

    def set_anchor(self, anchor: NPSequence[Numeric] | Numeric = 0., axis: int = -1) -> None:
        """self.anchor is expressed in fractional coordinates"""
        if not hasattr(self, "ndim"):
            if isinstance(anchor, Numeric): anchor = [anchor]
            if not isinstance(anchor, NPSequence):
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
    """Container class mirroring h5py.Dataset, with numpy data stored at self.data, along with units (self.units), a name (self.name), and attributes (self.attrs).
    This class can be used outside of the context of HDF5 files.
    """
    def __init__(self, data: list | np.ndarray | None = None, shape: tuple[int] | None = None, dtype: np.dtype | None = None, resizable_axes: int | tuple[int] | None = None, maxshape: tuple[int] | None = None, attrs: dict = {}, units: str = "", name: str = ""):
        self.set_name(name)
        
        if isinstance(data, list):
            if dtype: data = np.array(data, dtype)
            else: data = np.array(data, dtype = np.float32)
        
        if not isinstance(data, np.ndarray):
            if not isinstance(shape, tuple): raise Exception("Neither data nor a shape were passed to Dataset. Dataset cannot be created.")
            if dtype: data = np.empty(shape = shape, dtype = dtype)
            else: data = np.empty(shape = shape, dtype = np.float32)
        
        self.set_data(data)
        self.set_attrs(attrs)
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
        
        self.slice_axis = 0
        self.slice_index = 0

    def __getitem__(self, key) -> np.ndarray:
        return self.data[key]

    def __repr__(self) -> str:
        output_str_0 = f"SPMH5 dataset \"{self.name}\" holding a rank-{self.rank} numpy array of shape {self.shape}, dtype numpy.{self.dtype},"
        output_str_1 = f" with values in the range [{self.min:.4f} {self.units} to {self.max:.4f} {self.units}],"
        output_str_2 = f" and {len(self.attrs)} attributes stored at self.attrs"
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
    
    def set_attrs(self, attrs: dict) -> None:
        self.attrs = attrs
        return
    
    def del_attrs(self) -> None:
        self.attrs = {}
        return
    
    def add_attrs(self, attrs: dict) -> None:
        self.attrs.update(attrs)
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
                self.data_range = self.max - self.min
                return np.nan, np.nan    
        
        if np.issubdtype(arr.dtype, np.inexact) and np.all(np.isnan(arr)):
            self.min = np.nan
            self.max = np.nan
            self.data_range = self.max - self.min
            return np.nan, np.nan

        if np.issubdtype(arr.dtype, np.complexfloating):
            magnitudes = np.abs(arr)
            min_idx_flat = np.nanargmin(magnitudes)
            max_idx_flat = np.nanargmax(magnitudes)
            
            flat_arr = arr.ravel()
            self.min = complex(flat_arr[min_idx_flat])
            self.max = complex(flat_arr[max_idx_flat])
            self.data_range = self.max - self.min
            return self.min, self.max

        else:
            self.min = float(np.nanmin(arr))
            self.max = float(np.nanmax(arr))
            self.data_range = self.max - self.min
            return self.min, self.max

    def is_linear(self, rtol: float = 1e-5, atol: float = 1e-8) -> bool:
        arr = self.data
        if arr.ndim > 1: return False
        
        diffs = np.diff(arr)
        return np.allclose(diffs, diffs[0], rtol = rtol, atol = atol)



    def set_slice_axis(self, axis: int = 0) -> None:
        if axis < self.rank + 1: self.slice_axis = axis
        axis_length = self.shape[self.slice_axis]
        if self.slice_index > axis_length: self.slice_index = axis_length
        return

    def set_slice_index(self, index: int = 0) -> None:
        axis_length = self.shape[self.slice_axis]
        if index < axis_length + 1: self.slice_index = index
        else: raise Exception(f"Cannot set slice index to {index} for axis {self.slice_axis} with length {axis_length}")
        self.slice_index = index
        return

    def get_slice(self, slice_index: int | None = None, slice_axis: int | None = None) -> np.ndarray:
        array = self.data.copy()
        match self.rank:
            case 1: sliced_data = array
            case 2: sliced_data = array
            case 3:
                if isinstance(slice_axis, int): self.set_slice_axis(slice_axis)
                if isinstance(slice_index, int): self.set_slice_index(slice_index)                
                match self.slice_axis:
                    case 0: sliced_data = array[self.slice_index]
                    case 1: sliced_data = array[:, self.slice_index]
                    case 2: sliced_data = array[:, :, self.slice_index]
            case _: raise Exception(f"Cannot slice {self.rank}-dimensional data")
        return sliced_data

    def show_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), data_range: np.ndarray | None = None, cmap: str = "Greys_r",
                  slice_axis: int | None = None, slice_index: int | None = None, phase: float = .3) -> plt_fig.Figure:
        if isinstance(slice_axis, int): self.set_slice_axis(slice_axis)
        if isinstance(slice_index, int): self.set_slice_index(slice_index)
        
        if self.dkind == "complex": fig = self.show_complex_data(data = data, figsize = figsize, data_range = data_range, phase = phase)
        else: fig = self.show_real_data(data = data, figsize = figsize, data_range = data_range, cmap = cmap)
        return fig

    def show_real_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), data_range: np.ndarray | None = None, cmap: str = "Greys_r") -> plt_fig.Figure:
        array = data.copy() if isinstance(data, np.ndarray) else self.data.copy()
        fig, ax = plt.subplots(figsize = figsize)

        match self.rank:
            case 1:
                if isinstance(data_range, np.ndarray):
                    if data_range.ndim == 1: extent = (data_range[0], data_range[1])
                    else: extent = (data_range[0, 0], data_range[0, 1])
                    ax.plot(np.linspace(extent[0], extent[1], num = len(array)), array)
                else: ax.plot(array)
            case 2:
                if isinstance(data_range, np.ndarray):
                    extent = (data_range[0, 0], data_range[0, 1], data_range[1, 0], data_range[1, 1])
                    ax.imshow(array, extent = extent, origin = "lower", cmap = cmap) # type: ignore
                else: ax.imshow(array, origin = "lower", cmap = cmap)            
            case 3:
                data_slice = self.get_slice()
                if isinstance(data_range, np.ndarray):
                    match self.slice_axis:
                        case 0: extent = (data_range[1, 0], data_range[1, 1], data_range[2, 0], data_range[2, 1])
                        case 1: extent = (data_range[0, 0], data_range[0, 1], data_range[2, 0], data_range[2, 1])
                        case 2: extent = (data_range[0, 0], data_range[0, 1], data_range[1, 0], data_range[1, 1])
                    ax.imshow(data_slice, extent = extent, origin = "lower", cmap = cmap)
                else: ax.imshow(data_slice, origin = "lower", cmap = cmap)
            case _:
                raise Exception("I do not know yet how to represent these data")
        return fig

    def show_complex_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), data_range: np.ndarray | None = None, phase: float = .3) -> plt_fig.Figure:
        array = data.copy() if isinstance(data, np.ndarray) else self.data.copy()

        match self.rank:
            case 1:
                fig = plt.figure(figsize = figsize)
                ax = fig.add_subplot(projection = "3d")
                
                if isinstance(data_range, np.ndarray):
                    if data_range.ndim == 1: extent = (data_range[0], data_range[1])
                    else: extent = (data_range[0, 0], data_range[0, 1])
                    x_values = np.linspace(extent[0], extent[1], len(array))
                    ax.plot3D(x_values, np.real(array), np.imag(array))
                else:
                    x_values = np.arange(len(array))
                    ax.plot3D(x_values, np.real(array), np.imag(array))
            case 2:
                fig, ax = plt.subplots(figsize = figsize)                
                if isinstance(data_range, np.ndarray):
                    extent = (data_range[0, 0], data_range[0, 1], data_range[1, 0], data_range[1, 1])
                    fig = complex_plot(array, phase_shift = phase, extent = extent, origin = "lower") # type: ignore
                else:
                    fig = complex_plot(array, phase_shift = phase)
            case 3:
                data_slice = self.get_slice()
                if isinstance(data_range, np.ndarray):
                    match self.slice_axis:
                        case 0: extent = (data_range[1, 0], data_range[1, 1], data_range[2, 0], data_range[2, 1])
                        case 1: extent = (data_range[0, 0], data_range[0, 1], data_range[2, 0], data_range[2, 1])
                        case 2: extent = (data_range[0, 0], data_range[0, 1], data_range[1, 0], data_range[1, 1])
                    fig = complex_plot(data_slice, figsize = figsize, extent = extent, origin = "lower", phase_shift = phase)
                fig = complex_plot(data_slice, figsize = figsize, phase_shift = phase)
            case _:
                raise Exception("I do not know yet how to represent these data")
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
    def __init__(self, dataset: Dataset, axes: list[Dataset] = [], attrs: dict = {}):
        self.set_dataset(dataset)
        self.set_axes(axes)
        self.set_attrs(attrs)
        
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
        
        self.axis_names = [axis.name for axis in self.axes]
        self.axis_units = [axis.units for axis in self.axes]
        self.axis_ranges = [[axis.min, axis.max] for axis in self.axes]
        self.axes_are_linear = all([axis.is_linear() for axis in self.axes])

    def __len__(self) -> int:
        return len(self.axes) + 1

    def __getitem__(self, key) -> Dataset:
        if key == 0: return self.dataset
        else: return self.axes[key - 1]

    def __repr__(self) -> str:
        axis_dataset_names = ", ".join([axis.name for axis in self.axes])
        output_str_0 = f"SPMH5 datagrid \"{self.name}\" holding a rank-{self.rank} numpy array of shape {self.shape}, dtype numpy.{self.dtype},"
        output_str_1 = f" with values in the range [{self.min:.4f} {self.units} to {self.max:.4f} {self.units}],"
        output_str_2 = f" {len(self.attrs)} attributes stored at self.attrs and {len(self.dataset.attrs)} attributes stored at self.dataset.attrs.\n"
        output_str_3 = f"Attached to this datagrid are {len(self.axes)} datasets ({axis_dataset_names}) representing the axes:\n"
        axis_strings = "\n".join(["    " + repr(axis) for axis in self.axes])
        if self.units: return output_str_0 + output_str_1 + output_str_2 + output_str_3 + axis_strings + "\n"
        else: return output_str_0 + output_str_2 + axis_strings + "\n"

    @classmethod
    def from_frame(cls, dataset: Dataset, frame: CoordinateFrame = CoordinateFrame(), axes_names: list[str] = [], include_boundaries: bool | Sequence[bool] = True, attrs: dict = {}) -> Datagrid:
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
        
        return cls(dataset = dataset, axes = axis_ds_list, attrs = attrs)



    def set_dataset(self, dataset: Dataset) -> None:
        self.dataset = dataset
        return
    
    def set_axes(self, axes: list[Dataset]) -> None:
        self.axes = axes
        return
    
    def set_attrs(self, attrs: dict) -> None:
        self.attrs = attrs
        return

    def get_frame(self, anchor: NPSequence | None = None) -> CoordinateFrame:
        if not isinstance(anchor, list | np.ndarray): anchor = np.zeros(shape = len(self.axes))
        else: anchor = np.array(anchor)
        
        if not self.axes_are_linear: print("Warning! Non-linear axes found in Datagrid. The extracted \"frame\" object may be unphysical.")
        frame = CoordinateFrame(ranges = self.axis_ranges, anchor = anchor, units = self.axis_units)
        return frame



    def set_slice_axis(self, axis: int = 0) -> None:
        if axis < self.rank + 1: self.dataset.slice_axis = axis
        axis_length = self.shape[self.dataset.slice_axis]
        if self.dataset.slice_index > axis_length: self.dataset.slice_index = axis_length
        return

    def set_slice_index(self, index: int = 0) -> None:
        axis_length = self.shape[self.dataset.slice_axis]
        if index < axis_length + 1: self.dataset.slice_index = index
        else: raise Exception(f"Cannot set slice index to {index} for axis {self.dataset.slice_axis} with length {axis_length}")
        self.dataset.slice_index = index
        return

    def get_slice(self, slice_index: int | None = None, slice_axis: int | None = None) -> np.ndarray:
        array = self.data.copy()
        match self.rank:
            case 1: sliced_data = array
            case 2: sliced_data = array
            case 3:
                if isinstance(slice_axis, int): self.set_slice_axis(slice_axis)
                if isinstance(slice_index, int): self.set_slice_index(slice_index)                
                match self.dataset.slice_axis:
                    case 0: sliced_data = array[self.dataset.slice_index]
                    case 1: sliced_data = array[:, self.dataset.slice_index]
                    case 2: sliced_data = array[:, :, self.dataset.slice_index]
            case _: raise Exception(f"Cannot slice {self.rank}-dimensional data")
        return sliced_data

    def show_data(self, data: np.ndarray | None = None, figsize: tuple = (8, 6), cmap: str = "Greys_r",
                  slice_axis: int | None = None, slice_index: int | None = None, phase: float = .3) -> plt_fig.Figure:
        if isinstance(slice_axis, int): self.set_slice_axis(slice_axis)
        if isinstance(slice_index, int): self.set_slice_index(slice_index)
        
        fig = self.dataset.show_data(data = data, data_range = np.array(self.axis_ranges), figsize = figsize, cmap = cmap, slice_axis = slice_axis, slice_index = slice_index, phase = phase)
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


