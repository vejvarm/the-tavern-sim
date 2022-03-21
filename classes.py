import json
import random

with open("./data/names.json", "r") as f:
    PLAYER_NAMES = json.load(f)


class Brewery:
    price_default = 100  # MEAD
    __ferm_period = 14  # days after buy/claim during which no xp or br is earned
    __days_to_tier_up = [14, 42, 99999]  # cummulative days after FP needed to tier up (T2, T3, T4)
    __tier_mead_prod = [2, 3, 4]  # mead/day (resp. to tier)
    __br_per_day = 20  # BR/day after fermentation period

    def __init__(self, price=price_default):
        self.price = price
        self._mead = 0  # current mead
        self._days_after_claim = 0  # number of days after buy or claim
        self._days_after_fp = 0  # cumulative days after fermentation period
        self._tier = 0  # brewery tier
        self._age = 0  # total age of brewery in days
        self._daily_mead_prod = self.__tier_mead_prod[self._tier]  # mead production
        self._claim = False  # if mead has been claimed

    @property
    def tier(self):
        return self._tier

    def run_day(self):
        """ Runs the brewery for one day

        :return: mead reward for the day, brewer rank reward for the day (if after fermentation period)
        """
        self._days_after_claim += 1
        self._age += 1

        # is it after the fermentation period?
        if self._days_after_claim > self.__ferm_period:
            self._days_after_fp += 1  # add a day to the cummulative days after fermentation period
            br_reward = self.__br_per_day  # add a reward of br
        else:
            br_reward = 0

        # is it due for tier upgrade?
        if self._days_after_fp > self.__days_to_tier_up[self._tier]:
            self._tier += 1  # upgrade tier
            self._daily_mead_prod = self.__tier_mead_prod[self._tier]  # upgrade mead production

        self._mead += self._daily_mead_prod

        return self._daily_mead_prod, br_reward

    def claim(self, claim_tax):
        mead = self._mead
        mead_after_tax = mead*(1 - claim_tax)
        self._mead = 0
        self._days_after_claim = 0

        return mead, mead_after_tax

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value >= 0 and isinstance(value, int):
            self._price = value
        else:
            self._price = self.price_default
            print(f"Default price of {self.price_default} MEAD was set.")


class Player:
    __rank_names = ["novice", "brewer", "brewlord", "brewmaster"]
    __max_rank = len(__rank_names) - 1
    __br_requirements = [0, 50, 500, 2500]  # resp. to rank
    __claim_taxes = [0.18, 0.16, 0.14, 0.12]  # resp. to rank

    def __init__(self, num_breweries=0, price_per_brewery=100, br=0, unclaimed_mead=0., mead_in_wallet=0., name=None):
        self.name = str(name) if name is not None else PLAYER_NAMES.pop(random.randint(0, len(PLAYER_NAMES)-1))
        self.num_breweries = 0
        self.brews_per_tier = [0, 0, 0]
        self.breweries = {}
        self._day = 0
        self._rank = 0
        self._rank_name = self.__rank_names[self.rank]
        self._claim_tax = self.__claim_taxes[self.rank]

        self.unclaimed_mead = unclaimed_mead
        self._claimed_mead = 0.  # untaxed claimed mead (helper variable for claiming and compounding)
        self.mead_in_wallet = mead_in_wallet
        self.br = br  # also updates _rank and _rank_name

        self._history = {"day": [self.day, ],
                         "breweries_per_tier": {"t1": [self.brews_per_tier[0], ],
                                                "t2": [self.brews_per_tier[1], ],
                                                "t3": [self.brews_per_tier[2], ]},
                         "unclaimed_mead": [self.unclaimed_mead, ],
                         "mead_in_wallet": [self.mead_in_wallet, ]}

        # initial buy of breweries
        for _ in range(num_breweries):
            self.buy_brewery(price_per_brewery)

        # invested MEAD during the initial buy
        self.invested_mead = sum(brw.price for brw in self.breweries.values())

    def __str__(self):
        return (f"Player stats:".center(61, "_") + "\n"
                f"Day: {self.day}\n"
                f"Num Breweries: {self.num_breweries}\n"
                f"BR: {self.br} ({self.rank_name})\n"
                f"Claim tax: {int(self.claim_tax*100)} %\n"
                f"Unclaimed mead: {self.unclaimed_mead:.2f}\n"
                f"Mead in wallet: {self.mead_in_wallet:.2f}\n" +
                f"".center(61, "_") + "\n")

    @property
    def day(self):
        return self._day

    @property
    def br(self):
        return self._br

    @br.setter
    def br(self, value):
        self._br = max(0, int(value))
        self._update_rank()

    @property
    def rank(self):
        """ updates with self.br, can't be set"""
        return self._rank

    @property
    def rank_name(self):
        """ updates with self.br, can't be set"""
        return self.__rank_names[self.rank]

    @property
    def claim_tax(self):
        """ updates with self.br, can't be set"""
        return self.__claim_taxes[self.rank]

    @property
    def history(self):
        return self._history

    def _update_rank(self):
        """ Update until br is lower than next requirement or until rank is at __max_rank
            This also leads to updating rank_name and claim_tax

        :return: None
        """
        for next_rank in range(self.rank + 1, self.__max_rank+1):
            if self.br >= self.__br_requirements[next_rank]:
                self._rank = next_rank
            else:
                break  # TODO: Test

    def run_day(self):
        daily_mead = 0
        daily_br = 0
        num_breweries = [0, 0, 0]
        for name, brewery in self.breweries.items():  # for each brewery
            mead, br = brewery.run_day()
            daily_mead += mead
            daily_br += br
            num_breweries[brewery.tier] += 1  # populate new brewery tier distribution
        self.unclaimed_mead += daily_mead
        self.br += daily_br
        self.brews_per_tier = num_breweries
        self._day += 1

        self.history["day"].append(self.day)
        self.history["breweries_per_tier"]["t1"].append(self.brews_per_tier[0])
        self.history["breweries_per_tier"]["t2"].append(self.brews_per_tier[1])
        self.history["breweries_per_tier"]["t3"].append(self.brews_per_tier[2])
        self.history["unclaimed_mead"].append(self.unclaimed_mead)
        self.history["mead_in_wallet"].append(self.mead_in_wallet)

        return self.unclaimed_mead  # TODO: maybe change to daily mead to make more sense?

    def run_breweries_for_n_days(self, n=1):
        for _ in range(n):  # for each day
            self.run_day()

    def claim_from_brewery(self, brewery_id: str):
        """ DONT FORGET TO TAX AFTERWARD!

        :param brewery_id (str): id of the brewery Player wants to claim mead from
        :return: None
        """
        try:
            mead, mead_after_tax = self.breweries[brewery_id].claim(self.claim_tax)
            self.unclaimed_mead -= mead
            self._claimed_mead += mead
            print(f"Sucessfully claimed {mead:.2f} MEAD (before tax) from brewery {brewery_id}.")
            self.history["unclaimed_mead"][-1] = self.unclaimed_mead
        except KeyError:
            print(f"Player doesn't own a brewery with id: {brewery_id}.")

    def tax_claimed_mead_to_wallet(self):
        if self._claimed_mead > 0:
            self.mead_in_wallet += self._claimed_mead - self._claimed_mead*self.claim_tax
            print(f"Taxed {self._claimed_mead} MEAD with tax of {self.claim_tax*100:.0f} %. New Wallet balance: {self.mead_in_wallet} MEAD.")
            self._claimed_mead = 0
            self.history["mead_in_wallet"][-1] = self.mead_in_wallet
        else:
            print("No claimed mead to tax.")

    def claim_all_and_tax_to_wallet(self):
        # step 1: claim mead from all breweries
        for b_id in self.breweries.keys():
            self.claim_from_brewery(b_id)
        print(f"Succesfully claimed MEAD from all breweries.")
        # step 2: tax all claimed mead and add to wallet
        self.tax_claimed_mead_to_wallet()

    def compound(self, price=Brewery.price_default):
        """ Buy as many breweries as possible with claimed_mead, tax the rest and add to wallet
        :param price: price of one Brewery in MEAD

        :return: None
        """
        if self.unclaimed_mead > price:
            # claim from all breweries but don't tax yet!
            for brw_id in self.breweries.keys():
                self.claim_from_brewery(brw_id)

            breweries_to_buy, mead_to_claim = divmod(self._claimed_mead, price)
            for _ in range(int(breweries_to_buy)):
                self.buy_brewery(price)
                self._claimed_mead -= price
            print(f"Bought {breweries_to_buy} Breweries, with new total of {self.num_breweries} Breweries.")
            assert mead_to_claim == self._claimed_mead, "Something is wrong with rest of _claimed_mead calculations"
            # tax and add rest of mead to wallet
            self.tax_claimed_mead_to_wallet()
        else:
            print(f"Not enough unclaimed mead to compound.")

    def buy_brewery(self, price):
        b_id = f"b{self.num_breweries:02d}"
        self.breweries[b_id] = Brewery(price)
        self.num_breweries += 1  # update overall number of breweries
        self.brews_per_tier[0] += 1  # update number of TIER 1 breweries
        self.br += 10
        self.history["breweries_per_tier"]["t1"][-1] = self.brews_per_tier[0]
        print(f"Succesfully bought Brewery {b_id} for {price} MEAD.")