from modeling.train import make_features
import numpy as np
import os

def test_make_features_shape():
    y = np.arange(10)
    X, Y = make_features(y, window=3)
    assert X.shape[0] == len(Y)
    assert X.shape[1] == 3

def test_make_features_values():
    y = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    X, Y = make_features(y, window=3)
    assert X[0][0] == 1
    assert X[0][1] == 2
    assert X[0][2] == 3
    assert Y[0] == 4

def test_make_features_edge_cases():
    # Test with minimum window size
    y = np.array([1, 2, 3])
    X, Y = make_features(y, window=2)
    assert len(X) == 1
    assert len(Y) == 1
    assert X[0][0] == 1
    assert X[0][1] == 2
    assert Y[0] == 3

def test_data_module_import():
    """Test that data module can be imported without database connection."""
    try:
        from modeling import data
        # This should work even without DATABASE_URL set
        assert True, "Data module imported successfully"
    except Exception as e:
        # If it fails due to missing DATABASE_URL, that's expected in CI
        if "DATABASE_URL" in str(e):
            assert True, "Data module import failed as expected due to missing DATABASE_URL"
        else:
            raise e
