#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2021 Nathan Juraj Michlo
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

import logging
import os
from abc import ABC
from abc import ABCMeta
from typing import Any
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import numpy as np
from torch.utils.data import Dataset

from disent.dataset.util.datafile import DataFile
from disent.dataset.util.datafile import DataFileHashedDlH5
from disent.dataset.data._raw import Hdf5Dataset
from disent.dataset.util.state_space import StateSpace
from disent.util.deprecate import deprecated
from disent.util.inout.paths import ensure_dir_exists
from disent.util.iters import LengthIter


log = logging.getLogger(__name__)


# ========================================================================= #
# disent data                                                               #
# ========================================================================= #


class DisentData(LengthIter, Dataset, ABC):

    def __init__(self, transform=None):
        self._transform = transform

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Overridable Defaults                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def name(self):
        raise NotImplementedError()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Properties                                                            #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def x_shape(self) -> Tuple[int, ...]:
        # shape as would be for a single observation in a torch batch
        # eg. C x H x W
        H, W, C = self.img_shape
        return (C, H, W)

    @property
    def img_shape(self) -> Tuple[int, ...]:
        # shape as would be for an original image
        # eg. H x W x C
        raise NotImplementedError()

    @property
    def img_channels(self) -> int:
        channels = self.img_shape[-1]
        assert channels in (1, 3), f'invalid number of channels for dataset: {self.__class__.__name__}, got: {repr(channels)}, required: 1 or 3'
        return channels

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Overrides                                                             #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __getitem__(self, idx):
        obs = self._get_observation(idx)
        if self._transform is not None:
            obs = self._transform(obs)
        return obs

    def _get_observation(self, idx):
        raise NotImplementedError


# ========================================================================= #
# ground truth data                                                         #
# ========================================================================= #


# TODO: StateSpace should be accessed via a property?
#       this should not inherit all its methods?
class DisentGtData(DisentData):
    """
    Dataset that corresponds to some state space or ground truth factors
    """

    def __init__(self, transform=None):
        super().__init__(
            transform=transform,
        )
        self.__state_space = StateSpace(
            factor_sizes=self.factor_sizes,
            factor_names=self.factor_names,
        )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # State Space                                                           #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def factor_names(self) -> Tuple[str, ...]:
        raise NotImplementedError()

    @property
    def factor_sizes(self) -> Tuple[int, ...]:
        raise NotImplementedError()

    @property
    def states(self) -> StateSpace:
        return self.__state_space

    @deprecated('state spaces are immutable, use the .states property instead')
    def state_space_copy(self) -> StateSpace:
        """
        :return: Copy this ground truth dataset as a StateSpace, discarding everything else!
        """
        return StateSpace(
            factor_sizes=self.factor_sizes,
            factor_names=self.factor_names,
        )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # OVERRIDE                                                              #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __len__(self):
        return len(self.states)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # EXTRAS                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def sample_random_obs_traversal(self, f_idx: int = None, base_factors=None, num: int = None, mode='interval', obs_collect_fn=None) -> Tuple[np.ndarray, np.ndarray, Union[List[Any], Any]]:
        """
        Same API as sample_random_factor_traversal, but also
        returns the corresponding indices and uncollated list of observations
        """
        factors = self.sample_random_factor_traversal(f_idx=f_idx, base_factors=base_factors, num=num, mode=mode)
        indices = self.pos_to_idx(factors)
        obs = [self[i] for i in indices]
        if obs_collect_fn is not None:
            obs = obs_collect_fn(obs)
        return factors, indices, obs

    # ================================ #
    # STATE SPACE PROPERTIES & METHODS #
    # ================================ #

    @property
    @deprecated('`DisentGtData.size` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this property from `DisentGtData.states.size`')
    def size(self) -> int:
        return self.states.size

    @property
    @deprecated('`DisentGtData.num_factors` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this property from `DisentGtData.states.num_factors`')
    def num_factors(self) -> int:
        return self.states.num_factors

    # @property
    # @deprecated('`DisentGtData.factor_sizes` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this property from `DisentGtData.states.factor_sizes`')
    # def factor_sizes(self) -> np.ndarray:
    #     return self.states.factor_sizes

    # @property
    # @deprecated('`DisentGtData.factor_names` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this property from `DisentGtData.states.factor_names`')
    # def factor_names(self) -> Tuple[str, ...]:
    #     return self.states.factor_names

    @property
    @deprecated('`DisentGtData.factor_multipliers` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this property from `DisentGtData.states.factor_multipliers`')
    def factor_multipliers(self) -> np.ndarray:
        return self.states.factor_multipliers

    @deprecated('`DisentGtData.normalise_factor_idx(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.normalise_factor_idx(...)`')
    def normalise_factor_idx(self, *args, **kwargs):
        return self.states.normalise_factor_idx(*args, **kwargs)

    @deprecated('`DisentGtData.normalise_factor_idxs(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.normalise_factor_idxs(...)`')
    def normalise_factor_idxs(self, *args, **kwargs):
        return self.states.normalise_factor_idxs(*args, **kwargs)

    @deprecated('`DisentGtData.invert_factor_idxs(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.invert_factor_idxs(...)`')
    def invert_factor_idxs(self, *args, **kwargs):
        return self.states.invert_factor_idxs(*args, **kwargs)

    @deprecated('`DisentGtData.pos_to_idx(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.pos_to_idx(...)`')
    def pos_to_idx(self, *args, **kwargs):
        return self.states.pos_to_idx(*args, **kwargs)

    @deprecated('`DisentGtData.idx_to_pos(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.idx_to_pos(...)`')
    def idx_to_pos(self, *args, **kwargs):
        return self.states.idx_to_pos(*args, **kwargs)

    @deprecated('`DisentGtData.iter_traversal_indices(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.iter_traversal_indices(...)`')
    def iter_traversal_indices(self, *args, **kwargs):
        return self.states.iter_traversal_indices(*args, **kwargs)

    @deprecated('`DisentGtData.sample_indices(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.sample_indices(...)`')
    def sample_indices(self, *args, **kwargs):
        return self.states.sample_indices(*args, **kwargs)

    @deprecated('`DisentGtData.sample_factors(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.sample_factors(...)`')
    def sample_factors(self, *args, **kwargs):
        return self.states.sample_factors(*args, **kwargs)

    @deprecated('`DisentGtData.sample_missing_factors(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.sample_missing_factors(...)`')
    def sample_missing_factors(self, *args, **kwargs):
        return self.states.sample_missing_factors(*args, **kwargs)

    @deprecated('`DisentGtData.resample_other_factors(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.resample_other_factors(...)`')
    def resample_other_factors(self, *args, **kwargs):
        return self.states.resample_other_factors(*args, **kwargs)

    @deprecated('`DisentGtData.resample_given_factors(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.resample_given_factors(...)`')
    def resample_given_factors(self, *args, **kwargs):
        return self.states.resample_given_factors(*args, **kwargs)

    @deprecated('`DisentGtData.sample_random_factor_traversal(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.sample_random_factor_traversal(...)`')
    def sample_random_factor_traversal(self, *args, **kwargs):
        return self.states.sample_random_factor_traversal(*args, **kwargs)

    @deprecated('`DisentGtData.sample_random_factor_traversal_grid(...)` has been deprecated, `DisentGtData` no longer inherits `StateSpace`, please access this method from `DisentGtData.states.sample_random_factor_traversal_grid(...)`')
    def sample_random_factor_traversal_grid(self, *args, **kwargs):
        return self.states.sample_random_factor_traversal_grid(*args, **kwargs)


# ========================================================================= #
# EXPORT                                                                    #
# ========================================================================= #


GroundTruthData = deprecated('`GroundTruthData` has been renamed to `DisentGtData`', fn=DisentGtData)


# ========================================================================= #
# Basic Array Ground Truth Dataset                                          #
# ========================================================================= #


class ArrayGroundTruthData(GroundTruthData):

    def __init__(self, array, factor_names: Tuple[str, ...], factor_sizes: Tuple[int, ...], array_chn_is_last: bool = True, x_shape: Optional[Tuple[int, ...]] = None, transform=None):
        self.__factor_names = tuple(factor_names)
        self.__factor_sizes = tuple(factor_sizes)
        self._array = array
        # get shape
        if x_shape is not None:
            C, H, W = x_shape
        elif array_chn_is_last:
            H, W, C = array.shape[1:]
        else:
            C, H, W = array.shape[1:]
        # set observation shape
        self.__img_shape = (H, W, C)
        # initialize
        super().__init__(transform=transform)
        # check shapes -- it is up to the user to handle which method they choose
        assert (array.shape[1:] == self.img_shape) or (array.shape[1:] == self.x_shape)

    @property
    def array(self):
        return self._array

    @property
    def factor_names(self) -> Tuple[str, ...]:
        return self.__factor_names

    @property
    def factor_sizes(self) -> Tuple[int, ...]:
        return self.__factor_sizes

    @property
    def img_shape(self) -> Tuple[int, ...]:
        return self.__img_shape

    def _get_observation(self, idx):
        # TODO: INVESTIGATE! I think this implements a lock,
        #       hindering multi-threaded environments?
        return self._array[idx]

    @classmethod
    def new_like(cls, array, gt_data: GroundTruthData, array_chn_is_last: bool = True):
        # TODO: should this not copy the x_shape and transform?
        return cls(
            array=array,
            factor_names=gt_data.factor_names,
            factor_sizes=gt_data.factor_sizes,
            array_chn_is_last=array_chn_is_last,
            x_shape=None,  # infer from array
            transform=None,
        )


# ========================================================================= #
# disk ground truth data                                                    #
# TODO: data & datafile preparation should be split out from                #
#       GroundTruthData, instead GroundTruthData should be a wrapper        #
# ========================================================================= #


class _DiskDataMixin(object):

    # attr this class defines in _mixin_disk_init
    _data_dir: str

    def _mixin_disk_init(self, data_root: Optional[str] = None, prepare: bool = False):
        # get root data folder
        if data_root is None:
            data_root = self.default_data_root
        else:
            data_root = os.path.abspath(os.path.expanduser(data_root))
        # get class data folder
        self._data_dir = ensure_dir_exists(os.path.join(data_root, self.name))
        log.info(f'{self.name}: data_dir_share={repr(self._data_dir)}')
        # prepare everything
        if prepare:
            for datafile in self.datafiles:
                log.debug(f'[preparing]: {datafile} into data dir: {self._data_dir}')
                datafile.prepare(self.data_dir)

    @property
    def data_dir(self) -> str:
        return self._data_dir

    @property
    def default_data_root(self):
        return os.path.abspath(os.environ.get('DISENT_DATA_ROOT', 'data/dataset'))

    @property
    def datafiles(self) -> Sequence[DataFile]:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError


class DiskGroundTruthData(_DiskDataMixin, GroundTruthData, metaclass=ABCMeta):

    """
    Dataset that prepares a list DataObjects into some local directory.
    - This directory can be
    """

    def __init__(self, data_root: Optional[str] = None, prepare: bool = False, transform=None):
        super().__init__(transform=transform)
        # get root data folder
        self._mixin_disk_init(data_root=data_root, prepare=prepare)


class NumpyFileGroundTruthData(DiskGroundTruthData, metaclass=ABCMeta):
    """
    Dataset that loads a numpy file from a DataObject
    - if the dataset is contained in a key, set the `data_key` property
    """

    def __init__(self, data_root: Optional[str] = None, prepare: bool = False, transform=None):
        super().__init__(data_root=data_root, prepare=prepare, transform=transform)
        # load dataset
        load_path = os.path.join(self.data_dir, self.datafile.out_name)
        if load_path.endswith('.gz'):
            import gzip
            with gzip.GzipFile(load_path, 'r') as load_file:
                self._data = np.load(load_file)
        else:
            self._data = np.load(load_path)
        # load from the key if specified
        if self.data_key is not None:
            self._data = self._data[self.data_key]

    def _get_observation(self, idx):
        return self._data[idx]

    @property
    def datafiles(self) -> Sequence[DataFile]:
        return [self.datafile]

    @property
    def datafile(self) -> DataFile:
        raise NotImplementedError

    @property
    def data_key(self) -> Optional[str]:
        # can override this!
        return None


class _Hdf5DataMixin(object):

    # attrs this class defines in _mixin_hdf5_init
    _in_memory: bool
    _attrs: dict
    _data: Union[Hdf5Dataset, np.ndarray]

    def _mixin_hdf5_init(self, h5_path: str, h5_dataset_name: str = 'data', in_memory: bool = False):
        # variables
        self._in_memory = in_memory
        # load the h5py dataset
        data = Hdf5Dataset(
            h5_path=h5_path,
            h5_dataset_name=h5_dataset_name,
        )
        # load attributes
        self._attrs = data.get_attrs()
        # handle different memory modes
        if self._in_memory:
            # Load the entire dataset into memory if required
            # indexing dataset objects returns numpy array
            # instantiating np.array from the dataset requires double memory.
            self._data = data[:]
            self._data.flags.writeable = False
            data.close()
        else:
            # Load the dataset from the disk
            self._data = data

    def __len__(self):
        return len(self._data)

    @property
    def img_shape(self):
        shape = self._data.shape[1:]
        assert len(shape) == 3
        return shape

    # override from GroundTruthData
    def _get_observation(self, idx):
        return self._data[idx]


class Hdf5GroundTruthData(_Hdf5DataMixin, DiskGroundTruthData, metaclass=ABCMeta):
    """
    Dataset that loads an Hdf5 file from a DataObject
    - requires that the data object has the `out_dataset_name` attribute
      that points to the hdf5 dataset in the file to load.
    """

    def __init__(self, data_root: Optional[str] = None, prepare: bool = False, in_memory=False, transform=None):
        super().__init__(data_root=data_root, prepare=prepare, transform=transform)
        # initialize mixin
        self._mixin_hdf5_init(
            h5_path=os.path.join(self.data_dir, self.datafile.out_name),
            h5_dataset_name=self.datafile.dataset_name,
            in_memory=in_memory,
        )

    @property
    def datafiles(self) -> Sequence[DataFileHashedDlH5]:
        return [self.datafile]

    @property
    def datafile(self) -> DataFileHashedDlH5:
        raise NotImplementedError


class SelfContainedHdf5GroundTruthData(_Hdf5DataMixin, GroundTruthData):

    def __init__(self, h5_path: str, in_memory=False, transform=None):
        # initialize mixin
        self._mixin_hdf5_init(
            h5_path=h5_path,
            h5_dataset_name='data',
            in_memory=in_memory,
        )
        # load attrs
        self._attr_name = self._attrs['dataset_name'].decode("utf-8")
        self._attr_factor_names = tuple(name.decode("utf-8") for name in self._attrs['factor_names'])
        self._attr_factor_sizes = tuple(int(size) for size in self._attrs['factor_sizes'])
        # set size
        (B, H, W, C) = self._data.shape
        self._img_shape = (H, W, C)
        # initialize!
        super().__init__(transform=transform)

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def factor_names(self) -> Tuple[str, ...]:
        return self._attr_factor_names

    @property
    def factor_sizes(self) -> Tuple[int, ...]:
        return self._attr_factor_sizes

    @property
    def img_shape(self) -> Tuple[int, ...]:
        return self._img_shape


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
