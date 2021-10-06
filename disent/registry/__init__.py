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

"""
The disent registry only contains implemented versions of
classes and functions, no interfaces are included.
  - for interfaces and creating your own data types, extend
    the base classes from the various locations.

*NB* All modules and classes are lazily imported!

You can register your own modules and classes using the provided decorator:
eg. `DATASET.register(...options...)(your_function_or_class)`
"""

from disent.registry._registry import Registry as _Registry
from disent.registry._registry import LazyImport as _LazyImport


# ========================================================================= #
# DATASETS - should be synchronized with: `disent/dataset/data/__init__.py` #
# ========================================================================= #


DATASETS = _Registry('DATASET')
# groundtruth -- impl
DATASETS['cars3d']            = _LazyImport('disent.dataset.data._groundtruth__cars3d')
DATASETS['dsprites']          = _LazyImport('disent.dataset.data._groundtruth__dsprites')
DATASETS['mpi3d']             = _LazyImport('disent.dataset.data._groundtruth__mpi3d')
DATASETS['smallnorb']         = _LazyImport('disent.dataset.data._groundtruth__norb')
DATASETS['shapes3d']          = _LazyImport('disent.dataset.data._groundtruth__shapes3d')
# groundtruth -- impl synthetic
DATASETS['xyblocks']          = _LazyImport('disent.dataset.data._groundtruth__xyblocks')   # pragma: delete-on-release
DATASETS['xyobject']          = _LazyImport('disent.dataset.data._groundtruth__xyobject')
DATASETS['xysquares']         = _LazyImport('disent.dataset.data._groundtruth__xysquares')  # pragma: delete-on-release
DATASETS['xysquares_minimal'] = _LazyImport('disent.dataset.data._groundtruth__xysquares')  # pragma: delete-on-release
DATASETS['xcolumns']          = _LazyImport('disent.dataset.data._groundtruth__xcolumns')   # pragma: delete-on-release


# ========================================================================= #
# SAMPLERS - should be synchronized with:                                   #
#            `disent/dataset/sampling/__init__.py`                          #
# ========================================================================= #


# changes here should also update
SAMPLERS = _Registry('SAMPLER')
# [ground truth samplers]
SAMPLERS['gt_dist']         = _LazyImport('disent.dataset.sampling._groundtruth__dist.GroundTruthDistSampler')
SAMPLERS['gt_pair']         = _LazyImport('disent.dataset.sampling._groundtruth__pair.GroundTruthPairSampler')
SAMPLERS['gt_pair_orig']    = _LazyImport('disent.dataset.sampling._groundtruth__pair_orig.GroundTruthPairOrigSampler')
SAMPLERS['gt_single']       = _LazyImport('disent.dataset.sampling._groundtruth__single.GroundTruthSingleSampler')
SAMPLERS['gt_triple']       = _LazyImport('disent.dataset.sampling._groundtruth__triplet.GroundTruthTripleSampler')
# [any dataset samplers]
SAMPLERS['single']          = _LazyImport('disent.dataset.sampling._single.SingleSampler')
SAMPLERS['random']          = _LazyImport('disent.dataset.sampling._random__any.RandomSampler')
# [episode samplers]
SAMPLERS['random_episode']  = _LazyImport('disent.dataset.sampling._random__episodes.RandomEpisodeSampler')


# ========================================================================= #
# FRAMEWORKS - should be synchronized with:                                 #
#             `disent/frameworks/ae/__init__.py`                            #
#             `disent/frameworks/ae/experimental/__init__.py`               #
#             `disent/frameworks/vae/__init__.py`                           #
#             `disent/frameworks/vae/experimental/__init__.py`              #
# ========================================================================= #


FRAMEWORKS = _Registry('FRAMEWORK')
# [AE]
FRAMEWORKS['tae']           = _LazyImport('disent.frameworks.ae._supervised__tae.TripletAe')
FRAMEWORKS['ae']            = _LazyImport('disent.frameworks.ae._unsupervised__ae.Ae')
# [VAE]
FRAMEWORKS['tvae']          = _LazyImport('disent.frameworks.vae._supervised__tvae.TripletVae')
FRAMEWORKS['betatc_vae']    = _LazyImport('disent.frameworks.vae._unsupervised__betatcvae.BetaTcVae')
FRAMEWORKS['beta_vae']      = _LazyImport('disent.frameworks.vae._unsupervised__betavae.BetaVae')
FRAMEWORKS['dfc_vae']       = _LazyImport('disent.frameworks.vae._unsupervised__dfcvae.DfcVae')
FRAMEWORKS['dip_vae']       = _LazyImport('disent.frameworks.vae._unsupervised__dipvae.DipVae')
FRAMEWORKS['info_vae']      = _LazyImport('disent.frameworks.vae._unsupervised__infovae.InfoVae')
FRAMEWORKS['vae']           = _LazyImport('disent.frameworks.vae._unsupervised__vae.Vae')
FRAMEWORKS['ada_vae']       = _LazyImport('disent.frameworks.vae._weaklysupervised__adavae.AdaVae')
# [AE - EXPERIMENTAL]                                                                                                                 # pragma: delete-on-release
FRAMEWORKS['x__adaneg_tae']  = _LazyImport('disent.frameworks.ae.experimental._supervised__adaneg_tae.AdaNegTripletAe')               # pragma: delete-on-release
FRAMEWORKS['x__dot_ae']      = _LazyImport('disent.frameworks.ae.experimental._unsupervised__dotae.DataOverlapTripletAe')             # pragma: delete-on-release
FRAMEWORKS['x__ada_ae']      = _LazyImport('disent.frameworks.ae.experimental._weaklysupervised__adaae.AdaAe')                        # pragma: delete-on-release
# [VAE - EXPERIMENTAL]                                                                                                                # pragma: delete-on-release
FRAMEWORKS['x__adaave_tvae'] = _LazyImport('disent.frameworks.vae.experimental._supervised__adaave_tvae.AdaAveTripletVae')            # pragma: delete-on-release
FRAMEWORKS['x__adaneg_tvae'] = _LazyImport('disent.frameworks.vae.experimental._supervised__adaneg_tvae.AdaNegTripletVae')            # pragma: delete-on-release
FRAMEWORKS['x__ada_tvae']    = _LazyImport('disent.frameworks.vae.experimental._supervised__adatvae.AdaTripletVae')                   # pragma: delete-on-release
FRAMEWORKS['x__bada_vae']    = _LazyImport('disent.frameworks.vae.experimental._supervised__badavae.BoundedAdaVae')                   # pragma: delete-on-release
FRAMEWORKS['x__gada_vae']    = _LazyImport('disent.frameworks.vae.experimental._supervised__gadavae.GuidedAdaVae')                    # pragma: delete-on-release
FRAMEWORKS['x__tbada_vae']   = _LazyImport('disent.frameworks.vae.experimental._supervised__tbadavae.TripletBoundedAdaVae')           # pragma: delete-on-release
FRAMEWORKS['x__tgada_vae']   = _LazyImport('disent.frameworks.vae.experimental._supervised__tgadavae.TripletGuidedAdaVae')            # pragma: delete-on-release
FRAMEWORKS['x__dor_vae']     = _LazyImport('disent.frameworks.vae.experimental._unsupervised__dorvae.DataOverlapRankVae')             # pragma: delete-on-release
FRAMEWORKS['x__dot_vae']     = _LazyImport('disent.frameworks.vae.experimental._unsupervised__dotvae.DataOverlapTripletVae')          # pragma: delete-on-release
FRAMEWORKS['x__augpos_tvae'] = _LazyImport('disent.frameworks.vae.experimental._weaklysupervised__augpostriplet.AugPosTripletVae')    # pragma: delete-on-release
FRAMEWORKS['x__st_ada_vae']  = _LazyImport('disent.frameworks.vae.experimental._weaklysupervised__st_adavae.SwappedTargetAdaVae')     # pragma: delete-on-release
FRAMEWORKS['x__st_beta_vae'] = _LazyImport('disent.frameworks.vae.experimental._weaklysupervised__st_betavae.SwappedTargetBetaVae')   # pragma: delete-on-release


# ========================================================================= #
# RECON_LOSSES - should be synchronized with:                               #
#                `disent/frameworks/helper/reconstructions.py`              #
# ========================================================================= #


RECON_LOSSES = _Registry('RECON_LOSS')
# [STANDARD LOSSES]
RECON_LOSSES['mse']         = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerMse')                  # from the normal distribution - real values in the range [0, 1]
RECON_LOSSES['mae']         = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerMae')                  # mean absolute error
# [STANDARD DISTRIBUTIONS]
RECON_LOSSES['bce']         = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerBce')                  # from the bernoulli distribution - binary values in the set {0, 1}
RECON_LOSSES['bernoulli']   = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerBernoulli')            # reduces to bce - binary values in the set {0, 1}
RECON_LOSSES['c_bernoulli'] = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerContinuousBernoulli')  # bernoulli with a computed offset to handle values in the range [0, 1]
RECON_LOSSES['normal']      = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerNormal')               # handle all real values
# [EXPERIMENTAL LOSSES]                                                                                                                                                                                 # pragma: delete-on-release
RECON_LOSSES['mse4']        = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerMse4')                 # scaled as if computed over outputs of the range [-1, 1] instead of [0, 1]  # pragma: delete-on-release
RECON_LOSSES['mae2']        = _LazyImport('disent.frameworks.helper.reconstructions.ReconLossHandlerMae2')                 # scaled as if computed over outputs of the range [-1, 1] instead of [0, 1]  # pragma: delete-on-release


# ========================================================================= #
# LATENT_DISTS - should be synchronized with:                               #
#                `disent/frameworks/helper/latent_distributions.py`         #
# ========================================================================= #


LATENT_DISTS = _Registry('LATENT_DIST')
LATENT_DISTS['normal']  = _LazyImport('disent.frameworks.helper.latent_distributions.LatentDistsHandlerNormal')
LATENT_DISTS['laplace'] = _LazyImport('disent.frameworks.helper.latent_distributions.LatentDistsHandlerLaplace')


# ========================================================================= #
# OPTIMIZER                                                                 #
# ========================================================================= #


# default learning rate for each optimizer
_LR = 1e-3


OPTIMIZERS = _Registry('OPTIMIZER')
# [torch]
OPTIMIZERS['adadelta']    = _LazyImport(lr=_LR, import_path='torch.optim.adadelta.Adadelta')
OPTIMIZERS['adagrad']     = _LazyImport(lr=_LR, import_path='torch.optim.adagrad.Adagrad')
OPTIMIZERS['adam']        = _LazyImport(lr=_LR, import_path='torch.optim.adam.Adam')
OPTIMIZERS['adamax']      = _LazyImport(lr=_LR, import_path='torch.optim.adamax.Adamax')
OPTIMIZERS['adam_w']      = _LazyImport(lr=_LR, import_path='torch.optim.adamw.AdamW')
OPTIMIZERS['asgd']        = _LazyImport(lr=_LR, import_path='torch.optim.asgd.ASGD')
OPTIMIZERS['lbfgs']       = _LazyImport(lr=_LR, import_path='torch.optim.lbfgs.LBFGS')
OPTIMIZERS['rmsprop']     = _LazyImport(lr=_LR, import_path='torch.optim.rmsprop.RMSprop')
OPTIMIZERS['rprop']       = _LazyImport(lr=_LR, import_path='torch.optim.rprop.Rprop')
OPTIMIZERS['sgd']         = _LazyImport(lr=_LR, import_path='torch.optim.sgd.SGD')
OPTIMIZERS['sparse_adam'] = _LazyImport(lr=_LR, import_path='torch.optim.sparse_adam.SparseAdam')
# [torch_optimizer]
OPTIMIZERS['acc_sgd']     = _LazyImport(lr=_LR, import_path='torch_optimizer.AccSGD')
OPTIMIZERS['ada_bound']   = _LazyImport(lr=_LR, import_path='torch_optimizer.AdaBound')
OPTIMIZERS['ada_mod']     = _LazyImport(lr=_LR, import_path='torch_optimizer.AdaMod')
OPTIMIZERS['adam_p']      = _LazyImport(lr=_LR, import_path='torch_optimizer.AdamP')
OPTIMIZERS['agg_mo']      = _LazyImport(lr=_LR, import_path='torch_optimizer.AggMo')
OPTIMIZERS['diff_grad']   = _LazyImport(lr=_LR, import_path='torch_optimizer.DiffGrad')
OPTIMIZERS['lamb']        = _LazyImport(lr=_LR, import_path='torch_optimizer.Lamb')
# 'torch_optimizer.Lookahead' is skipped because it is wrapped
OPTIMIZERS['novograd']    = _LazyImport(lr=_LR, import_path='torch_optimizer.NovoGrad')
OPTIMIZERS['pid']         = _LazyImport(lr=_LR, import_path='torch_optimizer.PID')
OPTIMIZERS['qh_adam']     = _LazyImport(lr=_LR, import_path='torch_optimizer.QHAdam')
OPTIMIZERS['qhm']         = _LazyImport(lr=_LR, import_path='torch_optimizer.QHM')
OPTIMIZERS['radam']       = _LazyImport(lr=_LR, import_path='torch_optimizer.RAdam')
OPTIMIZERS['ranger']      = _LazyImport(lr=_LR, import_path='torch_optimizer.Ranger')
OPTIMIZERS['ranger_qh']   = _LazyImport(lr=_LR, import_path='torch_optimizer.RangerQH')
OPTIMIZERS['ranger_va']   = _LazyImport(lr=_LR, import_path='torch_optimizer.RangerVA')
OPTIMIZERS['sgd_w']       = _LazyImport(lr=_LR, import_path='torch_optimizer.SGDW')
OPTIMIZERS['sgd_p']       = _LazyImport(lr=_LR, import_path='torch_optimizer.SGDP')
OPTIMIZERS['shampoo']     = _LazyImport(lr=_LR, import_path='torch_optimizer.Shampoo')
OPTIMIZERS['yogi']        = _LazyImport(lr=_LR, import_path='torch_optimizer.Yogi')


# ========================================================================= #
# METRIC - should be synchronized with: `disent/metrics/__init__.py`        #
# ========================================================================= #


METRICS = _Registry('METRIC')
METRICS['dci']                 = _LazyImport('disent.metrics._dci.metric_dci')
METRICS['factor_vae']          = _LazyImport('disent.metrics._factor_vae.metric_factor_vae')
METRICS['flatness']            = _LazyImport('disent.metrics._flatness.metric_flatness')                        # pragma: delete-on-release
METRICS['flatness_components'] = _LazyImport('disent.metrics._flatness_components.metric_flatness_components')  # pragma: delete-on-release
METRICS['mig']                 = _LazyImport('disent.metrics._mig.metric_mig')
METRICS['sap']                 = _LazyImport('disent.metrics._sap.metric_sap')
METRICS['unsupervised']        = _LazyImport('disent.metrics._unsupervised.metric_unsupervised')


# ========================================================================= #
# SCHEDULE - should be synchronized with: `disent/schedule/__init__.py`     #
# ========================================================================= #


SCHEDULES = _Registry('SCHEDULE')
SCHEDULES['clip']        = _LazyImport('disent.schedule._schedule.ClipSchedule')
SCHEDULES['cosine_wave'] = _LazyImport('disent.schedule._schedule.CosineWaveSchedule')
SCHEDULES['cyclic']      = _LazyImport('disent.schedule._schedule.CyclicSchedule')
SCHEDULES['linear']      = _LazyImport('disent.schedule._schedule.LinearSchedule')
SCHEDULES['noop']        = _LazyImport('disent.schedule._schedule.NoopSchedule')


# ========================================================================= #
# MODEL - should be synchronized with: `disent/model/ae/__init__.py`        #
# ========================================================================= #


MODELS = _Registry('MODEL')
# [DECODER]
MODELS['encoder_conv64']     = _LazyImport('disent.model.ae._vae_conv64.EncoderConv64')
MODELS['encoder_conv64norm'] = _LazyImport('disent.model.ae._norm_conv64.EncoderConv64Norm')
MODELS['encoder_fc']         = _LazyImport('disent.model.ae._vae_fc.EncoderFC')
MODELS['encoder_test']       = _LazyImport('disent.model.ae._test.EncoderTest')
# [ENCODER]
MODELS['decoder_conv64']     = _LazyImport('disent.model.ae._vae_conv64.DecoderConv64')
MODELS['decoder_conv64norm'] = _LazyImport('disent.model.ae._norm_conv64.DecoderConv64Norm')
MODELS['decoder_fc']         = _LazyImport('disent.model.ae._vae_fc.DecoderFC')
MODELS['decoder_test']       = _LazyImport('disent.model.ae._test.DecoderTest')


# ========================================================================= #
# Registry of all Registries                                                #
# ========================================================================= #


# registry of registries
REGISTRIES = _Registry('REGISTRIES')
REGISTRIES['DATASETS']      = DATASETS
REGISTRIES['SAMPLERS']      = SAMPLERS
REGISTRIES['FRAMEWORKS']    = FRAMEWORKS
REGISTRIES['RECON_LOSSES']  = RECON_LOSSES
REGISTRIES['LATENT_DISTS']  = LATENT_DISTS
REGISTRIES['OPTIMIZERS']    = OPTIMIZERS
REGISTRIES['METRICS']       = METRICS
REGISTRIES['SCHEDULES']     = SCHEDULES
REGISTRIES['MODELS']        = MODELS


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
