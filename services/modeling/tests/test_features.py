from modeling.train import make_features
import numpy as np

def test_make_features_shape():
    y = np.arange(10)
    X, Y = make_features(y, window=3)
    assert X.shape[0] == len(Y)
    assert X.shape[1] == 3
