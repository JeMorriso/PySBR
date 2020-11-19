from string import Template
import copy
import typing

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd

import pysbr.utils as utils
from pysbr.config.config import Config


class Query:
    def __init__(self):
        self._config = Config()

        self._raw = None
        self._subpath_keys = None
        self._sublist_keys = None
        self._id_key = None

        self._translated = None

        transport = RequestsHTTPTransport(
            url="https://www.sportsbookreview.com/ms-odds-v2/odds-v2-service"
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=False)

    def typecheck(f):
        def recurse(a, t):
            t_origin = typing.get_origin(t)
            t_args = typing.get_args(t)

            if t_origin is None and len(t_args) == 0:
                if not isinstance(a, t):
                    return False

            elif isinstance(t_origin, type(list)):
                if not isinstance(a, list):
                    return False
                if len(t_args) > 0:
                    try:
                        for x in a:
                            for arg in t_args:
                                if not recurse(x, arg):
                                    return False
                    except TypeError:
                        return False
                else:
                    if not isinstance(a, t_origin):
                        return False

            elif isinstance(t_origin, typing._SpecialForm):
                for arg in t_args:
                    is_arg = recurse(a, arg)
                    if is_arg:
                        return True
                return False

            return True

        def wrapper(*args):
            types = list(typing.get_type_hints(f).values())
            # first argument is self, ignore it
            for a, t in zip(args[1:], types):
                valid = recurse(a, t)
                if not valid:
                    raise TypeError(f"Expected {t}, got {a}")

            f(*args)

        return wrapper

    def _build_args(self, arg_str, args):
        """Build the argument string that gets inserted into a query.

        Args:
            arg_str (str): The arguments template string.
            args (dict): The substitutions to make. Each key must match a template
                placeholder, with the value being what gets substituted into the string.

        Returns:
            str: The argument string, with values inserted for each argument.
        """
        if arg_str is not None and args is not None:
            return Template(arg_str).substitute(args)
        else:
            return None

    def _build_query_string(self, q_name, q_fields=None, q_args=None):
        """Build up the GraphQL query string.

        Args:
            q_name (str): The name of the query object to be queried.
            q_fields (str): The fields to return.
            q_args (str, optional): The arg names to pass to the query. Defaults to
                None.

        Returns:
            str: The query string ready to be substituted using Template.substitute()
        """
        return (
            Template(
                utils.str_format(
                    """
                query {
                    $q_name(
                        $q_args
                    ) $q_fields
                }
            """
                )
            ).substitute(
                {
                    "q_name": q_name,
                    "q_args": ""
                    if q_args is None
                    else utils.str_format(q_args, indent_=2, dedent_l1=True),
                    "q_fields": ""
                    if q_fields is None
                    else utils.str_format(q_fields, indent_=1, dedent_l1=True),
                }
            )
            # graphql query will not accept single quotes, but Template string by
            # default uses single quotes
            .replace("'", '"')
        )

    def _get_val_from_yaml(self, fname, k):
        """[summary]

        Args:
            fname ([type]): [description]
            type ([type]): [description]

        Returns:
            [type]: [description]

        Raises:
            NameError: If value of k is not a key in the loaded dictionary.
        """
        return utils.load_yaml((utils.build_yaml_path(fname)))[k]

    def _get_args(self, k):
        return self._get_val_from_yaml("arguments", k)

    def _get_fields(self, k):
        return self._get_val_from_yaml("fields", k)

    def _execute_query(self, q):
        """Execute a graphql query.

        Args:
            q (str): The query string.

        Returns:
            dict: The result of the query.
        """
        return self.client.execute(gql(q))

    def _build_and_execute_query(
        self, q_name, q_fields=None, q_arg_str=None, q_args=None
    ):
        q_string = self._build_query_string(
            q_name, q_fields, self._build_args(q_arg_str, q_args)
        )
        return self._execute_query(q_string)

    def _find_data(self):
        data = self._raw[self.name]
        if self._subpath_keys is not None:
            for k in self._subpath_keys:
                data = data[k]

        return data

    def _translate_dict(self, d):
        def _recurse(el):
            if isinstance(el, dict):
                # MUST cast to list to avoid RuntimeError because d.pop()
                for k in list(el.keys()):
                    try:
                        old_k = k
                        # raises KeyError if no translation available
                        k = t[k]

                        v = el.pop(old_k)

                        if k not in ["datetime", "start datetime", "end datetime"]:
                            el[k] = v
                        else:
                            try:
                                el[k] = utils.timestamp_to_iso_str(v)
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

        t = self._config.translations()
        _recurse(d)
        return d

    def _copy_and_translate_data(self):
        if self._translated is None:
            data = copy.deepcopy(self._find_data())
            self._translated = self._translate_dict(data)
        return copy.deepcopy(self._translated)

    # for queries returning ids call this function to process _raw and return ids only
    def ids(self):
        if self._id_key is None:
            raise NotImplementedError(
                f"{type(self).__name__} does not have a default return id type"
            )

        translated = self.list()
        ids = []
        for el in translated:
            ids.append(el[self._id_key])

        return list(set(ids))

    def list(self):
        data = self._copy_and_translate_data()
        # Some queries return dictionaries. Enforce this method returning a list.
        if isinstance(data, dict):
            data = [data]
        return data

    def dataframe(self):
        data = self._copy_and_translate_data()

        # Using sublist_keys instead of recursive method because there is a possibility
        # of overwriting keys without realizing it if using recursive method
        # The idea is that pd.json_normalize() doesn't work on sublists
        if self._sublist_keys is not None:
            for k in self._sublist_keys:
                for el in data:
                    for i, subel in enumerate(el[k]):
                        new_key = f"{k}.{i+1}"
                        el[new_key] = subel
                    el.pop(k)
        try:
            return pd.json_normalize(data)
        except AttributeError:
            return pd.DataFrame(data)
