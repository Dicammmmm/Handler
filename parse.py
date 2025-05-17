import re
import io
import pandas as pd
from datetime import datetime

# Function to normalize column names
def standardize_columns(df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    re_pattern = re.compile(r'[^a-zA-Z0-9]+')

    df['timestamp'] = now
    df.columns = [
        re_pattern.sub('_', str(col).lower()).strip('_')
        for col in df.columns
    ]

    return df

# Load the attachment into a Pandas dataframe
def get_attachment(data):
    # Try to read attachment as CSV
    try:
        df = pd.read_csv(io.BytesIO(data))
        return df
    except Exception as e:
        print(e)
        pass

    # Try to read attachment as CSV
    try:
        df = pd.read_excel(io.BytesIO(data), engine='xlrd')
        return df

    except Exception as e:
        print(e)
        pass

    # If unable to read return None
    return None

# Brand specific processing function
def examplebrand(data):
    df = get_attachment(data)

    df = standardize_columns(df)

    return df
