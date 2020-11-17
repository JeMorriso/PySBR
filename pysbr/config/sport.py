import pysbr.utils as utils
from pysbr.config.config import Config


class Sport(Config):
    def __init__(self, sport_config, league_config):
        super().__init__()

        self._search_translations = utils.load_yaml(
            utils.build_yaml_path("search_dictionary")
        )

        self._sport = self._translate_dict(
            utils.load_yaml(utils.build_yaml_path(sport_config))
        )
        self._league = self._translate_dict(
            utils.load_yaml(utils.build_yaml_path(league_config))
        )

        self._market_ids = self._build_market_ids(self._sport["markets"])

        self.market_names = self._build_market_names(self._sport["markets"])

        self.sport_id = self._sport["sport id"]
        self.default_market_id = self._sport["default market id"]
        self.league_id = self._league["league id"]
        self.league_name = self._league["name"]
        self.abbr = self._league["alias"]

    def _build_market_ids(self, m):
        markets = {}
        for x in m:
            url_key = x["url"].lower()
            name_key = x["name"].lower()
            markets[url_key] = {}
            markets[name_key] = {}
            for y in x["market types"]:
                id = [v for k, v in y.items() if k == "market id"][0]
                for k in ["alias", "name", "url"]:
                    v = [v.lower() for list_key, v in y.items() if list_key == k][0]
                    markets[url_key][v] = id
                    markets[name_key][v] = id
        return markets

    def _build_market_names(self, m):
        markets = {}
        for x in m:
            for y in x["market types"]:
                markets[y["market id"]] = y["name"]
        return markets

    def sport_config(self):
        return self._sport

    def league_config(self):
        return self._league

    def search_translations(self):
        return self._search_translations

    def market_ids(self, terms):
        search_dict = self._search_translations
        ids = []
        for t in terms:
            if isinstance(t, int):
                ids.append(t)
            else:
                old_t = t
                if isinstance(t, str):
                    t = ["full game", t]
                t = list(t)
                try:
                    t = [x.lower() for x in t]
                except AttributeError:
                    raise AttributeError("Search components must be ints or strings.")
                try:
                    t[0] = search_dict[t[0]]
                except KeyError:
                    pass
                try:
                    t[1] = search_dict[t[1]]
                except KeyError:
                    pass

                try:
                    ids.append(self._market_ids[t[0]][t[1]])
                except KeyError:
                    raise ValueError(f"Could not find market {old_t}")
        # TODO: need to handle case where they resolve to same ID, because I don't
        # think it will work for the query?
        return ids


class TeamSport(Sport):
    def __init__(self, sport_config, league_config):
        super().__init__(sport_config, league_config)

        self._team_ids = self._build_team_ids(self._league["teams"])

    def _build_team_ids(self, t):
        teams = {}
        for k in [
            "abbreviation",
            "sbr abbreviation",
            "name",
            "nickname",
            "location",
            "full name",
        ]:
            teams[k] = {}
            if not k == "full name":
                for x in t:
                    teams[k][x[k].lower()] = x["team id"]
            else:
                for x in t:
                    full_name = " ".join([x["location"].lower(), x["nickname"].lower()])
                    teams[k][full_name] = x["team id"]

        return teams

    def team_ids(self, terms):
        ids = []
        for t in terms:
            if isinstance(t, int):
                ids.append(t)
            else:
                old_t = t
                t = t.lower()
                found = False
                # Pylance error 'id is possibly unbound' if I don't set id to None here
                id = None
                for k, v in self._team_ids.items():
                    if t in v:
                        if not found:
                            found = True
                            id = v[t]
                        else:
                            # TODO - could I raise a warning instead?
                            # raise ValueError(f"Search term {old_t} is ambiguous")
                            pass
                if not found:
                    raise ValueError(f"Could not find team {old_t}")
                else:
                    ids.append(id)

        return ids
