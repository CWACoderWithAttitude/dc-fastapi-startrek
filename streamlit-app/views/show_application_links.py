import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"


def show_application_links():
    st.title("🚀 Show Application Links")

    st.markdown("## App Links")
    st.markdown("- [FastAPI > Ships REST Endpoint](http://localhost:9600/ship/)")
    st.markdown("- [FastAPI > Ships SwaggerUI / OpenAPI](http://localhost:9600/docs#)")
    st.markdown("- [FastAPI > Ships ReDoc](http://localhost:9600/redoc)")
    st.markdown("## Admin Links")
    st.markdown("- [Generate API Clients from this URL](http://localhost:9600/openapi.json)")
    st.markdown("- [Streamlit Ships UI](http://localhost:8501) - this UI ;-)")
    st.markdown("- [DB Adminer](http://localhost:9610/?pgsql=db&username=star&db=star-trek-ships-db&ns=public&select=ship)")
    st.markdown("- [Prometheus Targets](http://localhost:9690/targets)")
    st.markdown("- [Grafana /admin/admin)](http://localhost:9630)")
    st.markdown("- [Grafana Datasource](http://localhost:9630/connections/datasources/edit/defqw6dierj7ke) (admin/admin)")
