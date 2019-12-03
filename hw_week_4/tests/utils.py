import datetime
import hashlib
from typing import Dict, Union

import api


def set_valid_auth(request: Dict[str, Union[str, Dict, int]]):

    """
    Sets valid authorization token
    """

    if request.get("login") == api.ADMIN_LOGIN:
        request["token"] = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        msg = request.get("account", "") + request.get("login", "") + api.SALT
        request["token"] = hashlib.sha512(msg.encode("utf-8")).hexdigest()