import functools
import httpx
import json
import logging

from datetime import datetime
from flask import Flask, abort, jsonify
from werkzeug.exceptions import HTTPException


class API(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_error_handler(HTTPException, self.error_handler)

    def error_handler(self, e):
        return {"title": f"{e.code}: {e.name}"}, e.code


api = API(__name__)


@functools.cache
def fetch_data(query):
    day = query.strftime("%d")
    month = query.strftime("%m")
    req = httpx.post(
        "https://namedays.tm-tieto.fi/api/public/namedays-search",
        headers={"Content-type": "application/json"},
        data=json.dumps(
            {"q": "*", "per_page": 100, "filter_by": f"day:={day} && month:={month}"}
        ),
    )

    data = req.json()
    if not data["success"]:
        abort(502)

    ret = {}
    for k in (
        "hevonen",
        "historiallinen",
        "kissa",
        "koira",
        "ortod",
        "ruotsi",
        "saame",
        "suomi",
    ):
        ret[k] = []
    for entry in data["data"]["hits"]:
        ret[entry["document"]["type"]].append(entry["document"]["name"])
    return ret


@api.route("/", defaults={"isodate": None}, methods=["GET"])
@api.route("/<isodate>", methods=["GET"])
def handler(isodate):
    if isodate is None:
        isodate = datetime.now()
    else:
        try:
            isodate = datetime.strptime(query, "%Y-%m-%d")
        except ValueError:
            api.logger.warning("Invalid date {}".format(repr(query)))
            abort(400)
    return jsonify(fetch_data(isodate))


if __name__ == "__main__":
    api.run(host="127.0.0.1", port=8000, debug=True)
else:
    gunicorn_logger = logging.getLogger("gunicorn.error")
    api.logger.handlers = gunicorn_logger.handlers
    api.logger.setLevel(gunicorn_logger.level)
