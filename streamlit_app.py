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

aledata_df["Date"] = pd.to_datetime(aledata_df["Date"])
min_date = aledata_df["Date"].min()

# FILTERS

# f1, f2, f3, f4 = st.columns((1,1,1,0.5),vertical_alignment='bottom')

def reset_filters():
    st.session_state.product_selection = []
    st.session_state.type_selection = "All"
    st.session_state.start_date = min_date
    st.session_state.end_date = datetime.today()

with st.sidebar:
    st.header('Dashboard Filters')
    itemname = st.multiselect('Filter by Product',aleitems_df,default=None,key='product_selection')
    itemtype = st.selectbox('Filter by Reservations',("General","Reservations","All"),index=2,key='type_selection')
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
if itemtype == 'General':
    showdata_df=showdata_df[showdata_df["Reservation"] == False]
elif itemtype == 'Reservations':
    showdata_df=showdata_df[showdata_df["Reservation"] == True]


## TEMP FILTER OUTPUTS

# z1, z2, z3, z4 = st.columns((1,1,1,0.5))
# with z1: st.write("Product Filter:", itemname)
# with z2: st.write("Product Filter:", startdate)
# with z3: st.write("Product Filter:", enddate)

# HERO STATISTICS

h1, h2, h3 = st.columns((0.25,1,0.4),vertical_alignment='center')

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

fig = px.line(
    monthly_data, 
    x="YearMonth", 
    y="Revenue",
    labels={"YearMonth": "Month", "Revenue": "Total Revenue"},
    title="Revenue per Month (General & Reservations)",
    markers=True,
    template="plotly_white"
)
fig.update_layout(
    yaxis=dict(
        tickprefix="$",   # adds $ before each tick
        tickformat=",",   # adds thousand separator
    )
)
h2.plotly_chart(fig,use_container_width=True)

reservation_rev = showdata_df[showdata_df['Reservation'] == True]['Revenue'].sum()
general_rev = showdata_df[showdata_df['Reservation'] == False]['Revenue'].sum()
rev_pie = {'Type': ['Total', 'General', 'Reservation'], 'Amount': [scope_rev,general_rev,reservation_rev]}
rev_pie_df = pd.DataFrame(data=rev_pie)
fig = px.pie(rev_pie_df, values='Amount', names='Type', title='Revenue Breakdown (General vs. Reservations)')
fig.update_traces(textposition='inside', textinfo='value+label', texttemplate="%{label}<br>$%{value}")
fig.update(layout_showlegend=False)
h3.plotly_chart(fig,use_container_width=True)

p1, p2= st.columns((1,1),vertical_alignment='center')


# Trim reservations from df
# Convert Time to datetime
showdata_df['Time'] = pd.to_datetime(showdata_df['Time'].astype(str))

# Create Hour column in AM/PM format
showdata_df['Hour'] = showdata_df['Time'].dt.strftime('%I %p')  # e.g., "09 AM"

# Group by Hour and sum Revenue
hourly_data = showdata_df.groupby('Hour')['Revenue'].sum().reset_index()

# Keep only the range from first non-zero to last non-zero
nonzero_indices = hourly_data[hourly_data['Revenue'] != 0].index
if len(nonzero_indices) > 0:
    hourly_data = hourly_data.loc[nonzero_indices[0] : nonzero_indices[-1]]

# Sort hours chronologically
hourly_data['Hour_dt'] = pd.to_datetime(hourly_data['Hour'], format='%I %p')
hourly_data = hourly_data.sort_values('Hour_dt')
hourly_data = hourly_data.drop(columns='Hour_dt')

# Plot
fig = px.bar(
    hourly_data,
    x='Hour',
    y='Revenue',
    labels={"Hour": "Hour of Day", "Revenue": "Total Revenue"},
    title="Revenue by Hour (General Sales Only)",
    template="plotly_white"
)

fig.update_layout(
    yaxis=dict(
        tickprefix='$',
        tickformat=',.2f'
    )
)

p1.plotly_chart(fig, use_container_width=True)

showdata_df['Weekday'] = showdata_df['Date'].dt.day_name()
weekday_rev = showdata_df.groupby("Weekday", as_index=False)['Revenue'].sum()

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Make Weekday column categorical with ordered categories
weekday_rev['Weekday'] = pd.Categorical(
    weekday_rev['Weekday'], 
    categories=weekday_order, 
    ordered=True
)

# Sort by that order
weekday_rev = weekday_rev.sort_values('Weekday')

fig = px.bar(
    weekday_rev,
    x='Weekday',
    y='Revenue',
    labels={"Weekday": "Day of Week", "Revenue": "Total Revenue"},
    title="Revenue by Day of Week",
    template="plotly_white"
)

fig.update_layout(
    yaxis=dict(
        tickprefix='$',
        tickformat=',.2f'
    )
)

p2.plotly_chart(fig,use_container_width=True)