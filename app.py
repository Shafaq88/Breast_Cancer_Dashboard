from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Breast Cancer Insights",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink: #172b4d; --muted: #6b7c93; --line: #e6ebf2; --blue: #6d4aff; }
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
    .stApp { background: #f6f7fb; color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(246,247,251,.92); }
    [data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
    [data-testid="stMetric"] { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 18px 20px; box-shadow: 0 4px 16px rgba(23,43,77,.035); }
    [data-testid="stMetricLabel"] { color: var(--muted); font-size: .84rem; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    .hero { padding: 8px 0 14px; }
    .eyebrow { color: var(--blue); font-weight: 700; letter-spacing: .1em; text-transform: uppercase; font-size: .74rem; }
    .hero h1 { font-family: 'Manrope', sans-serif; color: var(--ink); font-size: 2.2rem; margin: 4px 0; }
    .hero p { color: var(--muted); margin: 0; }
    .insight { background: #fff; border: 1px solid var(--line); border-left: 4px solid var(--blue); border-radius: 10px; padding: 14px 16px; margin: 8px 0; color: var(--ink); }
    .notice { background: #f0edff; border: 1px solid #ded7ff; border-radius: 12px; padding: 14px 16px; color: #32236f; }
    </style>
    """,
    unsafe_allow_html=True,
)


BLUE = "#6d4aff"
OUTCOME_COLORS = {"Alive": "#16a085", "Dead": "#e45c74"}
STAGE_ORDER = ["IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IIIC", "IV"]
FIELD_ALIASES = {
    "age": ["age"],
    "race": ["race"],
    "marital": ["marital status"],
    "t_stage": ["t stage"],
    "n_stage": ["n stage"],
    "stage": ["6th stage", "sixth stage", "stage"],
    "differentiation": ["differentiate", "differentiation"],
    "grade": ["grade"],
    "a_stage": ["a stage"],
    "tumor_size": ["tumor size"],
    "estrogen": ["estrogen status", "estrogen receptor status"],
    "progesterone": ["progesterone status", "progesterone receptor status"],
    "nodes_examined": ["regional node examined", "regional nodes examined"],
    "nodes_positive": ["reginol node positive", "regional node positive", "regional nodes positive"],
    "survival": ["survival months", "survival month"],
    "status": ["status", "patient status", "survival status"],
}


def normalize_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def find_fields(columns: list[object]) -> dict[str, object | None]:
    normalized = {column: normalize_name(column) for column in columns}
    result = {}
    for key, aliases in FIELD_ALIASES.items():
        result[key] = next(
            (column for alias in aliases for column, name in normalized.items() if name == alias),
            None,
        )
        if result[key] is None:
            result[key] = next(
                (column for alias in aliases for column, name in normalized.items() if alias in name),
                None,
            )
    return result


@st.cache_data(show_spinner=False)
def read_dataset(file_name: str, payload: bytes) -> pd.DataFrame:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(BytesIO(payload))
    try:
        return pd.read_csv(BytesIO(payload), sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(BytesIO(payload), sep=None, engine="python", encoding="latin-1")


def find_local_data() -> Path | None:
    root = Path(__file__).parent
    for folder in (root, root / "data"):
        if folder.exists():
            for path in sorted(list(folder.glob("*.csv")) + list(folder.glob("*.xlsx"))):
                if "breast" in path.name.lower() and "cancer" in path.name.lower():
                    return path
    return None


def palette_for_status(values: list[str]) -> dict[str, str]:
    return {value: OUTCOME_COLORS.get(value, "#7d8ba3") for value in values}


def style_figure(fig, height: int | None = None):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#24344d",
        margin=dict(l=12, r=12, t=54, b=12),
        legend_title_text="",
    )
    if height is not None:
        fig.update_layout(height=height)
    fig.update_xaxes(showgrid=True, gridcolor="#edf0f6", zerolinecolor="#edf0f6")
    fig.update_yaxes(showgrid=False, zerolinecolor="#edf0f6")
    return fig


def add_insight(message: str) -> None:
    with st.container(border=True):
        st.markdown(message)


def render_notebook_snapshot() -> None:
    """Show only aggregates saved in the notebook until the row-level CSV is supplied."""
    st.markdown(
        '<div class="notice"><strong>Notebook summary preview.</strong> Upload the notebook\'s source CSV to enable row-level filters and patient-level charts.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Deduplicated records", "4,023")
    m2.metric("Recorded Alive share", "84.7%")
    m3.metric("Mean age", "54.0 years")
    m4.metric("Mean recorded survival", "71.3 months")
    left, right = st.columns(2)
    with left:
        stage_data = pd.DataFrame(
            {"6th Stage": ["IIA", "IIB", "IIIA", "IIIC", "IIIB"], "Records": [1304, 1130, 1050, 472, 67]}
        )
        fig = px.bar(
            stage_data.sort_values("Records"), x="Records", y="6th Stage", orientation="h",
            title="Records by 6th stage", color_discrete_sequence=[BLUE],
        )
        st.plotly_chart(style_figure(fig, 360), use_container_width=True)
    with right:
        status_data = pd.DataFrame({"Recorded status": ["Alive", "Dead"], "Records": [3407, 616]})
        fig = px.pie(
            status_data, names="Recorded status", values="Records", hole=0.68,
            title="Recorded status distribution", color="Recorded status",
            color_discrete_map=OUTCOME_COLORS,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(style_figure(fig, 360), use_container_width=True)
    st.caption(
        "Notebook summary: 4,024 source rows with one duplicate removed; 16 columns and no missing cells after deduplication; mean tumor size 30.48. "
        "The corrected IQR rule identifies 222 high-end tumor-size outliers (upper bound 71); excluding them leaves 3,801 records."
    )


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Patient cohort · descriptive analysis</div>
      <h1>Breast Cancer Insights</h1>
      <p>Explore patient characteristics, tumor stages, recorded outcomes, and survival-month patterns in the notebook dataset.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "This dashboard describes the supplied dataset. It does not estimate an individual's prognosis or support clinical decisions."
)

with st.sidebar:
    st.markdown("## Patient dataset")
    st.caption("Upload the CSV used by the notebook, or place it in this folder (or `data/`).")
    uploaded = st.file_uploader("Upload source data", type=["csv", "xlsx"], label_visibility="collapsed")
    local_path = find_local_data() if uploaded is None else None

if uploaded is not None:
    source_name = uploaded.name
    try:
        raw = read_dataset(uploaded.name, uploaded.getvalue())
    except Exception as exc:
        st.error(f"Could not read the selected file: {exc}")
        st.stop()
elif local_path is not None:
    source_name = local_path.name
    try:
        raw = read_dataset(local_path.name, local_path.read_bytes())
    except Exception as exc:
        st.error(f"Could not read {local_path.name}: {exc}")
        st.stop()
else:
    render_notebook_snapshot()
    with st.expander("What the notebook analyzed"):
        st.markdown(
            "The saved notebook output has 16 fields: age, race, marital status, T/N/6th stage, tumor differentiation and grade, "
            "anatomic stage, tumor size, estrogen and progesterone status, regional nodes examined and positive, survival months, and recorded status."
        )
        st.markdown(
            "The notebook reads `/content/Breast_Cancer.csv`; that source file is not currently in the project folder. "
            "Upload it above to enable the interactive analysis."
        )
    st.stop()

if raw.empty:
    st.error("The selected dataset has no rows.")
    st.stop()

raw.columns = [str(column).strip() for column in raw.columns]
raw_row_count = len(raw)
duplicate_count = int(raw.duplicated().sum())
df = raw.drop_duplicates().copy()
fields = find_fields(list(df.columns))

numeric_keys = ["age", "grade", "tumor_size", "nodes_examined", "nodes_positive", "survival"]
for key in numeric_keys:
    column = fields[key]
    if column is not None:
        df[column] = pd.to_numeric(df[column], errors="coerce")

required_fields = ["age", "stage", "tumor_size", "survival", "status"]
missing_fields = [key for key in required_fields if fields[key] is None]
if missing_fields:
    st.warning(
        "Some expected notebook fields were not found: " + ", ".join(missing_fields) +
        ". Available charts will adapt to the columns present."
    )

status_col = fields["status"]
stage_col = fields["stage"]
race_col = fields["race"]
age_col = fields["age"]
tumor_col = fields["tumor_size"]
survival_col = fields["survival"]

iqr_bounds = None
outlier_mask = pd.Series(False, index=df.index)
if tumor_col is not None and df[tumor_col].notna().any():
    q1 = float(df[tumor_col].quantile(0.25))
    q3 = float(df[tumor_col].quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    iqr_bounds = (q1, q3, lower_bound, upper_bound)
    outlier_mask = df[tumor_col].lt(lower_bound) | df[tumor_col].gt(upper_bound)

with st.sidebar:
    st.divider()
    st.markdown("### Cohort filters")
    working = df.copy()
    if status_col is not None:
        status_values = sorted(working[status_col].dropna().astype(str).unique().tolist())
        selected_status = st.multiselect("Recorded status", status_values, default=status_values)
        working = working[working[status_col].astype(str).isin(selected_status)]
    if stage_col is not None:
        stage_values = working[stage_col].dropna().astype(str).unique().tolist()
        stage_values = sorted(stage_values, key=lambda value: (STAGE_ORDER.index(value) if value in STAGE_ORDER else len(STAGE_ORDER), value))
        selected_stage = st.multiselect("6th stage", stage_values, default=stage_values)
        working = working[working[stage_col].astype(str).isin(selected_stage)]
    if race_col is not None and working[race_col].nunique(dropna=True) <= 100:
        race_values = sorted(working[race_col].dropna().astype(str).unique().tolist())
        selected_race = st.multiselect("Race", race_values, default=race_values)
        working = working[working[race_col].astype(str).isin(selected_race)]
    if age_col is not None and working[age_col].notna().any():
        age_min = int(working[age_col].min())
        age_max = int(working[age_col].max())
        if age_min < age_max:
            selected_age = st.slider("Age range", min_value=age_min, max_value=age_max, value=(age_min, age_max))
            working = working[working[age_col].between(selected_age[0], selected_age[1])]
    if iqr_bounds is not None:
        exclude_outliers = st.toggle("Exclude tumor-size IQR outliers", value=False)
        if exclude_outliers:
            working = working.loc[~outlier_mask.loc[working.index]]
    else:
        exclude_outliers = False

if working.empty:
    st.warning("No records match the selected filters. Broaden the cohort filters to continue.")
    st.stop()


overview_tab, stage_tab, clinical_tab, quality_tab = st.tabs(
    ["Overview", "Stage & nodes", "Clinical characteristics", "Data quality"]
)

with overview_tab:
    total_records = len(working)
    alive_count = int(working[status_col].astype(str).str.strip().str.casefold().eq("alive").sum()) if status_col is not None else None
    dead_count = int(working[status_col].astype(str).str.strip().str.casefold().eq("dead").sum()) if status_col is not None else None
    status_total = int(working[status_col].notna().sum()) if status_col is not None else 0
    alive_share = alive_count / status_total * 100 if alive_count is not None and status_total else None
    mean_age = float(working[age_col].mean()) if age_col is not None else None
    mean_tumor_size = float(working[tumor_col].mean()) if tumor_col is not None else None
    mean_survival = float(working[survival_col].mean()) if survival_col is not None else None

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Patient records", f"{total_records:,}")
    m2.metric("Recorded Alive share", f"{alive_share:.1f}%" if alive_share is not None else "—")
    m3.metric("Mean age", f"{mean_age:.1f} years" if mean_age is not None else "—")
    m4.metric("Mean tumor size", f"{mean_tumor_size:.2f}" if mean_tumor_size is not None else "—")
    s1, s2, s3 = st.columns(3)
    s1.metric("Recorded Dead", f"{dead_count:,}" if dead_count is not None else "—")
    s2.metric("Mean recorded survival", f"{mean_survival:.1f} months" if mean_survival is not None else "—")
    s3.metric("Tumor-size IQR outliers", f"{int(outlier_mask.sum()):,}" if tumor_col is not None else "—")

    left, right = st.columns(2)
    with left:
        if status_col is not None:
            status_summary = working[status_col].fillna("Unknown").astype(str).value_counts().rename_axis("Status").reset_index(name="Records")
            fig = px.pie(
                status_summary, names="Status", values="Records", hole=0.68,
                title="Recorded status distribution", color="Status",
                color_discrete_map=palette_for_status(status_summary["Status"].tolist()),
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(style_figure(fig, 360), use_container_width=True)
        else:
            st.info("A status field is needed for the outcome distribution chart.")
    with right:
        if survival_col is not None and status_col is not None:
            fig = px.violin(
                working.dropna(subset=[survival_col, status_col]), x=status_col, y=survival_col,
                color=status_col, box=True, points="outliers", color_discrete_map=palette_for_status(working[status_col].dropna().astype(str).unique().tolist()),
                title="Recorded survival months by status",
            )
            fig.update_layout(showlegend=False, xaxis_title="Recorded status", yaxis_title="Survival months")
            st.plotly_chart(style_figure(fig, 360), use_container_width=True)
        else:
            st.info("Status and survival-month fields are needed for this comparison.")

    if age_col is not None and tumor_col is not None:
        plot_data = working.dropna(subset=[age_col, tumor_col])
        hover_fields = [column for column in (stage_col, survival_col) if column is not None]
        fig = px.scatter(
            plot_data, x=age_col, y=tumor_col, color=status_col if status_col is not None else None,
            hover_data=hover_fields, opacity=0.68, color_discrete_map=palette_for_status(plot_data[status_col].dropna().astype(str).unique().tolist()) if status_col is not None else None,
            title="Age and tumor size",
        )
        fig.update_layout(xaxis_title="Age (years)", yaxis_title="Tumor size (dataset units)")
        st.plotly_chart(style_figure(fig, 390), use_container_width=True)

    st.subheader("Patterns in the selected cohort")
    insights = []
    if stage_col is not None:
        stage_counts = working[stage_col].dropna().astype(str).value_counts()
        if not stage_counts.empty:
            share = stage_counts.iloc[0] / total_records * 100
            insights.append(f"The most frequent 6th stage is **{stage_counts.index[0]}** ({stage_counts.iloc[0]:,} records, {share:.1f}% of this cohort).")
    if status_col is not None and survival_col is not None:
        by_status = working.groupby(status_col, dropna=True)[survival_col].mean().dropna()
        if len(by_status) >= 2:
            status_text = " · ".join(f"**{label}**: {value:.1f} months mean recorded survival" for label, value in by_status.items())
            insights.append(f"Recorded survival-month averages by status: {status_text}. This is a descriptive comparison, not a survival probability.")
    if tumor_col is not None and survival_col is not None:
        pair = working[[tumor_col, survival_col]].dropna()
        if len(pair) > 2:
            correlation = pair[tumor_col].corr(pair[survival_col], method="spearman")
            if pd.notna(correlation):
                insights.append(f"Tumor size and recorded survival months have a Spearman correlation of {correlation:.2f} in this selection; this association does not show cause and effect.")
    if not insights:
        insights.append("Choose a cohort using the sidebar filters. Available patterns depend on which notebook fields are present in the data file.")
    for insight in insights:
        add_insight(insight)

with stage_tab:
    st.subheader("Stage distribution and recorded outcomes")
    left, right = st.columns(2)
    with left:
        if stage_col is not None:
            stage_summary = working[stage_col].fillna("Unknown").astype(str).value_counts().rename_axis("Stage").reset_index(name="Records")
            order = [stage for stage in STAGE_ORDER if stage in stage_summary["Stage"].values]
            order.extend(stage for stage in stage_summary["Stage"].values if stage not in order)
            fig = px.bar(stage_summary, x="Stage", y="Records", category_orders={"Stage": order}, title="Patient records by 6th stage", color_discrete_sequence=[BLUE])
            st.plotly_chart(style_figure(fig, 370), use_container_width=True)
        else:
            st.info("A stage field is needed for this view.")
    with right:
        if stage_col is not None and status_col is not None:
            stage_status = working.groupby([stage_col, status_col], dropna=False).size().rename("Records").reset_index()
            stage_totals = stage_status.groupby(stage_col)["Records"].transform("sum")
            stage_status["Share within stage"] = stage_status["Records"] / stage_totals * 100
            order = [stage for stage in STAGE_ORDER if stage in stage_status[stage_col].astype(str).unique()]
            fig = px.bar(
                stage_status, x=stage_col, y="Share within stage", color=status_col,
                category_orders={stage_col: order}, barmode="stack", title="Recorded status mix within each stage",
                color_discrete_map=palette_for_status(stage_status[status_col].dropna().astype(str).unique().tolist()),
                hover_data={"Records": True, "Share within stage": ":.1f"},
            )
            fig.update_layout(yaxis_title="Share of records (%)")
            st.plotly_chart(style_figure(fig, 370), use_container_width=True)
        else:
            st.info("Stage and status fields are needed for the outcome mix by stage.")

    if tumor_col is not None and stage_col is not None:
        fig = px.box(working.dropna(subset=[tumor_col, stage_col]), x=stage_col, y=tumor_col, color=stage_col, points="outliers", title="Tumor-size distribution by 6th stage")
        fig.update_layout(showlegend=False, xaxis_title="6th stage", yaxis_title="Tumor size (dataset units)")
        st.plotly_chart(style_figure(fig, 390), use_container_width=True)

    examined_col = fields["nodes_examined"]
    positive_col = fields["nodes_positive"]
    if examined_col is not None and positive_col is not None:
        node_data = working.dropna(subset=[examined_col, positive_col])
        fig = px.scatter(
            node_data, x=examined_col, y=positive_col,
            color=status_col if status_col is not None else None,
            hover_data=[column for column in (stage_col, tumor_col) if column is not None],
            title="Regional nodes examined and recorded positive",
            color_discrete_map=palette_for_status(node_data[status_col].dropna().astype(str).unique().tolist()) if status_col is not None else None,
            opacity=0.7,
        )
        fig.update_layout(xaxis_title="Regional nodes examined", yaxis_title="Regional nodes positive")
        st.plotly_chart(style_figure(fig, 390), use_container_width=True)

with clinical_tab:
    st.subheader("Age, tumor, and receptor characteristics")
    left, right = st.columns(2)
    with left:
        if age_col is not None:
            fig = px.histogram(
                working.dropna(subset=[age_col]), x=age_col,
                color=status_col if status_col is not None else None,
                marginal="box", barmode="overlay", opacity=0.68, nbins=24,
                color_discrete_map=palette_for_status(working[status_col].dropna().astype(str).unique().tolist()) if status_col is not None else None,
                title="Age distribution by recorded status",
            )
            st.plotly_chart(style_figure(fig, 370), use_container_width=True)
        else:
            st.info("An age field is needed for this view.")
    with right:
        receptor_cols = [column for column in (fields["estrogen"], fields["progesterone"]) if column is not None]
        if receptor_cols:
            receptor_data = working[receptor_cols].melt(var_name="Receptor", value_name="Recorded status")
            receptor_data["Receptor"] = receptor_data["Receptor"].replace({fields["estrogen"]: "Estrogen", fields["progesterone"]: "Progesterone"})
            receptor_summary = receptor_data.value_counts(["Receptor", "Recorded status"]).rename("Records").reset_index()
            fig = px.bar(receptor_summary, x="Receptor", y="Records", color="Recorded status", barmode="group", title="Receptor status records", color_discrete_sequence=[BLUE, "#f4a340", "#8a97ab"])
            st.plotly_chart(style_figure(fig, 370), use_container_width=True)
        else:
            st.info("Estrogen or progesterone status fields were not found.")

    if status_col is not None:
        factor_cols = [column for column in (fields["race"], fields["marital"], fields["grade"], fields["differentiation"], fields["t_stage"], fields["n_stage"], fields["a_stage"]) if column is not None]
        if factor_cols:
            selected_factor = st.selectbox("Compare recorded status by", factor_cols, format_func=lambda col: str(col))
            factor_summary = working.groupby([selected_factor, status_col], dropna=False).size().rename("Records").reset_index()
            fig = px.bar(factor_summary, x=selected_factor, y="Records", color=status_col, barmode="group", title=f"Recorded status by {selected_factor}", color_discrete_map=palette_for_status(factor_summary[status_col].dropna().astype(str).unique().tolist()))
            st.plotly_chart(style_figure(fig, 380), use_container_width=True)

with quality_tab:
    st.subheader("Dataset quality and outlier review")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Rows in source", f"{raw_row_count:,}")
    q2.metric("Exact duplicates removed", f"{duplicate_count:,}")
    q3.metric("Rows analyzed", f"{len(df):,}")
    q4.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")

    if iqr_bounds is not None:
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Tumor-size Q1", f"{iqr_bounds[0]:.1f}")
        q2.metric("Tumor-size Q3", f"{iqr_bounds[1]:.1f}")
        q3.metric("IQR lower bound", f"{iqr_bounds[2]:.1f}")
        q4.metric("IQR upper bound", f"{iqr_bounds[3]:.1f}")
        st.caption(
            f"The standard IQR rule flags {int(outlier_mask.sum()):,} records outside the bounds. "
            "The notebook's first outlier expression used a condition that could not flag values; the corrected outside-range rule is used here."
        )

    quality = pd.DataFrame(
        {
            "Column": df.columns,
            "Type": [str(dtype) for dtype in df.dtypes],
            "Missing": df.isna().sum().values,
            "Unique values": df.nunique(dropna=True).values,
        }
    )
    st.dataframe(quality, use_container_width=True, hide_index=True)

    numeric_columns = [column for column in df.select_dtypes(include="number").columns if df[column].nunique(dropna=True) > 1]
    if len(numeric_columns) >= 2:
        correlation = df[numeric_columns].corr(method="spearman")
        fig = px.imshow(correlation, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title="Spearman correlations across numeric fields")
        st.plotly_chart(style_figure(fig, 510), use_container_width=True)

st.divider()
st.caption(f"Source: {source_name} · {len(working):,} deduplicated records in the selected cohort")
with st.expander("Preview selected records"):
    st.dataframe(working, use_container_width=True, hide_index=True)
