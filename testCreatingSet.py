import pandas as pd


def combine_dataframes(df1, df2):
    combined_records = []
    for i, row1 in df1.iterrows():
        for j, row2 in df2.iterrows():
            combined_record = {
                'Name1': row1['Name'],
                'Name2': row2['Name'],
                'Health': row1['Health'] + row2['Health'],
                'Damage': row1['Damage'] + row2['Damage'],
                'Resist': row1['Resist'] + row2['Resist'],
                'Source1': row1['Source'],
                'Source2': row2['Source'],
                'Owned1': row1['Owned'],
                'Owned2': row2['Owned']
            }
            combined_records.append(combined_record)
    return pd.DataFrame(combined_records)