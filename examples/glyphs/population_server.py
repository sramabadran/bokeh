from __future__ import print_function

import sys
from math import pi

import requests
from requests.exceptions import ConnectionError

import pandas as pd

from bokeh.objects import (Plot, ColumnDataSource, DataRange1d, FactorRange,
    LinearAxis, CategoricalAxis, Grid, Glyph, SingleIntervalTicker, HoverTool)
from bokeh.widgetobjects import Select, HBox, VBox
from bokeh.glyphs import Line, Quad
from bokeh.session import PlotServerSession
from bokeh.sampledata.population import load_population

df = load_population()
revision = 2012

year = 2010
location = "World"

years = list(map(str, sorted(df.Year.unique())))
locations = sorted(df.Location.unique())

source_pyramid = ColumnDataSource(data=dict())

def pyramid():
    xdr = DataRange1d(sources=[source_pyramid.columns("male"), source_pyramid.columns("female")])
    ydr = DataRange1d(sources=[source_pyramid.columns("groups")])

    plot = Plot(title=None, data_sources=[source_pyramid], x_range=xdr, y_range=ydr, width=600, height=600)

    xaxis = LinearAxis(plot=plot, dimension=0)
    yaxis = LinearAxis(plot=plot, dimension=1, ticker=SingleIntervalTicker(interval=5))

    xgrid = Grid(plot=plot, dimension=0, axis=xaxis)
    ygrid = Grid(plot=plot, dimension=1, axis=yaxis)

    male_quad = Quad(left="male", right=0, bottom="groups", top="shifted", fill_color="blue")
    plot.renderers.append(Glyph(data_source=source_pyramid, xdata_range=xdr, ydata_range=ydr, glyph=male_quad))

    female_quad = Quad(left=0, right="female", bottom="groups", top="shifted", fill_color="violet")
    plot.renderers.append(Glyph(data_source=source_pyramid, xdata_range=xdr, ydata_range=ydr, glyph=female_quad))

    return plot

source_known = ColumnDataSource(data=dict(x=[], y=[]))
source_predicted = ColumnDataSource(data=dict(x=[], y=[]))

def population():
    xdr = FactorRange(factors=years)
    ydr = DataRange1d(sources=[source_known.columns("y"), source_predicted.columns("y")])

    plot = Plot(title=None, data_sources=[source_known, source_predicted], x_range=xdr, y_range=ydr, width=800, height=200)

    xaxis = CategoricalAxis(plot=plot, dimension=0, major_label_orientation=pi/4)
    # yaxis = LinearAxis(plot=plot, dimension=1, ...)

    line_known = Line(x="x", y="y", line_color="violet", line_width=2)
    plot.renderers.append(Glyph(data_source=source_known, xdata_range=xdr, ydata_range=ydr, glyph=line_known))

    line_predicted = Line(x="x", y="y", line_color="violet", line_width=2, line_dash="dashed")
    plot.renderers.append(Glyph(data_source=source_predicted, xdata_range=xdr, ydata_range=ydr, glyph=line_predicted))

    return plot

def update_pyramid():
    pyramid = df[(df.Location == location) & (df.Year == year)]

    male = pyramid[pyramid.Sex == "Male"]
    female = pyramid[pyramid.Sex == "Female"]

    total = male.Value.sum() + female.Value.sum()

    male_percent = -male.Value/total
    female_percent = female.Value/total

    groups = male.AgeGrpStart.tolist()
    shifted = groups[1:] + [groups[-1] + 5]

    source_pyramid.data = dict(
        groups=groups,
        shifted=shifted,
        male=male_percent,
        female=female_percent,
    )

def update_population():
    population = df[df.Location == location].groupby(df.Year).Value.sum()
    aligned_revision = revision//10 * 10

    known = population[population.index <= aligned_revision]
    predicted = population[population.index >= aligned_revision]

    source_known.data = dict(x=known.index.map(str), y=known.values)
    source_predicted.data = dict(x=predicted.index.map(str), y=predicted.values)

def update_data():
    update_population()
    update_pyramid()
    session.store_all()

def on_year_change(obj, attr, old, new):
    global year
    year = int(new)
    update_data()

def on_location_change(obj, attr, old, new):
    global location
    location = new
    update_data()

def layout():
    year_select = Select(title="Year:", value="2010", options=years)
    location_select = Select(title="Location:", value="World", options=locations)

    year_select.on_change('value', on_year_change)
    location_select.on_change('value', on_location_change)

    controls = HBox(children=[year_select, location_select])
    layout = VBox(children=[controls, pyramid(), population()])

    return layout

try:
    session = PlotServerSession(serverloc="http://localhost:5006")
except ConnectionError:
    print("ERROR: This example requires the plot server. Please make sure plot server is running, by executing 'bokeh-server'")
    sys.exit(1)

session.use_doc('population_server')
session.add_plot(layout())

update_data()