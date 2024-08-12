import streamlit as st
import folium
import geopandas as gpd
import pandas as pd
import shapely
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(layout="wide")

mappable_df_path = "Datasets/WVCS_Mappable_CSV.csv"
global mappable_df 
mappable_df = pd.read_csv(mappable_df_path) #Creates dataframe from CSV file of neighborhood geometry and statistics
mappable_df["the_geom"] = mappable_df["the_geom"].apply(shapely.wkt.loads)

global mappable_gdf
mappable_gdf = gpd.GeoDataFrame(mappable_df, geometry = "the_geom", crs = "epsg:4326") #Turns dataframe into a GeoDataFrame for mapping

columns_with_description = {
    "% Of Single Parent Households": "single_parent_households", 
    "Per Capita Income": "per_capital_income", 
    "Median Household Income": "median_household_income", 
    "% Of Children Living In Assisted Households": "children_living_in_households", 
    "% Of Households Without Full Time Employment": "households_without_full_time", 
    "% Of Children Aged 0-17": "children_ages_0_17_below",
    "% Of Families Below 200% Of Federal Poverty Line": "families_below_200_fpl", 
    "% Of Households Recieving CalFresh Benifits": "households_receiving_calfresh", 
    "% Of Households Where Gross Rent >30% Of Income": "households_with_gross_rent"
} #Dictionary to map column descriptions to column names

ordering = dict() #Creates a dictionary that defines how each metric should be sorted (bottom up vs top down)
for key in columns_with_description.keys():
    if key[0] == "%":
        ordering[key] = "bottom"
    else:
        ordering[key] = "top"

column_values = list(columns_with_description.values())

to_multiply = column_values.copy()

to_multiply.remove("per_capital_income")
to_multiply.remove("median_household_income")

mappable_gdf[to_multiply] = mappable_gdf[to_multiply].mul(100).round(2) #Multiplies all percentage values by 100 (0.1 -> 10)
mappable_df[to_multiply] = mappable_df[to_multiply].mul(100).round(2)

#Creates sidepanel to select different metrics
def create_sidepanel():
    global mappable_df
    global mappable_gdf
    options = list(columns_with_description.keys())
    selectbox = st.sidebar.selectbox(
        "Choose A Statistic To Display", 
        options = options,
        index = 0
    )
    neighborhood_options = mappable_gdf["Neighborhood Name"].unique()
    default_neighborhoods = [
        "Cupertino - Eastside",
        "Cupertino - Northside",
        "Cupertino - Southside",
        "Cupertino - Westside",
        "Los Gatos - Eastern",
        "Saratoga - Northwestern",
        "Saratoga - Southeastern",
        "San Tomas - North",
        "San Tomas - South",
        "Monte Sereno/Los Gatos - Western",
        "Cambrian Park West",
        "Cambrian Park West Central",
        "Calabazas",
        "Santa Clara - Southwest",
        "Santa Clara - West Central",
        "West San Jose",
        "Winchester West",
        "Winchester East"
    ]
    st.write(np.sort(neighborhood_options))
    multiselect = st.sidebar.multiselect(
        "Choose the neighborhoods to display",
        options = neighborhood_options,
        default = default_neighborhoods
    )
    mappable_gdf = mappable_gdf[mappable_gdf["Neighborhood Name"].isin(multiselect)]
    mappable_df = mappable_df[mappable_df["Neighborhood Name"].isin(multiselect)]
    return selectbox, multiselect
    

#Displays the top/bottom three neighborhoods for the selected metric
def select_top_3 (column_description, mappable_df):
    column = columns_with_description[column_description]
    if ordering[column_description] == "bottom":
        top_3 = np.sort(mappable_df[column])[::-1][:3]
        st.header("Neighborhoods Where " + "\"" + column_description + "\"" + " Is The Greatest")
    else:
        top_3 = np.sort(mappable_df[column])[:3]
        st.header("Neighborhoods Where " + "\"" + column_description + "\"" + " Is The Least")
    top_3_df = mappable_df[mappable_df[column].isin(top_3)] 
    neighborhoods = np.array(top_3_df["Neighborhood Name"])
    neighborhood1, neighborhood2, neighborhood3 = st.columns(3) #Creates three columns to display each of the top/bottom 3 cities
    #Displays the top/bottom three neighborhoods for each metric
    neighborhood1.metric(neighborhoods[0], top_3_df.loc[top_3_df["Neighborhood Name"] == neighborhoods[0], column])
    neighborhood2.metric(neighborhoods[1], top_3_df.loc[top_3_df["Neighborhood Name"] == neighborhoods[1], column])
    neighborhood3.metric(neighborhoods[2], top_3_df.loc[top_3_df["Neighborhood Name"] == neighborhoods[2], column])

    return neighborhoods, top_3_df

#Creates the map that should be displayed on the screen
def create_map (column_description, mappable_gdf):
    map = folium.Map(location = [37.2200, -121.6000], zoom_start = 10)
    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)
    #Defines the Choropleth map
    choropleth = folium.Choropleth(
        geo_data = mappable_gdf,
        data = mappable_gdf,
        columns = ["Neighborhood Name", columns_with_description[column_description]],
        fill_color = "YlGnBu",
        key_on = "feature.properties.Neighborhood Name",
        highlight = True,
        legend_name = column_description
    )

    choropleth.geojson.add_to(map)

    #When a particular neighborhood is hovered over, it displays the desired metric for that neighborhood
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields = ["Neighborhood Name", columns_with_description[column_description]],
            aliases = ["Neighborhood Name: ", column_description + ": "],
            localize = True
        )
    )

    st_map = st_folium(map, use_container_width=True, height = 600)


selection, multiselect = create_sidepanel()
select_top_3(selection, mappable_df = mappable_df)
create_map(selection, mappable_gdf = mappable_gdf)
