import numpy as np
from typing import Any, Literal
from collections.abc import Sequence
Numeric = float | int | complex | np.integer | np.floating



class CoordinateFrame:
    def __init__(self, x_range: Numeric | Sequence[Numeric] | None = 10, y_range: Numeric | Sequence[Numeric] | None = 10, z_range: Numeric | Sequence[Numeric] | None = None,
                 ranges: Sequence[Numeric] | Sequence[Sequence[Numeric]] | None = None, units: str | Sequence[str] = "nm", offset: Numeric | Sequence[Numeric] = 0, angles: Numeric | Sequence[Numeric] = 0, angle_units: Literal["degree", "rad"] = "degree"):
        self.rank: int = 0
        
        if ranges: self.set_range(ranges)
        if x_range: self.set_range(x_range, axis = 0)
        if y_range: self.set_range(y_range, axis = 1)
        if z_range: self.set_range(z_range, axis = 2)
        
        self.set_units(units)
        self.set_offset(offset)
        self.set_angle(angles)
        self.set_angle_units(angle_units)
    
    def set_range(self, value: Numeric | Sequence[Numeric] | Sequence[Sequence[Numeric]], axis: int = -1) -> None:
        if isinstance(value, Numeric): value = [-.5 * value, .5 * value]
        if isinstance(value[0], Sequence): self.ranges = list(value)
        
        if isinstance(value[0], Numeric):
            if hasattr(self, "ranges") and axis > -1:
                assert isinstance(self.ranges, list)
                if axis > len(self.ranges) - 1: self.ranges.append([value[0], value[1]]) # type: ignore
                else: self.ranges[axis] = [value[0], value[1]]
            else: self.ranges = [[value[0], value[1]]]
        
        self.x_range = None
        self.y_range = None
        self.z_range = None
        if not hasattr(self, "ranges"): return
        for dim, values in enumerate(self.ranges):
            if dim == 0: self.x_range = values
            if dim == 1: self.y_range = values
            if dim == 2: self.z_range = values
        
        self.rank = len(self.ranges)
        self.ndim = self.rank
        if not hasattr(self, "units"): self.units = ["" for _ in range(self.rank)]
        if not hasattr(self, "offset"): self.offset = [0 for _ in range(self.rank)]
        if not hasattr(self, "angles"): self.angles = [0 for _ in range(self.rank)]        
        return
    
    def set_units(self, value: str | Sequence[str], axis: int = -1) -> None:
        if isinstance(value, str):
            if axis > -1 and axis < self.rank: self.units[axis] = value
            else: self.units = [value for _ in range(self.rank)]
            return
        if isinstance(value, list | tuple | np.ndarray): self.units = list(value)
        return
    
    def set_offset(self, value: Numeric | Sequence[Numeric], axis: int = -1) -> None:
        if isinstance(value, Numeric) and axis > -1 and axis < self.rank: self.offset[axis] = value
        if isinstance(value, Sequence): self.offset = list(value)
        return

    def set_angle(self, value: Numeric | Sequence[Numeric], axis: int = -1) -> None:
        if isinstance(value, Numeric) and axis > -1 and axis < self.rank: self.angles[axis] = value
        if isinstance(value, Sequence): self.angles = list(value)
        return
        
    def set_angle_units(self, value: Literal["degree", "rad"]) -> None:
        self.angle_units = value
        return



class DataGrid(CoordinateFrame):
    def __init__(self, x_range: float | int | complex | np.integer | np.floating | Sequence[float | int | complex | np.integer | np.floating] | None = 10,
                 y_range: float | int | complex | np.integer | np.floating | Sequence[float | int | complex | np.integer | np.floating] | None = 10,
                 z_range: float | int | complex | np.integer | np.floating | Sequence[float | int | complex | np.integer | np.floating] | None = None,
                 ranges: Sequence[float | int | complex | np.integer | np.floating] | Sequence[Sequence[float | int | complex | np.integer | np.floating]] | None = None,
                 units: str | Sequence[str] = "nm", offset: float | int | complex | np.integer | np.floating | Sequence[float | int | complex | np.integer | np.floating] = 0,
                 angles: float | int | complex | np.integer | np.floating | Sequence[float | int | complex | np.integer | np.floating] = 0, angle_units: Literal['degree'] | Literal['rad'] = "degree",
                 main_data: np.ndarray = np.zeros((2, 2), dtype = np.float32)
                 ):
        super().__init__(x_range, y_range, z_range, ranges, units, offset, angles, angle_units)
        self.data = main_data
        

