import pandas as pd
import numpy as np


# Show head
dataset = pd.read_csv(r"side-project\spotify-tracks-dataset\data\dataset.csv")
# print(dataset.head())
# print("Columns:", dataset.columns)


# # Data type
# print(dataset.info())


# # Data cleansing
# print(dataset.isna().sum())
# print(dataset[dataset.isna().any(axis=1)])      # Unnamed K-pop & Zero-duration --> drop
# print(dataset[dataset['duration_ms'] == 0])      # Zero-duration --> drop

# dataset = dataset.dropna()
# dataset = dataset[dataset['duration_ms'] != 0]

# print(dataset.isna().sum())


def cleanse_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the dataset by dropping rows with missing values and zero-duration tracks.

    Args:
        df (pd.DataFrame): The input dataset.

    Returns:
        pd.DataFrame: The cleaned dataset.
    """
    df = df.dropna()
    df = df[df['duration_ms'] != 0]
    return df

dataset = cleanse_dataset(dataset)


# Show distribution of each column
import matplotlib.pyplot as plt
from pathlib import Path


def plot_non_str_columns_distribution(df: pd.DataFrame) -> None:
    """
    Plots the distribution of non-string columns in the dataset.
    Boolean columns are treated as categorical and will be plotted as bar charts.

    Args:
        df (pd.DataFrame): The input dataset.
    """
    non_str_columns = df.select_dtypes(exclude='object').columns
    for column in non_str_columns:
        plt.figure(figsize=(10, 6))
        if df[column].dtype == 'bool':
            df[column].value_counts().plot(kind='bar', color='blue', alpha=0.7)
        else:
            plt.hist(df[column], bins=30, color='blue', alpha=0.7)
        plt.title(f'Distribution of {column}')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        plt.grid(axis='y', alpha=0.75)

        filepath = Path(r"side-project\spotify-tracks-dataset\fig") / f"{column}_distribution.png"
        plt.savefig(filepath)
        plt.close()

def plot_str_columns_distribution(df: pd.DataFrame) -> None:
    """
    Plots the distribution of string columns in the dataset.
    Boolean columns are treated as categorical and will be plotted as bar charts.

    Args:
        df (pd.DataFrame): The input dataset.
    """
    str_columns = df.select_dtypes(include=['object', 'string']).columns
    
    for column in str_columns:
        plt.figure(figsize=(10, 6))
        
        # df values converts into string
        df[column] = df[column].astype(str)

        df[column].value_counts().plot(kind='bar', color='blue', alpha=0.7)
        plt.title(f'Distribution of {column}')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        plt.grid(axis='y', alpha=0.75)

        filepath = Path(r"side-project\spotify-tracks-dataset\fig") / f"{column}_distribution.png"
        plt.savefig(filepath)
        plt.close()

# plot_non_str_columns_distribution(dataset)
# plot_str_columns_distribution(dataset)

# Track genre distribution
dataset['track_genre'].value_counts().plot(kind='bar', figsize=(10, 6), color='blue', alpha=0.7)
plt.title('Distribution of track_genre')
plt.xlabel('Track Genre')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.75)
filepath = Path(r"side-project\spotify-tracks-dataset\fig") / "track_genre_distribution.png"
plt.savefig(filepath)
