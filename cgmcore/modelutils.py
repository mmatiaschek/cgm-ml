"""
Helper module for instaniating some Neural Networks.
"""

from keras import models, layers
from keras import backend as K
import numpy as np
import tensorflow as tf


def create_sequence_model(base_model, sequence_length, input_shape, output_size, use_lstm):

    assert base_model == "voxnet" or base_model == "pointnet"

    if base_model == "voxnet":
        base_model = create_voxnet_model_homepage(input_shape, output_size)
    elif base_model == "pointnet":
        base_model = create_point_net(input_shape, output_size)

    model = models.Sequential()
    model.add(layers.TimeDistributed(base_model, input_shape=(sequence_length,) + input_shape))
    if use_lstm == True:
        model.add(layers.LSTM(8, activation="relu"))
    else:
        model.add(layers.AveragePooling1D(sequence_length))
        model.add(layers.Flatten())
    model.add(layers.Dense(output_size))

    return model


def create_dense_model(input_shape, output_size):
    """
    Creates a simple dense model.

    Note: This is only suitable for baseling.

    Args:
        input_shape (shape): Input-shape.
        output_size (int): Output-size.

    Returns:
        Model: A model.
    """

    model = models.Sequential(name="baseline-dense")
    model.add(layers.Flatten(input_shape=input_shape))
    model.add(layers.Dense(128, activation="relu"))
    model.add(layers.Dense(64, activation="relu"))
    model.add(layers.Dense(output_size))

    return model


def create_voxnet_model_small(input_shape, output_size):
    """
    Creates a small VoxNet.

    See: http://dimatura.net/publications/3dcnn_lz_maturana_scherer_icra15.pdf

    Args:
        input_shape (shape): Input-shape.
        output_size (int): Output-size.

    Returns:
        Model: A model.
    """

    #Trainable params: 301,378
    model = models.Sequential(name="C7-F32-P2-C5-F64-P2-D512")
    model.add(layers.Reshape(target_shape=input_shape + (1,), input_shape=input_shape))
    model.add(layers.Conv3D(32, (7, 7, 7), activation="relu"))
    model.add(layers.MaxPooling3D((4, 4, 4)))
    model.add(layers.Conv3D(64, (5, 5, 5), activation="relu"))
    model.add(layers.MaxPooling3D((2, 2, 2)))
    model.add(layers.Flatten())
    model.add(layers.Dense(512, activation="relu"))
    model.add(layers.Dense(output_size))

    return model


def create_voxnet_model_big(input_shape, output_size):
    """
    Creates a big VoxNet.

    See: http://dimatura.net/publications/3dcnn_lz_maturana_scherer_icra15.pdf

    Args:
        input_shape (shape): Input-shape.
        output_size (int): Output-size.

    Returns:
        Model: A model.
    """

    # Trainable params: 7,101,442
    model = models.Sequential(name="C7-F64-P4-D512")
    model.add(layers.Reshape(target_shape=input_shape + (1,), input_shape=input_shape))
    model.add(layers.Conv3D(64, (7, 7, 7), activation="relu"))
    model.add(layers.MaxPooling3D((4, 4, 4)))
    model.add(layers.Flatten())
    model.add(layers.Dense(512, activation="relu"))
    model.add(layers.Dense(output_size))

    return model


def create_voxnet_model_homepage(input_shape, output_size):
    """
    Creates a small VoxNet.

    See: http://dimatura.net/publications/3dcnn_lz_maturana_scherer_icra15.pdf

    Note: This is the latest model that the VoxNet-authors used.

    Args:
        input_shape (shape): Input-shape.
        output_size (int): Output-size.

    Returns:
        Model: A model.
    """

    # Trainable params: 916,834
    model = models.Sequential(name="VoxNetHomepage")
    model.add(layers.Reshape(target_shape=input_shape + (1,), input_shape=input_shape))
    model.add(layers.Conv3D(32, (5, 5, 5), strides=(2, 2, 2), activation="relu"))
    model.add(layers.Conv3D(32, (3, 3, 3), strides=(1, 1, 1), activation="relu"))
    model.add(layers.MaxPooling3D((2, 2, 2)))
    model.add(layers.Flatten())
    model.add(layers.Dense(128, activation="relu"))
    model.add(layers.Dense(output_size))

    return model


def create_point_net(input_shape, output_size):
    """
    Creates a PointNet.

    See https://github.com/garyloveavocado/pointnet-keras/blob/master/train_cls.py

    Args:
        input_shape (shape): Input-shape.
        output_size (int): Output-size.

    Returns:
        Model: A model.
    """

    num_points = input_shape[0]

    def mat_mul(A, B):
        result = tf.matmul(A, B)
        return result

    input_points = layers.Input(shape=input_shape)
    x = layers.Convolution1D(64, 1, activation='relu',
                      input_shape=input_shape)(input_points)
    x = layers.BatchNormalization()(x)
    x = layers.Convolution1D(128, 1, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Convolution1D(1024, 1, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=num_points)(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(9, weights=[np.zeros([256, 9]), np.array([1, 0, 0, 0, 1, 0, 0, 0, 1]).astype(np.float32)])(x)
    input_T = layers.Reshape((3, 3))(x)

    # forward net
    g = layers.Lambda(mat_mul, arguments={'B': input_T})(input_points)
    g = layers.Convolution1D(64, 1, input_shape=input_shape, activation='relu')(g)
    g = layers.BatchNormalization()(g)
    g = layers.Convolution1D(64, 1, input_shape=input_shape, activation='relu')(g)
    g = layers.BatchNormalization()(g)

    # feature transform net
    f = layers.Convolution1D(64, 1, activation='relu')(g)
    f = layers.BatchNormalization()(f)
    f = layers.Convolution1D(128, 1, activation='relu')(f)
    f = layers.BatchNormalization()(f)
    f = layers.Convolution1D(1024, 1, activation='relu')(f)
    f = layers.BatchNormalization()(f)
    f = layers.MaxPooling1D(pool_size=num_points)(f)
    f = layers.Dense(512, activation='relu')(f)
    f = layers.BatchNormalization()(f)
    f = layers.Dense(256, activation='relu')(f)
    f = layers.BatchNormalization()(f)
    f = layers.Dense(64 * 64, weights=[np.zeros([256, 64 * 64]), np.eye(64).flatten().astype(np.float32)])(f)
    feature_T = layers.Reshape((64, 64))(f)

    # forward net
    g = layers.Lambda(mat_mul, arguments={'B': feature_T})(g)
    g = layers.Convolution1D(64, 1, activation='relu')(g)
    g = layers.BatchNormalization()(g)
    g = layers.Convolution1D(128, 1, activation='relu')(g)
    g = layers.BatchNormalization()(g)
    g = layers.Convolution1D(1024, 1, activation='relu')(g)
    g = layers.BatchNormalization()(g)

    # global_feature
    global_feature = layers.MaxPooling1D(pool_size=num_points)(g)

    # point_net_cls
    c = layers.Dense(512, activation='relu')(global_feature)
    c = layers.BatchNormalization()(c)
    c = layers.Dropout(rate=0.7)(c)
    c = layers.Dense(256, activation='relu')(c)
    c = layers.BatchNormalization()(c)
    c = layers.Dropout(rate=0.7)(c)
    #c = layers.Dense(k, activation='softmax')(c)
    c = layers.Dense(output_size, activation='linear')(c)
    prediction = layers.Flatten()(c)

    model = models.Model(inputs=input_points, outputs=prediction)
    return model
