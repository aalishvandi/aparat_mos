import pandas as pd
import numpy as np

# Read the CSV file into a DataFrame
df = pd.read_csv('../output.csv')

# Assume the column with continuous values is named 'Values'
# Define a function to round to the nearest 0.5
def round_to_nearest_half(x):
    return np.round(x * 2) / 2

df = df.drop('number', axis=1)

# Apply the function to the 'Values' column
# df['Rounded_MOS_normal'] = (df['MOS'].round()).astype(int)
# df['Rounded_MOS'] = np.round(df['MOS'] * 4) / 4
# df['Rounded_MOS'] = df['MOS'].apply(round_to_nearest_half)
# df['Rounded_MOS_normal'] = (df['Rounded_MOS']*4).astype(int)

# Optionally, save the DataFrame back to a new CSV file
df.to_csv('../output.csv', index=False)

