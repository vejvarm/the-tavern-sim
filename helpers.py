from bokeh.plotting import figure
from bokeh.models import Spinner


def plot_constructor():
    p = figure(title="Mead trend", x_axis_label="day", y_axis_label="mead", min_width=800,
               width_policy="max", height_policy="fit")  # TODO: aspect_ratio
    return p


def brewery_plot_constructor():
    p = figure(title="Breweries", x_axis_label="day", y_axis_label="breweries", min_width=800,
               width_policy="max", height_policy="fit")
    return p


def initialization_models():
    # initial number of breweries (TODO: expand to number of T1, T2, T3)?
    sp_num_breweries = Spinner(
        title="Breweries (T1)",
        low=0,
        high=60,
        step=1,
        value=1,
    )
    # average price per brewery
    sp_total_price = Spinner(
        title="Total price (MEAD)",
        low=50,
        high=99999,
        step=100,
        value=100,
    )
    # initial BR
    sp_init_br = Spinner(
        title="Initial BR",
        low=0,
        high=9999,
        step=10,
        value=0,
    )
    # initial mead in wallet
    sp_init_mead = Spinner(
        title="Mead in wallet",
        low=0,
        high=9999,
        step=100,
        value=0,
    )

    return sp_num_breweries, sp_total_price, sp_init_br, sp_init_mead


def update_output_values(player, **kwargs):
    if "name" in kwargs.keys():
        kwargs["name"].text = str(player.name)
    if "day" in kwargs.keys():
        kwargs["day"].text = str(player.day)
    if "breweries" in kwargs.keys():
        kwargs["breweries"].text = str(tuple(player.brews_per_tier))
    if "br" in kwargs.keys():
        kwargs["br"].text = f"{player.br} ({player.rank_name})"
    if "claim_tax" in kwargs.keys():
        kwargs["claim_tax"].text = f"{player.claim_tax*100:.0f} %"
    if "unclaimed_mead" in kwargs.keys():
        kwargs["unclaimed_mead"].text = str(player.unclaimed_mead)
    if "wallet_mead" in kwargs.keys():
        kwargs["wallet_mead"].text = str(player.mead_in_wallet)


def append_l2(num_brws_list: list, num_brw_now: list):
    n_tiers = len(num_brws_list)
    assert n_tiers == len(num_brw_now)
    for i in range(n_tiers):
        num_brws_list[i].extend(num_brw_now[i])
