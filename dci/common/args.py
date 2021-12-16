import csv
from datetime import datetime


def _get_csv(element, dict):
    e = dict.get(element, [])
    if e:
        return list(csv.reader([e]))[0]
    return e


def _get_int(element, dict):
    e = dict.get(element, None)
    if e:
        return int(e)
    return e


def _get_date(element, dict):
    e = dict.get(element, None)
    if e:
        try:
            return datetime.strptime(e, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            pass

        return datetime.strptime(e, "%Y-%m-%d")


def parse_args(args):
    return {
        "limit": _get_int("limit", args),
        "offset": _get_int("offset", args),
        "sort": _get_csv("sort", args),
        "where": _get_csv("where", args),
        "embed": _get_csv("embed", args),
        "created_after": _get_date("created_after", args),
        "updated_after": _get_date("updated_after", args)
    }
