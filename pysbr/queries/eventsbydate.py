from pysbr.queries.query import Query
from pysbr.utils import Utils


class EventsByDate(Query):
    def __init__(self, league_id, dt):
        super().__init__()
        self.name = "eventsByDateNew"
        self.arg_str = self._get_args("date")
        self.fields = self._get_fields("event")
        self.args = {"lids": [league_id], "timestamp": Utils.datetime_to_timestamp(dt)}
        self._raw = self._build_and_execute_query(
            self.name, self.fields, self.arg_str, self.args
        )