from functools import partial

from bokeh.models import Button, ColumnDataSource, Select, Span, Spinner
from bokeh.layouts import row, column, layout
from bokeh.models.widgets import Paragraph, Div
from bokeh.plotting import curdoc

from classes import Player
from helpers import brewery_plot_constructor, plot_constructor, initialization_models, update_output_values


PLAYER = Player()
PLOT = plot_constructor()
BREWERY_PLOT = brewery_plot_constructor()


# TODO: mead in wallet and initial br is not really important for initialization
def initialize():
    global PLAYER, PLOT, BREWERY_PLOT

    # get values from spinners
    num_breweries = int(sp_num_breweries.value)
    average_brewery_price = int(sp_total_price.value//num_breweries)
    br = int(sp_init_br.value)
    mead_in_wallet = float(sp_init_mead.value)

    # initialize and update globals
    PLAYER = Player(num_breweries, average_brewery_price, br, mead_in_wallet=mead_in_wallet)
    PLOT = plot_constructor()
    BREWERY_PLOT = brewery_plot_constructor()

    # show horizontal line for ROI (we have the sp_total_price for that)
    # TODO: make work!
    roi_line = Span(location=sp_total_price.value,
                    dimension='width', line_color='#F0E442',
                    line_dash='dashed', line_width=3)
    PLOT.add_layout(roi_line)

    # (Re)-initialize data_source
    new_data = {"day": [0],
                "breweries_per_tier": [PLAYER.num_breweries_per_tier],
                "unclaimed_mead": [0],
                "mead_in_wallet": [PLAYER.mead_in_wallet]}
    data_source.data = new_data

    # update outputs
    update_output_values(PLAYER,
                         name=p_company_name_val,
                         day=p_day_val,
                         breweries=p_breweries_val,
                         br=p_br_val,
                         claim_tax=p_claim_tax_val,
                         unclaimed_mead=p_unclaimed_mead_val,
                         wallet_mead=p_wallet_mead_val)


def callback_run():

    starting_day = max(1, PLAYER.day)
    days_to_run = int(sp_run_days.value)  # num days to run
    brewery_price = int(sp_compound_brewery_price.value)  # MEAD/brewery

    # get strategy
    strategy = str(sel_strats.value)

    # run simulation for "days_to_run" with selected "strategy"
    if strategy == "hodl":
        PLAYER.run_breweries_for_n_days(days_to_run)
    elif strategy == "compound when possible":
        for d in range(days_to_run):
            PLAYER.run_day()
            if PLAYER.unclaimed_mead >= brewery_price:  # COMPOUND ASAP
                PLAYER.compound(brewery_price)
    elif strategy == "claim daily":
        for d in range(days_to_run):
            PLAYER.run_day()
            PLAYER.claim_all_and_tax_to_wallet()
    else:
        raise ValueError("You selected something that shouldn't exists. Now give back the reaility stone.")

    # Update data sources
    new_data = dict()
    new_data["day"] = PLAYER.history["day"][starting_day:]
    new_data["breweries_per_tier"] = PLAYER.history["breweries_per_tier"][starting_day:]
    new_data["unclaimed_mead"] = PLAYER.history["unclaimed_mead"][starting_day:]
    new_data["mead_in_wallet"] = PLAYER.history["mead_in_wallet"][starting_day:]
    data_source.stream(new_data)  # stream new data to data_source

    new_brew_data = dict()
    new_brew_data["days"] = [new_data["day"] for _ in range(3)]
    new_brew_data["brew_tiers"] = list(zip(*new_data["breweries_per_tier"]))
    ds_breweries.stream(new_brew_data)  # stream new data to ds_breweries

    # update outputs
    update_output_values(PLAYER,
                         name=p_company_name_val,
                         day=p_day_val,
                         breweries=p_breweries_val,
                         br=p_br_val,
                         claim_tax=p_claim_tax_val,
                         unclaimed_mead=p_unclaimed_mead_val,
                         wallet_mead=p_wallet_mead_val)


# INITIALIZATION
sp_num_breweries, sp_total_price, sp_init_br, sp_init_mead = initialization_models()
# TODO: (remove) init_input_row = row(column(sp_num_breweries, sp_total_price), column(sp_init_br, sp_init_mead))
# button for initialization/reset
btn_initialize = Button(label="Initialize/Reset")
btn_initialize.on_click(initialize)


# VISUALIZATION
# create data sources to feed data into
data_source = ColumnDataSource(data={"day": [0], "unclaimed_mead": [0], "mead_in_wallet": [0]})
ds_breweries = ColumnDataSource(data={"days": [[0], [0], [0]], "brew_tiers": [[0], [0], [0]]})
# ds_mead_wallet = ln_mead_wallet.data_source

# add line renderers connected to the data sources
ln_mead_unclmd = PLOT.line(x="day", y="unclaimed_mead", line_color="red", line_width=2, legend_label="unclaimed", source=data_source)
ln_mead_wallet = PLOT.line(x="day", y="mead_in_wallet", line_color="blue", line_width=2, legend_label="wallet", source=data_source)
PLOT.legend.location = "top_left"

xs = [data_source.data["day"] for _ in range(3)]
ys = list(zip(*PLAYER.history["breweries_per_tier"]))
ln_breweries = BREWERY_PLOT.multi_line(xs="days", ys="brew_tiers", line_width=2, source=ds_breweries)
# TODO: multi_line different colors and legend

# SIMULATION
# SPINNERS for (x) days, brewery buy price and choice box for strategies
sp_run_days = Spinner(title="Days to run:", low=1, high=1000, value=1)
sp_compound_brewery_price = Spinner(title="Brewery price (MEAD):", low=1, high=1000, value=100)
# STRATEGIES (HODL, COMPOUND whenever possible, Claim daily, TODO: Wait for T2 and then COMPOUND)
sel_strats = Select(title="Strategy:", value="hodl", options=["hodl", "compound when possible", "claim daily"])

# BUTTON FOR RUNNING SIMULATION FOR (x) DAYS
btn_run_sim = Button(label="Advance time")
btn_run_sim.on_click(callback_run)

# TODO: BUTTONS FOR MANUAL CLAIM AND COMPOUND without advancing time


# OUTPUTS:
p_company_name_text, p_company_name_val = Paragraph(text="Company name: "), Paragraph(text="")
p_day_text, p_day_val = Paragraph(text="Day: "), Paragraph(text="0")
p_breweries_text, p_breweries_val = Paragraph(text="Breweries (T1, T2, T3): "), Paragraph(text="(0, 0, 0)")
p_br_text, p_br_val = Paragraph(text="Brewer rank: "), Paragraph(text="0 (novice)")
p_claim_tax_text, p_claim_tax_val = Paragraph(text="Claim tax: "), Paragraph(text="18 %")
p_unclaimed_mead_text, p_unclaimed_mead_val = Paragraph(text="Unclaimed mead: "), Paragraph(text="0")
p_wallet_mead_text, p_wallet_mead_val = Paragraph(text="Mead in wallet: "), Paragraph(text="0")

outputs_text = column(p_company_name_text, p_day_text, p_breweries_text, p_br_text, p_claim_tax_text, p_unclaimed_mead_text, p_wallet_mead_text)
outputs_vals = column(p_company_name_val, p_day_val, p_breweries_val, p_br_val, p_claim_tax_val, p_unclaimed_mead_val, p_wallet_mead_val)

# MARKUP
h3_stats = Div(text="""<h3>Stats</h3>""", align="center")
h3_init = Div(text="""<h3>Initialization</h3>""", align="center")
h3_run = Div(text="""<h3>Run simulation</h3>""", align="center")

# init_input_row = row(column(sp_num_breweries, sp_total_price), column(sp_init_br, sp_init_mead))
# in_out_layout = layout(children=[h3_stats,
#                                  row(outputs_text, outputs_vals),
#                                  h3_init,
#                                  row(sp_num_breweries, sp_total_price),
#                                  row(sp_init_br, sp_init_mead),
#                                  btn_initialize,
#                                  h3_run,
#                                  row(sp_run_days, sp_compound_brewery_price),
#                                  sel_strats,
#                                  btn_run_sim],
#                        sizing_mode="scale_width", max_width=300)

# Alternative simplified functionality
in_out_layout = layout(children=[h3_stats,
                                 row(outputs_text, outputs_vals),
                                 h3_init,
                                 sp_num_breweries,
                                 btn_initialize,
                                 h3_run,
                                 sp_run_days,
                                 sp_compound_brewery_price,
                                 sel_strats,
                                 btn_run_sim],
                       sizing_mode="scale_width", max_width=300)

full_layout = row(in_out_layout, column(PLOT, BREWERY_PLOT), sizing_mode="scale_height")

doc = curdoc()
# put the button and plot in a layout and add to the document
doc.add_root(full_layout)
