import flask

from dci.api.v2 import api
from dci.api.v1.notifications import publish
import logging

logger = logging.getLogger(__name__)


@api.route("/pubmsg", methods=["GET"])
def pubmsg():
    publish({"event": "pubmsg", "msg": "toto"})

    return flask.Response("Processing", 200, content_type="text/plain")
