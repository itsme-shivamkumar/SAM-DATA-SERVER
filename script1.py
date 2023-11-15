import pandas as pd
import os

files_to_delete = ['processed_data.xlsx', 'wfa_m.xlsx', 'wfa_f.xlsx', 'hfa_m.xlsx', 'hfa_f.xlsx']

for file_name in files_to_delete:
    if os.path.exists(file_name):
        os.remove(file_name)

def add_zscore_columns(child_data, wfa, hfa):
    data1 = pd.merge(child_data, wfa.add_suffix('_w'), left_on=['AGE'], right_on=['Day_w'], how='left')
    data1 = pd.merge(data1, hfa.add_suffix('_h'), left_on=['AGE'], right_on=['Day_h'], how='left')
    wfa.columns=wfa.columns.str.replace('_w','')
    hfa.columns=hfa.columns.str.replace('_h','')
    return data1

def preprocess_dataset(data, wfa_m, wfa_f, hfa_m, hfa_f):
    data['AGE'] = (data['HEIGHT/WEIGHT CAPTURE DATE'] - data['DOB']).dt.days
    data.rename(columns={'HEIGHT/WEIGHT CAPTURE DATE': 'CAPTURE-DATE'}, inplace=True)

    data_m = data[data['GENDER'] == 'M']
    data_f = data[data['GENDER'] == 'F']

    data_m = add_zscore_columns(data_m, wfa_m, hfa_m)
    data_f = add_zscore_columns(data_f, wfa_f, hfa_f)

    result_data = pd.concat([data_m, data_f], axis=0)

    return result_data

# Load the data and z-score tables
og_data = pd.read_excel('https://github.com/itsme-shivamkumar/SAM-Data-Analysis/raw/b14656bb6221ef7bd14986c07272c031fcb8f573/Dataset/dataset-child-v1.xlsx')
wfa_m = pd.read_excel('https://github.com/itsme-shivamkumar/SAM-Data-Analysis/raw/main/WHO-Dataset/wfa-boys-zscore-expanded-tables.xlsx')
wfa_f = pd.read_excel('https://github.com/itsme-shivamkumar/SAM-Data-Analysis/raw/main/WHO-Dataset/wfa-girls-zscore-expanded-tables.xlsx')
hfa_m = pd.read_excel('https://github.com/itsme-shivamkumar/SAM-Data-Analysis/raw/main/WHO-Dataset/lhfa-boys-zscore-expanded-tables.xlsx')
hfa_f = pd.read_excel('https://github.com/itsme-shivamkumar/SAM-Data-Analysis/raw/main/WHO-Dataset/lhfa-girls-zscore-expanded-tables.xlsx')

# Preprocess the dataset
og_data=og_data[['CHILD-ID','DOB','GENDER','HEIGHT','WEIGHT','HEIGHT/WEIGHT CAPTURE DATE','zscor']]
processed_data = preprocess_dataset(og_data, wfa_m, wfa_f, hfa_m, hfa_f)
processed_data = processed_data[['CHILD-ID','DOB','GENDER','CAPTURE-DATE','SD4neg_h','SD3neg_h','SD2neg_h',
                                 'SD1neg_h','SD0_h','SD1_h','SD2_h','SD3_h','SD4_h','SD4neg_w','SD3neg_w','SD2neg_w','SD1neg_w','SD0_w','SD1_w',
                                 'SD2_w','SD3_w','SD4_w','AGE','HEIGHT','WEIGHT','zscor']]

# Save processed data to Excel
processed_data.to_excel('processed_data.xlsx', index=False)

# Save z-score tables to Excel
wfa_m.to_excel('wfa_m.xlsx', index=False)
wfa_f.to_excel('wfa_f.xlsx', index=False)
hfa_m.to_excel('hfa_m.xlsx', index=False)
hfa_f.to_excel('hfa_f.xlsx', index=False)