import numpy as np
import pandas as pd
from joblib import Parallel, delayed


def check_dominance(points, i):
    """
    Helper function to check if point i is dominated by any other point.
    
    Parameters:
    points (np.array): Array of points with each point having several statistics.
    i (int): Index of the point to check.
    
    Returns:
    bool: True if point i is dominated by any other point, else False.
    """
    for j, point in enumerate(points):
        if i != j and np.all(point >= points[i]) and np.any(point > points[i]):
            return True
    return False

def pareto_efficient_parallel(points, n_jobs=-1):
    """
    Find the Pareto efficient points using parallel processing.
    
    Parameters:
    points (np.array): Array of points with each point having several statistics.
    n_jobs (int): The number of jobs to run in parallel. -1 means using all processors.
    
    Returns:
    np.array: Boolean array where True indicates a Pareto efficient point.
    """
    results = Parallel(n_jobs=n_jobs)(delayed(check_dominance)(points, i) for i in range(len(points)))
    is_efficient = np.logical_not(results)
    return is_efficient

def filter_pareto_efficient(df, n_jobs=-1):
    """
    Filters the dataframe to remove items that are dominated by others using parallel processing.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing the items and their statistics.
    n_jobs (int): The number of jobs to run in parallel. -1 means using all processors.
    
    Returns:
    pd.DataFrame: Filtered DataFrame with only Pareto efficient items.
    """
    points = df.iloc[:, 1:].values  # Exclude the first column which is 'Item'
    efficient_mask = pareto_efficient_parallel(points, n_jobs)
    return df[efficient_mask].reset_index(drop=True)

def main():
    # Example dataframe
    df = pd.DataFrame({
        'Item': ['Item_1', 'Item_2', 'Item_3', 'Item_4', 'Item_5'],
        'Stat_1': [15, 10, 12, 8, 11],
        'Stat_2': [20, 18, 16, 22, 19],
        'Stat_3': [18, 14, 17, 13, 15]
    })

    # Apply the filter function
    filtered_df = filter_pareto_efficient(df)
    print(filtered_df)
    
if __name__ == "__main__":
    main()