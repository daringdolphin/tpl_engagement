import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# lightweight function to validate the database connection
def validate_connection(client):
    try:
        client.table("member_list").select("user_id").limit(1).execute()
        return True
    except:
        return False

#initialize and cache a supabase client. runs the validation function to check for healthy database connection
@st.cache_resource(ttl="30 days", validate=validate_connection)
def init_supabase_connection():
    """Initializes and returns a Supabase client."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return client

supabase_client = init_supabase_connection()

# Uses st.cache_data to only rerun when the query changes or after a day.
@st.cache_data(ttl="1 day")
def get_data(table_name: str) -> pd.DataFrame:
    response = (supabase_client
                .table(table_name)
                .select('*')
                .execute()
                )
    data = response.data
    if data is None:
        raise ValueError("Error fetching data from Supabase")
    return pd.DataFrame(data)