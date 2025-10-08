import pytest
import pandas as pd
from load_data import clean_data

@pytest.fixture
def sample_data():
    """Fixture to provide sample data for testing."""
    data = {
        "Review_Id": [1, 2, 2, 3],
        "Review_Date": ["2023-01-01", "invalid_date", "2023-01-02", "2023-01-03"],
        "Review_Rating": [5, 6, 4, "invalid_rating"],
    }
    return pd.DataFrame(data)

def test_clean_data(sample_data):
    """Test the clean_data function."""
    cleaned_data = clean_data(sample_data)
    assert len(cleaned_data) == 1  # Only valid rows should remain
    assert all(cleaned_data["Review_Rating"].between(1, 5))  # Ratings should be valid
    assert pd.api.types.is_datetime64_any_dtype(cleaned_data["Review_Date"])  # Dates should be valid
