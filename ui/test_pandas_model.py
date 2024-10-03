#E:\UDH\Compiler\ui\test_pandas_model.py

import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from pandas_model import PandasModel  # Adjust import based on your structure

def test_pandas_model():
    # Create a sample DataFrame
    data = {
        "Column1": [1, 2, 3],
        "Column2": [4, 5, 6],
    }
    df = pd.DataFrame(data)

    # Initialize the application
    app = QApplication(sys.argv)

    # Create the PandasModel instance
    model = PandasModel(df)

    # Test the row count
    assert model.rowCount() == 3, "Row count should be 3"

    # Test the column count
    assert model.columnCount() == 2, "Column count should be 2"

    # Test data retrieval
    assert model.data(model.index(0, 0)) == "1", "Data at (0, 0) should be 1"
    assert model.data(model.index(1, 1)) == "5", "Data at (1, 1) should be 5"

    print("All tests passed!")

if __name__ == "__main__":
    test_pandas_model()
