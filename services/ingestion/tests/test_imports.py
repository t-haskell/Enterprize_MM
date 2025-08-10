"""Basic import tests for ingestion service."""

def test_imports():
    """Test that main modules can be imported without errors."""
    try:
        import pandas
        import requests
        import prefect
        import psycopg
        import sqlalchemy
        import confluent_kafka
        import pydantic
        assert True, "All required packages imported successfully"
    except ImportError as e:
        assert False, f"Failed to import required package: {e}"

def test_basic_functionality():
    """Test basic functionality."""
    assert True, "Basic test passes"

def test_pandas_functionality():
    """Test pandas basic functionality."""
    import pandas as pd
    df = pd.DataFrame({'test': [1, 2, 3]})
    assert len(df) == 3
    assert df['test'].sum() == 6

def test_pydantic_functionality():
    """Test pydantic basic functionality."""
    from pydantic import BaseModel
    
    class TestModel(BaseModel):
        name: str
        value: int
    
    model = TestModel(name="test", value=42)
    assert model.name == "test"
    assert model.value == 42 