import streamlit as st
import datetime as dt
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from streamlit_utils import group_messages, group_reactions, group_events, select_core_team, select_score, clean_dataframe
from dotenv import load_dotenv
from pytz import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from db_utils import get_data

load_dotenv()

st.title("TPL dashboard")
st.divider()

member_list = clean_dataframe(get_data('member_list'), 'member_list')
member_list['join_date'] = pd.to_datetime(member_list['join_date'])
msgs = clean_dataframe(get_data('chat_messages'), 'chat_messages')
rxns = clean_dataframe(get_data('chat_reactions'), 'chat_reactions')
events = clean_dataframe(get_data('tpl_events'), 'tpl_events')

period = st.sidebar.radio(
    "Select a period for metrics calculation", 
    [
        "Past Week",
        "Past Month",
        "Past Quarter",
        "Past 6 months",
        "Custom period"
    ], 
    index=2,
    label_visibility="visible"
    )

core_team = select_core_team()
if not core_team:
    msgs = msgs[~msgs['from_id'].isin(member_list[member_list['is_mgmt']]['user_id'])]
    rxns = rxns[~rxns['user_id'].isin(member_list[member_list['is_mgmt']]['user_id'])]
    events = events[~events['user_id'].isin(member_list[member_list['is_mgmt']]['user_id'])]
    member_list = member_list[~member_list['is_mgmt']]

today = dt.datetime.today().date()
if period == "Custom period":
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        curr_pd_start = st.date_input(
            label="Start date",
            value= today - timedelta(days=30)
            )

    with col2:
        curr_pd_end = st.date_input(
            label="End date",
            value= today
            )
    prev_pd_start = curr_pd_start - relativedelta(today, curr_pd_start)
else:
    period_dict = {
        "Past Week": {'weeks': 1},
        "Past Month": {'months': 1},
        "Past Quarter": {'months': 3},
        "Past 6 months": {'months': 6}
    }
    curr_pd_end = today
    curr_pd_start = curr_pd_end - relativedelta(**period_dict[period])
    prev_pd_start = curr_pd_start - relativedelta(**period_dict[period])
#filter dates
curr_msgs = msgs[(msgs['datetime'].dt.date > curr_pd_start) & (msgs['datetime'].dt.date < curr_pd_end)]
curr_rxns = rxns[(rxns['datetime'].dt.date > curr_pd_start) & (rxns['datetime'].dt.date < curr_pd_end)]
curr_events = events[(events['datetime'].dt.date > curr_pd_start) & (events['datetime'].dt.date < curr_pd_end)]

prev_msgs = msgs[(msgs['datetime'].dt.date > prev_pd_start) & (msgs['datetime'].dt.date < curr_pd_start)]
prev_rxns = rxns[(rxns['datetime'].dt.date > prev_pd_start) & (rxns['datetime'].dt.date < curr_pd_start)]
prev_events = events[(events['datetime'].dt.date > prev_pd_start) & (events['datetime'].dt.date < curr_pd_start)]

#run groupbys and merges
curr_msgs_count = group_messages(curr_msgs)
curr_rxns_count = group_reactions(curr_rxns)
curr_events_count = group_events(curr_events)

prev_msgs_count = group_messages(prev_msgs)
prev_rxns_count = group_reactions(prev_rxns)
prev_events_count = group_events(prev_events)

curr_merge_temp = pd.merge(
    curr_msgs_count, 
    curr_rxns_count,
    left_on='username',
    right_on='username',
    how='outer'
    )
curr_period = pd.merge(
    curr_events_count, 
    curr_merge_temp,
    left_on='username',
    right_on='username',
    how='outer'
    ).fillna(0)

prev_merge_temp = pd.merge(
    prev_msgs_count, 
    prev_rxns_count,
    left_on='username',
    right_on='username',
    how='outer'
    )
prev_period = pd.merge(
    prev_events_count, 
    prev_merge_temp,
    left_on='username',
    right_on='username',
    how='outer'
    ).fillna(0)

# compute scores
scoring_system = select_score()
curr_score = sum(curr_period[column] * weight for column, weight in scoring_system.items())
curr_period.insert(1, "total_score", curr_score)
curr_period = curr_period.sort_values(by=["total_score", "event_count"], ascending = False).reset_index(drop=True)
prev_score = sum(prev_period[column] * weight for column, weight in scoring_system.items())
prev_period.insert(1, "total_score", prev_score)
prev_period = prev_period.sort_values(by=["total_score", "event_count"], ascending = False).reset_index(drop=True)


# Display metrics
events_metric, messages_metric, reactions_metric = st.columns(3)
with events_metric:
    with st.container(border=True):
        curr_pd_event_attendees = curr_events.groupby('event_name')['username'].nunique().sum()
        prev_pd_event_attendees = prev_events.groupby('event_name')['username'].nunique().sum()
        st.metric(
            label='Total event attendees',
            value=curr_pd_event_attendees,
            delta=f"{int(curr_pd_event_attendees - prev_pd_event_attendees)} from prev. preiod"
            )
with messages_metric:
    with st.container(border=True):
        curr_pd_messages = curr_period['message_count'].sum()
        prev_pd_messages = prev_period['message_count'].sum()
        st.metric(
            label='Chat Messages',
            value=int(curr_pd_messages),
            delta=f"{int(curr_pd_messages - prev_pd_messages)} from prev. preiod"
            )
with reactions_metric:
    curr_pd_reactions = curr_period['reaction_count'].sum()
    prev_pd_reactions = prev_period['reaction_count'].sum()
    with st.container(border=True):
        st.metric(
            label='Chat Reactions',
            value=int(curr_pd_reactions),
            delta=f"{int(curr_pd_reactions - prev_pd_reactions)} from prev. preiod"
            )
st.caption(f"Period duration: {(today - curr_pd_start).days} days")

st.subheader("Top fans")
if st.checkbox("compare against past period"):
    curr, prev = st.columns(2)
    with curr:
        st.write("Current period:")
        st.write(curr_period)
    with prev:
        st.write("Previous period:")
        st.write(prev_period)
else:
    st.dataframe(curr_period)

st.divider()

st.subheader("New members")
st.caption("Refers to members who joined in the current selected period.")
if st.checkbox("Define your own cut-off date for new members:", value=False):
    col1, col2 = st.columns([1,5])
    with col1:
        new_member_cutoff_date = st.date_input(
            label="Cut-off date:",
            value=dt.date(2024, 1, 1))

else:
    new_member_cutoff_date = curr_pd_start

new_members = member_list[member_list['join_date'].dt.date > new_member_cutoff_date].reset_index(drop=True)

st.markdown("##### Offline engagement")
curr_events = events[(events['datetime'].dt.date > new_member_cutoff_date) & (events['datetime'].dt.date < curr_pd_end)]
curr_events = curr_events.pivot_table(
    index="username",
    columns="event_name",
    values="participation"
).reset_index().fillna(0)
curr_events = curr_events[curr_events['username'].isin(new_members['username'])]
new_member_events = pd.merge(
    new_members, 
    curr_events, 
    on='username', 
    how='left'
    ).fillna(0)[curr_events.columns]
st.write(new_member_events)

st.markdown("##### Online engagement")

fig = px.scatter(
    curr_period[curr_period['username'].isin(new_members['username'])], 
    x='message_count', 
    y='reaction_count', 
    title='Message vs Reaction Count',
    hover_name='username'
    )

mean_message_count = curr_period['message_count'].mean()
mean_reaction_count = curr_period['reaction_count'].mean()

# Add a point for the mean values
fig.add_trace(go.Scatter(x=[mean_message_count], y=[mean_reaction_count],
                         mode='markers+text', 
                         text=['Mean'], 
                         textposition='top center',
                         hoverinfo='text',
                         hovertext='Avg. no. of messages and reactions by active users in selected period', 
                         marker=dict(color='Red', size=10),
                         showlegend=False))

fig.update_xaxes(range=[0, fig.data[0].x.max() + 5])  # Adjust the maximum as needed
fig.update_yaxes(range=[0, fig.data[0].y.max() + 5])  # Adjust the maximum as needed

st.plotly_chart(fig)
with st.expander("Show data"):
    st.write(curr_period[curr_period['username'].isin(new_members['username'])].reset_index(drop=True))