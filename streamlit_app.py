import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# IMPORT + FILTER DATA
conn = st.connection("gsheets", type=GSheetsConnection)

dataurl = "https://docs.google.com/spreadsheets/d/1r1KE8qTZrl8nWASkyDKR27eVKH-PKX7gFcXxpzHz-Qc/edit?gid=1314983227#gid=1314983227"
itemsurl = "https://docs.google.com/spreadsheets/d/1r1KE8qTZrl8nWASkyDKR27eVKH-PKX7gFcXxpzHz-Qc/edit?gid=1284752657#gid=1284752657"

aledata = conn.read(spreadsheet=dataurl)
aleitems = conn.read(spreadsheet=itemsurl)

aledata_df = pd.DataFrame(data=aledata)
aleitems_df = pd.DataFrame(data=aleitems)

# HEADER

st.set_page_config(page_title='ALE Sales Dashboard',  layout='wide', page_icon='🎮')

t1, t2 = st.columns((0.2,1),vertical_alignment='center')
t1.image('images/logo.png', width=160)
t2.title("Alienware Longhorn Esports (ALE) Sales Dashboard")

aledata_df["date"] = pd.to_datetime(aledata_df["Date"])
min_date = aledata_df["date"].min()

# FILTERS

# f1, f2, f3, f4 = st.columns((1,1,1,0.5),vertical_alignment='bottom')

def reset_filters():
    st.session_state.product_selection = []
    st.session_state.start_date = min_date
    st.session_state.end_date = datetime.today()

with st.sidebar:
    st.header('Dashboard Filters')
    itemname = st.multiselect('Filter by Product',aleitems_df,default=None,key='product_selection')
    startdate = st.date_input('Start Date',value=min_date,key='start_date',format="MM/DD/YYYY",help="Earliest transaction: 8/21/2023")
    enddate = st.date_input('End Date',key='end_date',format="MM/DD/YYYY")
    st.button("Reset Filters",type="primary",on_click=reset_filters,use_container_width=True)

## SOME QUICK FORMATTING FOR CURRENT AND LATER SECTIONS
aledata_df["Date"] = pd.to_datetime(aledata_df["Date"], errors="coerce")
aledata_df["Time"] = pd.to_datetime(aledata_df["Time"], errors="coerce")

aledata_df = aledata_df.rename(columns={"Price": "Revenue"})
aledata_df['YearMonth'] = aledata_df["Date"].dt.to_period("M")
aledata_df["Revenue"] = (
    aledata_df["Revenue"]
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
    .astype(float)
)

showdata_df = aledata_df[
    (aledata_df["Date"] >= pd.to_datetime(startdate)) &
    (aledata_df["Date"] <= pd.to_datetime(enddate))
]
if itemname:
    showdata_df=showdata_df[showdata_df["Product Name"].isin(itemname)]

## TEMP FILTER OUTPUTS

# z1, z2, z3, z4 = st.columns((1,1,1,0.5))
# with z1: st.write("Product Filter:", itemname)
# with z2: st.write("Product Filter:", startdate)
# with z3: st.write("Product Filter:", enddate)

# HERO STATISTICS

h1, h2 = st.columns((0.4,1),vertical_alignment='center')

total_rev = aledata_df['Revenue'].sum()
scope_rev = showdata_df['Revenue'].sum()
ytd_rev = aledata_df[aledata_df["YearMonth"].dt.year >= datetime.now().year]['Revenue'].sum()

delta_yr = datetime.now() - timedelta(days=365)

lastytd_rev = aledata_df[
    (aledata_df["Date"] <= delta_yr) &
    (aledata_df["YearMonth"].dt.year > datetime.now().year-2)
]['Revenue'].sum()
ytd_rev_delta = ytd_rev-lastytd_rev

total_rev = f"{total_rev:,.2f}"
ytd_rev = f"{ytd_rev:,.2f}"
ytd_rev_delta = f"{ytd_rev_delta:,.2f}"
scope_rev = f"{scope_rev:,.2f}"

h1.metric(label ='Total Revenue',value = "$"+str(total_rev))
h1.metric(label ='YTD Revenue',value = "$"+str(ytd_rev),delta = "$"+ytd_rev_delta+" since "+str(datetime.now().year-1))
if total_rev != scope_rev:
    h1.metric(label = 'Filtered Revenue',value = "$"+str(scope_rev))
elif total_rev == scope_rev:
    h1.badge("Adjust filters to show **filtered revenue**", icon=":material/filter_alt:", color="blue")


monthly_data = showdata_df.groupby("YearMonth")["Revenue"].sum().reset_index()
monthly_data["YearMonth"] = monthly_data["YearMonth"].astype(str)  # convert to string for Plotly

fig = px.bar(
    monthly_data, 
    x="YearMonth", 
    y="Revenue",
    labels={"YearMonth": "Month", "Revenue": "Total Revenue"},
    template="seaborn"
)
fig.update_layout(
    yaxis=dict(
        tickprefix="$",   # adds $ before each tick
        tickformat=",",   # adds thousand separator
    )
)
h2.plotly_chart(fig,use_container_width=True)

