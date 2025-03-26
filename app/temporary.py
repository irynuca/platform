import pandas as pd

file_path = "C:/Users/irina/Project Element/Data source/TGN/TGN_raw_fin/TGN_Situatii fin_conso 31.03.2023.xlsx"
xls = pd.ExcelFile(file_path)

print(xls.sheet_names)  # Print all sheet names in the file

df = pd.read_excel(xls, sheet_name=xls.sheet_names[1], header=None)  # Read the first sheet
print(df.head(10))  # Display the first 10 rows