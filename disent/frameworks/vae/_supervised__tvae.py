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

from dataclasses import dataclass
from distutils.dist import Distribution
from numbers import Number
from typing import Any
from typing import Dict
from typing import Sequence
from typing import Tuple
from typing import Union

import numpy as np
import torch
from torch.distributions import Normal

from disent.frameworks.helper.triplet_loss import compute_triplet_loss
from disent.frameworks.helper.triplet_loss import TripletLossConfig
from disent.frameworks.vae._unsupervised__betavae import BetaVae


# ========================================================================= #
# tvae                                                                      #
# ========================================================================= #


class TripletVae(BetaVae):

    REQUIRED_OBS = 3

    @dataclass
    class cfg(BetaVae.cfg, TripletLossConfig):
        # tvae: no loss from decoder -> encoder
        # TODO: add detach mode in VAE that stops sampling!
        detach_no_kl: bool = False
        detach_std: float = None

    # TODO: move this into VAE
    def hook_intercept_zs(self, zs_params: Sequence['Params']) -> Tuple[Sequence['Params'], Dict[str, Any]]:
        # replace logvar
        if self.cfg.detach and (self.cfg.detach_std is not None):
            for z_params in zs_params:
                z_params.logvar = torch.full_like(z_params.logvar, fill_value=np.log(self.cfg.detach_std ** 2))
        return zs_params, {}

    # TODO: move this into VAE
    def compute_ave_reg_loss(self, ds_posterior: Sequence[Distribution], ds_prior: Sequence[Distribution], zs_sampled: Sequence[torch.Tensor]) -> Tuple[Union[torch.Tensor, Number], Dict[str, Any]]:
        if self.cfg.detach and self.cfg.detach_no_kl:
            return 0, {}
        return super().compute_ave_reg_loss(ds_posterior, ds_prior, zs_sampled)

    def hook_compute_ave_aug_loss(self, ds_posterior: Sequence[Normal], ds_prior: Sequence[Normal], zs_sampled: Sequence[torch.Tensor], xs_partial_recon: Sequence[torch.Tensor], xs_targ: Sequence[torch.Tensor]) -> Tuple[Union[torch.Tensor, Number], Dict[str, Any]]:
        return compute_triplet_loss(zs=[d.mean for d in ds_posterior], cfg=self.cfg)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
