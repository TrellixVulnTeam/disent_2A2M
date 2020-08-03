import logging
import os
from typing import List, Optional, Union

import coloredlogs as coloredlogs
import gin

import numpy as np
import pytorch_lightning as pl
import torch
import torch.utils.data
import torchvision
import wandb
from pytorch_lightning.loggers import CometLogger, LightningLoggerBase, WandbLogger

from disent.dataset.single import GroundTruthDataset
from disent.frameworks.unsupervised.vae import VaeLoss
from disent.metrics import compute_dci, compute_factor_vae
from disent.model import GaussianEncoderDecoderModel
from disent.util import TempNumpySeed, make_box_str, make_logger, to_numpy
from disent.visualize.visualize_model import latent_cycle
from disent.visualize.visualize_util import gridify_animation, reconstructions_to_images


log = make_logger()


# ========================================================================= #
# runner                                                                    #
# ========================================================================= #


class VaeSystem(pl.LightningModule):

    def __init__(self, hparams):
        super().__init__()
        # hyper-parameters
        self.hparams = hparams
        # vae model
        self.model = GaussianEncoderDecoderModel()
        # framework
        self.framework: VaeLoss = hydra.utils.instantiate(self.hparams.framework.cls)
        # data
        self.dataset = None
        self.dataset_train = None
        # self.dataset_val = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Initialisation                                                        #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def prepare_data(self) -> None:
        # *NB* Do not set model parameters here.
        # - Instantiate data once to download and prepare if needed.
        # - trainer.prepare_data_per_node affects this functions behavior per node.
        if 'in_memory' in self.hparams.dataset.cls.params:
            hydra.utils.instantiate(self.hparams.dataset.cls, in_memory=False)
        else:
            hydra.utils.instantiate(self.hparams.dataset.cls)

    def setup(self, stage: str):
        # single observations
        self.dataset = GroundTruthDataset(
            ground_truth_data=hydra.utils.instantiate(self.hparams.dataset.cls),
            transform=torchvision.transforms.Compose([
                hydra.utils.instantiate(transform_cls)
                for transform_cls in self.hparams.dataset.transforms
            ])
        )
        # augment dataset if the framework requires
        self.dataset_train = self.dataset
        if 'augment_dataset' in self.hparams.framework:
            self.dataset_train = hydra.utils.instantiate(self.hparams.framework.augment_dataset.cls, self.dataset)

    def configure_optimizers(self):
        return hydra.utils.instantiate(
            self.hparams.optimizer.cls,
            self.model.parameters()
        )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Output                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def forward(self, x):
        return self.model.forward(x)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Training & Evaluation                                                 #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def training_step(self, batch, batch_idx):
        # handle single case
        if isinstance(batch, torch.Tensor):
            batch = [batch]
        assert len(batch) == self.framework.required_observations, f'Incorrect number of observations ({len(batch)}) for loss: {self.framework.__class__.__name__} ({self.framework.required_observations})'
        # encode, then intercept and mutate if needed [(z_mean, z_logvar), ...]
        z_params = [self.model.encode_gaussian(x) for x in batch]
        z_params = self.framework.intercept_z(*z_params)
        # reparametrize
        zs = [self.model.sample_from_latent_distribution(z0_mean, z0_logvar) for z0_mean, z0_logvar in z_params]
        # reconstruct
        x_recons = [self.model.decode(z) for z in zs]
        # compute loss [(x, x_recon, (z_mean, z_logvar), z), ...]
        loss_dict = self.framework.compute_loss(*[forward_data for forward_data in zip(batch, x_recons, z_params, zs)])
        # log & train
        return {
            'loss': loss_dict['train_loss'],
            'log': loss_dict,
            'progress_bar': loss_dict
        }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Training Dataset:
    #     The sample of data used to fit the model.
    # Validation Dataset:
    #     Data used to provide an unbiased evaluation of a model fit on the
    #     training dataset while tuning model hyperparameters. The
    #     evaluation becomes more biased as skill on the validation
    #     dataset is incorporated into the model configuration.
    # Test Dataset:
    #     The sample of data used to provide an unbiased evaluation of a
    #     final model fit on the training dataset.
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @pl.data_loader
    def train_dataloader(self):
        # Sample of data used to fit the model.
        return torch.utils.data.DataLoader(
            self.dataset_train,
            batch_size=self.hparams.dataset.batch_size,
            num_workers=self.hparams.dataset.num_workers,
            shuffle=True
        )




# ========================================================================= #
# CALLBACKS                                                                 #
# ========================================================================= #


class LatentCycleLoggingCallback(pl.Callback):

    def __init__(self, wandb_logger):
        assert isinstance(wandb_logger, WandbLogger)
        self.wandb_logger = wandb_logger

    def on_epoch_end(self, trainer, system):
        # VISUALISE!
        # generate and log latent traversals
        assert isinstance(system, HydraSystem)
        # get random sample of z_means and z_logvars for computing the range of values for the latent_cycle
        with TempNumpySeed(7777):
            obs = system.dataset.sample_observations(64).to(system.device)
        z_means, z_logvars = system.model.encode_gaussian(obs)
        # produce latent cycle animation & merge frames
        animation = latent_cycle(system.model.reconstruct, z_means, z_logvars, mode='fitted_gaussian_cycle', num_animations=1, num_frames=21)
        animation = reconstructions_to_images(animation, mode='int', moveaxis=False)  # axis already moved above
        frames = np.transpose(gridify_animation(animation[0], padding_px=4, value=64), [0, 3, 1, 2])
        # check and add missing channel if needed (convert greyscale to rgb images)
        assert frames.shape[1] in {1, 3}, f'Invalid number of image channels: {animation.shape} -> {frames.shape}'
        if frames.shape[1] == 1:
            frames = np.repeat(frames, 3, axis=1)
        # log video
        self.wandb_logger.experiment.log({
            'fitted_gaussian_cycle': wandb.Video(frames, fps=5, format='mp4'),
            'epoch': trainer.current_epoch,
        }, commit=False)

# ========================================================================= #
# RUNNER                                                                    #
# ========================================================================= #


gin.external_configurable(WandbLogger, 'pl.loggers.WandbLogger')
gin.external_configurable(CometLogger, 'pl.loggers.CometLogger')

@gin.configurable
def main(
        cuda: bool = gin.REQUIRED,
        loggers: Optional[Union[LightningLoggerBase,List[LightningLoggerBase]]] = None,
):
    # directories
    log.critical(f"Current working directory : {os.getcwd()}")
    log.error(f"Current working directory : {os.getcwd()}")
    log.warning(f"Current working directory : {os.getcwd()}")
    log.info(f"Current working directory : {os.getcwd()}")
    log.debug(f"Current working directory : {os.getcwd()}")

    # warn about CUDA
    if torch.cuda.is_available():
        if not cuda:
            log.warning(f'{cuda=} but CUDA is available on this machine!')
    else:
        if cuda:
            log.error(f'{cuda=} but CUDA is not available on this machine!')
            exit()

    log.info(loggers)

    # # create trainer loggers
    # logger, callbacks = None, []
    # if cfg.logging.wandb.enabled:
    #     log.info(f'wandb log directory: {os.path.abspath("wandb")}')
    #     # TODO: this should be moved into configs, instantiated from a class & target
    #     logger = WandbLogger(
    #         name=cfg.logging.wandb.name,
    #         project=cfg.logging.wandb.project,
    #         group=cfg.logging.wandb.get('group', None),
    #         tags=cfg.logging.wandb.get('tags', None),
    #         entity=cfg.logging.get('entity', None),
    #         save_dir=hydra.utils.to_absolute_path(cfg.logging.logs_dir),  # relative to hydra's original cwd
    #         offline=cfg.logging.wandb.get('offline', False),
    #     )
    #     callbacks.append(LatentCycleLoggingCallback(logger))
    #
    # # check data preparation
    # prepare_data_per_node = cfg.trainer.get('prepare_data_per_node', True)
    # if not os.path.isabs(cfg.dataset.data_dir):
    #     log.warning(
    #         f'A relative path was specified for dataset.data_dir={repr(cfg.dataset.data_dir)}.'
    #         f' This is probably an error! Using relative paths can have unintended consequences'
    #         f' and performance drawbacks if the current working directory is on a shared/network drive.'
    #         f' Hydra config also uses a new working directory for each run of the program, meaning'
    #         f' data will be repeatedly downloaded.'
    #     )
    #     if prepare_data_per_node:
    #         log.error(
    #             f'trainer.prepare_data_per_node={repr(prepare_data_per_node)} but  dataset.data_dir='
    #             f'{repr(cfg.dataset.data_dir)} is a relative path which may be an error! Try specifying an'
    #             f' absolute path that is guaranteed to be unique from each node, eg. dataset.data_dir=/tmp/dataset'
    #         )
    #     raise RuntimeError('dataset.data_dir={repr(cfg.dataset.data_dir)} is a relative path!')
    #
    # # TRAIN
    #
    # system = HydraSystem(cfg)
    # trainer = pl.Trainer(
    #     logger=logger,
    #     callbacks=callbacks,
    #     gpus=1 if cuda else 0,
    #     max_epochs=cfg.trainer.get('epochs', 100),
    #     max_steps=cfg.trainer.get('steps', None),
    #     prepare_data_per_node=prepare_data_per_node,
    # )
    # trainer.fit(system)
    #
    # # EVALUATE
    #
    # metrics = [compute_dci, compute_factor_vae]
    # for metric in metrics:
    #     scores = metric(system.dataset, system.model.encode_deterministic)
    #     log.info(f'{metric.__name__}:\n{DictConfig(scores).pretty()}')
    #     if logger:
    #         assert isinstance(logger, WandbLogger)
    #         logger.experiment.log(scores, commit=False, step=0)


# ========================================================================= #
# MAIN                                                                      #
# ========================================================================= #


if __name__ == '__main__':
    gin.bind_parameter('main.cuda', True)

    main()


# ========================================================================= #
# END                                                                       #
# ========================================================================= #
