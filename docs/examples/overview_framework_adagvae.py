import pytorch_lightning as pl
from torch.utils.data import DataLoader
from disent.dataset import DisentDataset
from disent.dataset.data import XYObjectData
from disent.dataset.sampling import GroundTruthPairOrigSampler
from disent.frameworks.vae import AdaVae
from disent.model import AutoEncoder
from disent.model.ae import DecoderConv64, EncoderConv64
from disent.dataset.transform import ToImgTensorF32
from disent.util import is_test_run  # you can ignore and remove this


# prepare the data
data = XYObjectData()
dataset = DisentDataset(data, GroundTruthPairOrigSampler(), transform=ToImgTensorF32())
dataloader = DataLoader(dataset=dataset, batch_size=4, shuffle=True, num_workers=0)

# create the pytorch lightning system
module: pl.LightningModule = AdaVae(
    model=AutoEncoder(
        encoder=EncoderConv64(x_shape=data.x_shape, z_size=6, z_multiplier=2),
        decoder=DecoderConv64(x_shape=data.x_shape, z_size=6),
    ),
    cfg=AdaVae.cfg(
        optimizer='adam', optimizer_kwargs=dict(lr=1e-3),
        loss_reduction='mean_sum', beta=4, ada_average_mode='gvae', ada_thresh_mode='kl',
    )
)

# train the model
trainer = pl.Trainer(logger=False, enable_checkpointing=False, fast_dev_run=is_test_run())
trainer.fit(module, dataloader)
