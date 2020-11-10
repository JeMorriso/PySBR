from pysbr.queries.query import Query
from pysbr.utils import Utils


class EventsByDateRange(Query):
    def __init__(self, league_id, start, end):
        super().__init__()
        self.name = "eventsV2"
        self.arg_str = self._get_args("date_range")
        self.args = {
            "lids": [league_id],
            "start": Utils.datetime_to_timestamp(start),
            "end": Utils.datetime_to_timestamp(end),
        }
        self.fields = self._get_fields("event")
        self._raw = self._build_and_execute_query(
            self.name, self.fields, self.arg_str, self.args
        )
