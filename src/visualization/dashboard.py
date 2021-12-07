from logging import debug
import pgeocode
import os
import dash
import numpy as np
from dash import html
from dash import dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output, State

# For making longitude and Latitude from zip code
nomi = pgeocode.Nominatim('us')

app = dash.Dash(__name__)
server = app.server

# Making a list of columns to import
cols = ["year", "mileage", "price", "fueltype", "Drivetrain", "Transmission",
        "State", "City", "Engine size", "Avg mpg", "Vehicle Make", "Zip","Type"]


# Reading the file
def make_df(data_name, colmn):
    filedir = r"C:\Users\PSALISHOL\Documents\My Projects\Car Prediction\data\interim"
    filepath = os.path.join(filedir, data_name+".csv")

    # Reading the file
    data = pd.read_csv(filepath, usecols=colmn)
    # Making new col ---> Longitude and Latitude
    data['Latitude'] = (nomi.query_postal_code(data['Zip'].tolist()).latitude)
    data['Longitude'] = (nomi.query_postal_code(
        data['Zip'].tolist()).longitude)

    return data

# Making base data
data_ = make_df("Audi_cl", cols)


# For concatenating the data
def concat_data(dataname, col_s, base_data):
    new_df = make_df(dataname, col_s)
    concat_df = pd.concat([base_data, new_df], axis=0)

    return concat_df


# Making list of dataname to be concatinated
data_list = ["BMW_cl", "Buick_cl", "cardillac_cl", "Chevrolet_cl", "Chrysler_cl",
             "Dodge_cl", "Ford_cl", "GMC_cl", "hyundai_cl","honda_cl", "jaguar_cl", "toyota_cl","volvo_cl"]

# Concatinating the datas.
for data in data_list:
    data_ = concat_data(data, cols, data_)

# Creating access token for mapbox
mapbox_access_token = "sk.eyJ1IjoicHNhbGlzaG9sIiwiYSI6ImNrdTZydGhjMjFxbXEycXFrdmd0OWxnMmYifQ.KKXofcYq04f1MiPOIcitQQ"
# Layout for the Map
layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(
        l=30,
        r=30,
        b=20,
        t=40
    ),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation='h'),
    title='Satellite Overview',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="dark",
        center=dict(
            lon=-78.05,
            lat=42.54
        ),
        zoom=7,
    )
)


app.layout = html.Div(
    [
        dcc.Store(id='aggregate_data'),
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Value Insight", id="header-text"),
        
                    ],
                )
            ],
            className= "header"
        ),
        html.Div(
            [
                html.Div(
                    [
                        # Dropdown for selecting Vehicle make
                        html.Label("Vehicle Make"),
                        dcc.Dropdown(
                            id="dropdown_make",
                            options = [{"label":i,"value":i} for i in 
                                            sorted([feature for feature in list(data_["Vehicle Make"].unique()) if len(data_[data_["Vehicle Make"] == feature]) > 300],reverse=False)],
                            value= "Audi",
                            className="dcc_control"
                        ),
                        
                        # Dropdown for selecting Feature to compare price with
                        html.Label("Choose Feature to Compare"),
                        dcc.Dropdown(
                            id="dropdown_comp",
                            options=[{"label": i,"value": i} for i in data_.columns 
                                            if data_[i].dtype == object and i not in ["State","City","Model","Vehicle Make","Zip"]],
                            value="Transmission",
                            className="dcc_control"
                        ),
                    ]
                )
            ]
        ),
        html.Div(
            [
                # For Model slot
                html.Div(
                    [
                        html.P("Make", id="make_text"),
                        html.H6(
                            id="model_text",
                            className= "info_text"
                        )
                    ],
                    id="model",
                    className="container_card"
                ),
        
                # For displaying the Avg price
                html.Div(
                    [
                        html.P("Avg Price", id="card-detail"),
                        html.H6(
                            id="avg_price_text",
                            className= "info_text"
                        )
                    ],
                    id="avg_price",
                    className= "container_card"
                )
        
            ]
        ),
    
        # For plotting the Bargraph
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id="lineplot_graph")
                    ],
                    className="container first col"
                )
            ],
            className="row"
        ),
    
        # For ploting barplot grapgh
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id="barplot_graph")
                    ],
                    className="container first col"
                ),
                
                html.Div(
                    [
                        dcc.Graph(id="pie-plot-graph")
                    ],
                    className="container second col"
                )
            ],
            className="row"
        ),
    
        # For Displaying Geographical Location
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id="satelite_view")
                    ]
                )
            ]
        ),
    
    
        # For Plotting all make with price
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id="make_price")
                    ],
                    className ="container last row"
                )
            ],
            className= "row2"
        )
    ]
)


# Helper functions
@app.callback(Output("model_text","children"),
              [Input("dropdown_make","value")])
def update_avg_price(value):
    if value is None:
        return "None"
    else:
        return value

# UPDATING AVERAGE PRICE TEXT----->
@app.callback(Output("avg_price_text","children"),
              [Input("dropdown_make","value")])
def update_price_text(value):
    if value is None:
        return "0"
    else:
        name = data_.groupby("Vehicle Make")["price"].mean().to_frame()
        val = str(int(name[data_.groupby("Vehicle Make")["price"].mean().index == value].values))
        # formating the Price
        if len(val) == 5:
            return val[0:2]+","+val[2:]
        elif len(val) == 6:
            return val[0:3]+","+val[3:]
        elif len(val) == 7:
            return val[0]+","+val[1:4]+","+val[4:]
# updating Barplot-----------------------------------------------------------------------------------------------------------------------------
@app.callback(Output("lineplot_graph","figure"),
              [Input("dropdown_make","value"),
               Input("dropdown_comp","value")]
              )
def update_barplot(selected_make,selected_comp):
    data_filtered = data_[data_["Vehicle Make"] == selected_make]
    # If nothing is selected
    if selected_comp == None:
        fig =px.bar(
        x=data_.groupby("Transmission")["price"].mean().index, y=data_.groupby("Transmission")["price"].mean().values)
        return fig
    else:
        fig =px.bar(
            x=data_filtered.groupby(selected_comp)["price"].mean().index, y=data_filtered.groupby(selected_comp)["price"].mean().values)
        return fig


@app.callback(Output(component_id="barplot_graph",component_property="figure"),
              [Input(component_id="dropdown_make",component_property="value"),
               Input(component_id="dropdown_comp",component_property="value")]
              )
def update_lineplot(selected_make,selected_val):
    selected = []
    year = []
    price = []
    # Making a filtered dataframe
    data_filtered = data_[data_["Vehicle Make"] == selected_make]    
    grouped_d = data_filtered.groupby(["year",selected_val])["price"].mean().to_dict()
    for key_p,val_p in zip(grouped_d.keys(),grouped_d.values()):
        year.append(key_p[0])
        selected.append(key_p[1])
        price.append(val_p)
    
    # Plotting the graph
    fig =px.bar(
            x=year,y=price, color=selected, title=f"{selected_make}")
    return fig

@app.callback(Output(
    component_id="make_price",component_property="figure"),
              Input(
                  component_id="dropdown_comp",component_property="value"
              ))
def update_model(selected_co):
    V_price = []
    v_make = []
    color = []
    # Making a copy of the dataset
    new_d = data_.copy()
    mk_grouped = new_d.groupby("Vehicle Make",selected_co)["price"].mean()
    dict_val = mk_grouped.to_dict()
    for make,price in zip(dict_val.keys(),dict_val.values()):
        v_make.append(make[0])
        color.append(make[1])
        V_price.append(price)
    #Plotting the bar plot for showing the make and price 
    fig = px.bar(x=v_make, y=V_price,color=color, title='Vehicle Make with the price')
    return fig


# Making the plot showing all makes and preferred feature
@app.callback(Output(component_id="make_price",component_property="figure"),
              Input(component_id="dropdown_comp",component_property="value")) 
def update_pie_plot(selected_make):
    # Making the filtered data
    data_filtered = data_.groupby("Vehicle Make",selected_make)["price"].mean()
    selected = []   # Collects the selected feature for each price and make
    make = []      # Collects the make for each selected feature and price
    price = []    # Collects the mean price for each make and selected features
    data_dict = data_filtered.to_dict()
    for keys,values in zip(data_dict.keys(),data_dict.values()):
        make.append(keys[0])
        selected.append(keys[1])
        price.append(values)

    
    fig = px.bar(x=make, y=price, color=selected)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)



