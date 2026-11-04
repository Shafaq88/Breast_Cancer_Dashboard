# Breast Cancer Insights Dashboard

An interactive Streamlit dashboard based on the analyses in `Breast_Cancer (1).ipynb`. It explores patient age, race, marital status, tumor size, T/N/6th stage, grade and differentiation, receptor status, regional lymph nodes, survival months, and recorded status.

## Set up on Windows

Create the virtual environment once, install the packages, then start the dashboard:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Upload `Breast_Cancer.csv` in the dashboard sidebar, or put it in this folder or a `data/` folder. The notebook reads `/content/Breast_Cancer.csv`, but that CSV was not included in the project files. Until it is supplied, the app shows a visual preview from the notebook's saved aggregate outputs.

## Views

- **Overview:** patient count, recorded status share, age and tumor-size summaries, survival months by status, age versus tumor size, and cohort-specific descriptive findings.
- **Stage & nodes:** stage distribution, status mix by stage, tumor-size spread by stage, and regional node comparisons.
- **Clinical characteristics:** age distribution, estrogen/progesterone status, and status comparisons across demographic and clinical fields.
- **Data quality:** exact duplicates, missing cells, IQR bounds and outlier count, column profiles, and correlations among numeric fields.

Sidebar filters update all charts. The tumor-size IQR exclusion is optional and off by default so the initial view retains the full deduplicated cohort. Results describe this dataset and are not individual prognosis or clinical advice.
# Breast_Cancer_Dashboard
# Breast_Cancer_Dashboard
