from typing import List, Union

from pysbr.queries.lines import Lines
from pysbr.queries.query import Query
import pysbr.utils as utils


class Consensus(Lines):
    @Query.typecheck
    def __init__(
        self, event_ids: Union[List[int], int], market_ids: Union[List[int], int]
    ):
        super().__init__()
        event_ids = utils.make_list(event_ids)
        market_ids = utils.make_list(market_ids)
        self.name = "consensus"
        self.arg_str = self._get_args("lines")
        self.args = {"eids": event_ids, "mtids": market_ids}
        self.fields = self._get_fields("consensus")
        self._raw = self._build_and_execute_query(
            self.name, self.fields, self.arg_str, self.args
        )

    def _clean_lines(self, *args):
        pass
