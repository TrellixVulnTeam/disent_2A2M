# coding=utf-8
# Copyright 2018 The DisentanglementLib Authors.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Implementation of Disentanglement, Completeness and Informativeness.
Based on "A Framework for the Quantitative Evaluation of Disentangled
Representations" (https://openreview.net/forum?id=By-7dz-AZ).
"""

import logging
from tqdm import tqdm

from disent.metrics import utils
import numpy as np
import scipy
import scipy.stats
from sklearn.ensemble import GradientBoostingClassifier


# ========================================================================= #
# dci                                                                       #
# ========================================================================= #


def compute_dci(
        ground_truth_data,
        representation_function,
        num_train=10000,
        num_test=5000,
        batch_size=16
):
    """Computes the DCI scores according to Sec 2.
    Args:
      ground_truth_data: GroundTruthData to be sampled from.
      representation_function: Function that takes observations as input and
        outputs a dim_representation sized representation for each observation.
      num_train: Number of points used for training.
      num_test: Number of points used for testing.
      batch_size: Batch size for sampling.
    Returns:
      Dictionary with average disentanglement score, completeness and
        informativeness (train and test).
    """
    logging.info("Generating training set.")
    # mus_train are of shape [num_codes, num_train], while ys_train are of shape
    # [num_factors, num_train].
    mus_train, ys_train = utils.generate_batch_factor_code(ground_truth_data, representation_function, num_train, batch_size)
    assert mus_train.shape[1] == num_train
    assert ys_train.shape[1] == num_train
    mus_test, ys_test = utils.generate_batch_factor_code(ground_truth_data, representation_function, num_test, batch_size)

    logging.info("Computing DCI metric.")
    scores = _compute_dci(mus_train, ys_train, mus_test, ys_test)
    return scores


def _compute_dci(mus_train, ys_train, mus_test, ys_test):
    """Computes score based on both training and testing codes and factors."""
    scores = {}
    importance_matrix, train_err, test_err = compute_importance_gbt(mus_train, ys_train, mus_test, ys_test)
    assert importance_matrix.shape[0] == mus_train.shape[0]
    assert importance_matrix.shape[1] == ys_train.shape[0]
    scores["informativeness_train"] = train_err
    scores["informativeness_test"] = test_err
    scores["disentanglement"] = disentanglement(importance_matrix)
    scores["completeness"] = completeness(importance_matrix)
    return scores


def compute_importance_gbt(x_train, y_train, x_test, y_test):
    """Compute importance based on gradient boosted trees."""
    num_factors = y_train.shape[0]
    num_codes = x_train.shape[0]
    importance_matrix = np.zeros(shape=[num_codes, num_factors], dtype=np.float64)
    train_loss = []
    test_loss = []
    for i in tqdm(range(num_factors)):
        model = GradientBoostingClassifier()
        model.fit(x_train.T, y_train[i, :])
        importance_matrix[:, i] = np.abs(model.feature_importances_)
        train_loss.append(np.mean(model.predict(x_train.T) == y_train[i, :]))
        test_loss.append(np.mean(model.predict(x_test.T) == y_test[i, :]))
    return importance_matrix, np.mean(train_loss), np.mean(test_loss)


def disentanglement_per_code(importance_matrix):
    """Compute disentanglement score of each code."""
    # importance_matrix is of shape [num_codes, num_factors].
    return 1. - scipy.stats.entropy(importance_matrix.T + 1e-11, base=importance_matrix.shape[1])


def disentanglement(importance_matrix):
    """Compute the disentanglement score of the representation."""
    per_code = disentanglement_per_code(importance_matrix)
    if importance_matrix.sum() == 0.:
        importance_matrix = np.ones_like(importance_matrix)
    code_importance = importance_matrix.sum(axis=1) / importance_matrix.sum()

    return np.sum(per_code * code_importance)


def completeness_per_factor(importance_matrix):
    """Compute completeness of each factor."""
    # importance_matrix is of shape [num_codes, num_factors].
    return 1. - scipy.stats.entropy(importance_matrix + 1e-11, base=importance_matrix.shape[0])


def completeness(importance_matrix):
    """"Compute completeness of the representation."""
    per_factor = completeness_per_factor(importance_matrix)
    if importance_matrix.sum() == 0.:
        importance_matrix = np.ones_like(importance_matrix)
    factor_importance = importance_matrix.sum(axis=0) / importance_matrix.sum()
    return np.sum(per_factor * factor_importance)

# ========================================================================= #
# END                                                                       #
# ========================================================================= #


if __name__ == '__main__':
    def _main():
        from disent.systems.vae import HParams, VaeSystem
        from disent.util import load_model
        from disent.dataset import DEPRICATED_make_ground_truth_dataset

        for z_size in [12, 6, 3]:
            for loss in ['beta-vae', 'ada-gvae']:
                print()
                print('='*100)
                print()

                hparams = HParams(dataset='3dshapes', model='simple-fc', z_size=z_size, loss=loss)

                print(hparams)
                print()

                system = VaeSystem(hparams=hparams)
                load_model(system, f'data/models/trained-e10-{hparams.dataset}-{hparams.model}-z{hparams.z_size}-{hparams.loss.replace("-","")}.ckpt')
                score = compute_dci(
                    ground_truth_data=DEPRICATED_make_ground_truth_dataset(hparams.dataset),
                    representation_function=system.model.encode_deterministic,
                    num_train=1000,
                    num_test=500,
                )

                print()
                print(score)
                print()

    _main()
    del _main
