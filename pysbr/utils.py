import json
from inspect import cleandoc
from textwrap import indent
from datetime import datetime
from pathlib import Path

from pytz import timezone, utc
import yaml


class Utils:
    @staticmethod
    def dict_to_json(d, path):
        with open(path, "w") as f:
            json.dump(d, f, indent=2)

    @staticmethod
    def json_to_dict(path):
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def load_yaml(path):
        """[summary]

        Args:
            path ([type]): [description]

        Returns:
            [type]: [description]

        Raises:
            FileNotFoundError
        """
        with open(path) as f:
            return yaml.full_load(f)

    @staticmethod
    def dump_yaml(d, path):
        with open(path, "w") as f:
            yaml.dump(d, f)

    @staticmethod
    def get_project_root():
        return Path(__file__).parent.parent

    @staticmethod
    def build_yaml_path(fname, subpath="pysbr/config"):
        # TODO: use constant for yaml dir
        return Utils.get_project_root().joinpath(f"{subpath}/{fname}.yaml")

    @staticmethod
    def str_format(s, indent_=0, dedent_l1=False):
        """Format multiline string.

        Args:
            s (str): The string to format.
            indent_ (int, optional): Number of tabs to indent. Defaults to 0.
            dedent_l1 (bool, optional): Set line 1 indentation to 0. Defaults to False.

        Returns:
            str: The formatted string.
        """
        tab = "    "
        s = indent(cleandoc(s), tab * indent_)
        if dedent_l1:
            lines = s.split("\n")
            lines[0] = lines[0].lstrip()
            s = "\n".join(lines)
        return s

    @staticmethod
    def datetime_to_timestamp_aware(dt, tz=None):
        """**DEPRECATED** Convert python datetime object to epoch time.

        Note:
            The datetime object is naive, so localize using timezone.

        Args:
            dt (datetime.datetime): The datetime object.
            tz (str, optional): The timezone to use (see pytz documentation for list of
                available timezones). If None, uses system timezone. Defaults to None.

        Returns:
            float: Timestamp for the given datetime, for the given timezone.
        """
        if dt.tzinfo is None:
            dt = timezone(tz).localize(dt) if tz is not None else dt.astimezone()
        return int(dt.timestamp() * 1000)

    @staticmethod
    def timestamp_to_datetime_aware(ts, tz=None):
        """**DEPRECATED** Convert epoch timestamp to aware datetime object.

        Args:
            ts (int): The timestamp.
            tz (str, optional): The timezone to use (see pytz documentation for list of
                available timezones). If None, uses system timezone. Defaults to None.

        Returns:
            datetime.datetime: The timezone aware datetime object.
        """
        utc_dt = utc.localize(datetime.utcfromtimestamp(ts / 1000))
        return utc_dt.astimezone(timezone(tz) if tz is not None else None)

    @staticmethod
    def datetime_to_timestamp(dt):
        return int(dt.timestamp() * 1000)

    @staticmethod
    def timestamp_to_datetime(ts):
        return datetime.fromtimestamp(ts / 1000).astimezone()

    @staticmethod
    def timestamp_to_iso_str(ts):
        return Utils.timestamp_to_datetime(ts).replace(microsecond=0).isoformat()

    @staticmethod
    def translation_dict():
        return Utils.load_yaml(Utils.build_yaml_path("dictionary"))

    @staticmethod
    def translate_dict(d, t):
        def _recurse(el):
            if isinstance(el, dict):
                # MUST cast to list to avoid RuntimeError because d.pop()
                for k in list(el.keys()):
                    try:
                        old_k = k
                        # raises KeyError if no translation available
                        k = t[k]

                        v = el.pop(old_k)
                        # if v in ["datetime"]:
                        # v = Utils.timestamp_to_datetime(v)
                        if k not in ["datetime", "start datetime", "end datetime"]:
                            el[k] = v
                        else:
                            try:
                                el[k] = Utils.timestamp_to_iso_str(v)
                            except TypeError:
                                el[k] = v
                    except KeyError:
                        pass
                    v = el[k]
                    if isinstance(v, dict) or isinstance(v, list):
                        _recurse(v)
            elif isinstance(el, list):
                for x in el:
                    _recurse(x)

        _recurse(d)
