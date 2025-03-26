import os
import pandas as pd
from fuzzywuzzy import process
import re
from datetime import datetime

# Define the directory containing the Excel files
directory = r"C:\Users\irina\Project Element\Data source\TGN\TGN_raw_fin"

# Define the expected reporting dates (column headers)
reporting_dates = [
    "31/03/2019", "30/06/2019", "30/09/2019", "31/12/2019",
    "31/03/2020", "30/06/2020", "30/09/2020", "31/12/2020",
    "31/03/2021", "30/06/2021", "30/09/2021", "31/12/2021",
    "31/03/2022", "30/06/2022", "30/09/2022", "31/12/2022",
    "31/03/2023", "30/06/2023", "30/09/2023", "31/12/2023",
    "31/03/2024", "30/06/2024", "30/09/2024", "31/12/2024"
]

# Define metric lists
bs_metrics = ["Imobilizări corporale", "Drepturi de utilizare a activelor luate in leasing", "Imobilizări necorporale",
              "Fond comercial", "Creanţe comerciale şi alte creanţe", "Impozit amânat ", "Numerar restrictionat",
              "Active imobilizate totale", "Active circulante", "Stocuri", "Creanţe comerciale şi  alte creanţe",
              "Numerar şi echivalent de numerar", "Active circulante totale", "Active totale",
              "CAPITALURI PROPRII ŞI DATORII", "Capitaluri proprii", "Capital social",
              "Ajustări ale capitalului social la hiperinflaţie", "Primă de emisiune", "Alte rezerve",
              "Rezultat reportat", "Diferențe de conversie din consolidare", "Capitaluri proprii totale",
              "Capitaluri proprii atribuibile asociaților", "Interese fără control", "Datorii pe termen lung",
              "Imprumuturi pe termen lung", "Provizion pentru beneficiile angajaţilor", "Venituri înregistrate în avans",
              "Impozit amânat de plată", "Datorii comerciale şi alte datorii",
              "Datorii aferente drepturilor de utilizare a activelor luate în leasing", "Datorii pe termen lung totale",
              "Datorii curente", "Datorii comerciale şi alte datorii", "Venituri înregistrate în avans",
              "Provizion pentru riscuri şi cheltuieli", "Împrumuturi pe termen scurt", "Provizion pentru beneficiile angajaţilor",
              "Datorii aferente drepturilor de utilizare a activelor luate în leasing", "Impozit curent de plată",
              "Datorii curente totale", "Datorii totale", "Capitaluri proprii şi datorii totale"]

pl_metrics = ["Venituri din activitatea de transport intern", "Venituri din activitatea de transport internaţional și asimilate",
              "Alte venituri", "Venituri din exploatare inainte de activitatea de constructii conform cu IFRIC12 si echilibrare",
              "Amortizare", "Cheltuieli cu angajaţii ", "Consum gaze SNT, materiale şi consumabile utilizate ",
              "Cheltuieli cu redevenţe", "Întreţinere şi transport", "Impozite şi alte sume datorate statului",
              "Venituri/Cheltuieli cu provizionul pentru riscuri şi cheltuieli", "Alte cheltuieli de exploatare ",
              "Profit din exploatare inainte de activitatea de constructii conform cu IFRIC12",
              "Venituri din activitatea de echilibrare", "Cheltuieli din activitatea de echilibrare",
              "Venituri din activitatea de constructii conform cu IFRIC12", "Costul activelor construite conform cu IFRIC12",
              "Profit din exploatare", "Venituri financiare ", "Cheltuieli financiare ", "Venituri financiare, net",
              "Profit înainte de impozitare", "Cheltuiala cu impozitul pe profit ", "Profit net aferent perioadei ",
              "Atribuibil societăţii mamă", "Atribuibil intereselor care nu controlează",
              "Rezultatul pe acţiune, de bază şi diluat  (exprimat în lei pe acţiune)",
              "(Câștig)/Pierdere actuarială aferentă perioadei", "Diferențe de conversie",
              "Rezultatul global total aferent perioadei", "Atribuibil societăţii mamă", "Atribuibil intereselor care nu controlează"]

cf_metrics = ['Profit înainte de impozitare','Ajustări pentru:','Câştig/(pierdere) din cedarea de mijloace fixe ','Provizioane pentru riscuri şi cheltuieli',' Venituri din taxe de racordare, fonduri nerambursabile  și bunuri preluate cu titlu gratuit','Ajustarea Creanta privind Acordul de Concesiune','Pierdere din creante si debitori diversi','Pierdere/ (castig) din deprecierea stocurilor','Ajustări pentru deprecierea creanţelor ','Venituri din dobânzi','Cheltuieli din dobânzi','Alte venituri / cheltuieli','Profit din exploatare înainte de modificările în','   capitalul circulant','(Creştere)/descreştere stocuri ','Numerar generat din exploatare','Dobânzi plătite','Impozit pe profit plătit','   activitatea de exploatare','Flux de trezorerie din activităţi de ','Plăţi pentru achiziţia de imobilizări necorporale','Incasări din cedarea de imobilizări corporale','Numerar din taxe de racordare şi fonduri nerambursabile','Numerar net utilizat în activităţi de  investiţii','Flux de trezorerie din activităţi de    finanţare','Majorare capital social','Trageri imprumuturi pe termen lung','Rambursări împrumuturi termen lung','Trageri/rambursări credit pentru capital de lucru','Plăți IFRS 16','Dividende plătite','Numerar net utilizat în activităţi de','    finanţare','Modificarea netă a numerarului şi ','   echivalentului de numerar','Numerar şi echivalent de numerar '
]

# Create empty DataFrames
df_bs = pd.DataFrame(index=bs_metrics, columns=reporting_dates).infer_objects(copy=False).fillna(0)
df_pl = pd.DataFrame(index=pl_metrics, columns=reporting_dates).infer_objects(copy=False).fillna(0)
df_cf = pd.DataFrame(index=cf_metrics, columns=reporting_dates).infer_objects(copy=False).fillna(0)

# Process each file in chronological order
files = sorted([f for f in os.listdir(directory) if f.endswith(".xlsx")])

for file in files:
    file_path = os.path.join(directory, file)
    xls = pd.ExcelFile(file_path)

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)

        # Extract the first row (should contain the dates)
        date_columns = df.iloc[0].dropna().astype(str).tolist()
        def normalize_date_format(date):
            try:
                # If the date is in "YYYY-MM-DD HH:MM:SS" format, convert it
                dt = pd.to_datetime(date, errors='coerce')
                if not pd.isna(dt):
                    return dt.strftime("%d/%m/%Y")  # Convert to "DD/MM/YYYY"
            except:
                pass
            return date.strip()  # If conversion fails, return as is

        date_columns = [normalize_date_format(col) for col in date_columns]
       
        date_columns.insert(0, "Metric")
          
        if len(date_columns) != df.shape[1]:
            print(f"⚠️ Column mismatch in {sheet}: Expected {df.shape[1]} columns, found {len(date_columns)}")
            continue  # Skip this sheet

        # Set the correct column names
        df.columns = date_columns
        df = df.iloc[1:].reset_index(drop=True)  # Drop the first row and reset index

        # Debugging: Print extracted column names to check if the fix works
        print(f"✅ {sheet}: Normalized Columns -> {df.columns.tolist()}")
        
        # Determine which financial statement
        if "BS" in sheet:
            df_target = df_bs
        elif "PL" in sheet:
            df_target = df_pl
        elif "CF" in sheet:
            df_target = df_cf
        else:
            continue

        # Process each row and insert data
        for _, row in df.iterrows():
            metric = str(row["Metric"]).strip()
            if metric not in df_target.index:
                print(f"Skipping metric '{metric}' in {sheet}")
                continue

            for period in date_columns:
                value = row[period]

                # Convert to float if necessary
                if isinstance(value, str):
                    try:
                        value = float(value.replace(',', '.'))
                    except ValueError:
                        value = 0

                # Store in DataFrame
                if period in df_target.columns:
                    if isinstance(value, pd.Series):
                        value=value.iloc[0]
                    df_target.at[metric, period] = value

# Save the final aggregated data
output_path = os.path.join(directory, "TGN_c_aggregated.xlsx")
with pd.ExcelWriter(output_path) as writer:
    df_bs.to_excel(writer, sheet_name="Balance Sheet")
    df_pl.to_excel(writer, sheet_name="Profit & Loss")
    df_cf.to_excel(writer, sheet_name="Cash Flow")

print(f"✅ Data successfully aggregated and saved to {output_path}")