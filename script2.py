import sys
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
import pandas as pd
import json
import os

# Ignore all warnings
warnings.filterwarnings('ignore')

script_name = sys.argv[0]
child_id = None
n_months = None

if len(sys.argv) >= 3:
    child_id = int(sys.argv[1])
    n_months = int(sys.argv[2])

if len(sys.argv) == 2:
    child_id = int(sys.argv[1])

if not isinstance(child_id, int):
    child_id = 10006

if not isinstance(n_months, int):
    n_months = 2

# Update the paths to your Excel files
processed_data = pd.read_excel('processed_data.xlsx')
wfa_m = pd.read_excel('wfa_m.xlsx')
wfa_f = pd.read_excel('wfa_f.xlsx')
hfa_m = pd.read_excel('hfa_m.xlsx')
hfa_f = pd.read_excel('hfa_f.xlsx')

data = processed_data[processed_data['CHILD-ID'] == child_id]
data = data.sort_values(by=['AGE'])

height_result = {}
weight_result = {}


def find_inconsistent_heighted_childs(data):

    current_child = None
    prev_height = None
    include_child = True
    for index, row in data.iterrows():
        child_id = row['CHILD-ID']
        height = row['HEIGHT']

        if current_child is not None and child_id != current_child:
            if not include_child:
                print("Cannot process child due to inconsistency in the data")
                return False
            include_child = True

        if current_child is None or child_id != current_child:
            current_child = child_id
            prev_height = height
        else:
            if height < prev_height:
                include_child = False
                print("Cannot process child due to inconsistency in the data")
                return False

    return True

def find_inconsistent_out_of_range_childs(data):
    for idx, row in data.iterrows():
      day = row['AGE']
      gender = row['GENDER']
      weight = row['WEIGHT']
      height = row['HEIGHT']

      if gender == 'M':
          if weight < wfa_m[wfa_m['Day'] == day]['SD4neg'].values[0] or weight > wfa_m[wfa_m['Day'] == day]['SD4'].values[0]:
              print(f"CHILD-{child_id} is lying out of the recommended possible weight range of WHO")
              return False
          elif height < hfa_m[hfa_m['Day'] == day]['SD4neg'].values[0] or height > hfa_m[hfa_m['Day'] == day]['SD4'].values[0]:
              print(f"CHILD-{child_id} is lying out of the recommended possible height range of WHO")
              return False
      else:
          if weight < wfa_f[wfa_f['Day'] == day]['SD4neg'].values[0] or weight > wfa_f[wfa_f['Day'] == day]['SD4'].values[0]:
              print(f"CHILD-{child_id} is lying out of the recommended possible weight range of WHO")
              return False
          elif height < hfa_f[hfa_f['Day'] == day]['SD4neg'].values[0] or height > hfa_f[hfa_f['Day'] == day]['SD4'].values[0]:
              print(f"CHILD-{child_id} is lying out of the recommended possible weight range of WHO")
              return False
    return True

def sarima_forecast(child_data, child_id, target_column, n_months):
    if len(child_data) < 5:
        print(f"Not enough data for CHILD-ID {child_id}")
        return

    global weight_result, height_result

    child_data.sort_values(by='CAPTURE-DATE', inplace=True)

    last_capture_date = child_data['CAPTURE-DATE'].max()

    dob = child_data['DOB'].values[0]

    train_data = child_data

    model = SARIMAX(train_data[target_column], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    model_fit = model.fit()

    forecast = model_fit.get_forecast(steps=n_months)

    if forecast.predicted_mean.empty:
        print(f"No forecast data for CHILD-ID {child_id}")
        return

    forecast_dates = pd.date_range(start=last_capture_date, periods=n_months + 1, freq='M')[1:]

    for date, value in zip(forecast_dates, forecast.predicted_mean):
        age = (date - dob).days
        if target_column == 'WEIGHT':
            weight_result[age] = value
        else:
            height_result[age] = value

flag1 = find_inconsistent_heighted_childs(data)
flag2 = find_inconsistent_out_of_range_childs(data)

if flag1 == False or flag2 == False:
    print("Inconsistent Child Data")
    height_result[0]=-1
    weight_result[0]=-1
else:
    sarima_forecast(data, child_id, 'WEIGHT', n_months)
    sarima_forecast(data, child_id, 'HEIGHT', n_months)

if os.path.exists('forecast_result.json'):
    try:
        os.remove('forecast_result.json')
        print("Deleted existing forecast_result.json")
    except Exception as e:
        print(f"Error deleting forecast_result.json: {e}")


data_str_dates = data.copy()
data_str_dates['CAPTURE-DATE'] = data_str_dates['CAPTURE-DATE'].dt.strftime('%d-%m-%Y')
data_str_dates['DOB'] = data_str_dates['DOB'].dt.strftime('%d-%m-%Y')

# Combine the original data with forecast results
combined_data = {"original_data": data_str_dates.to_dict(orient='records'),
                 "forecast_result": {"weight_result": weight_result, "height_result": height_result}}

# Write the combined data to a JSON file
with open('forecast_result.json', 'w') as json_file:
    json.dump(combined_data, json_file)
