import os
from http import HTTPStatus
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from clay import core, logger, types


class HeaderBuilder:
    @staticmethod
    def auth_via_static_token(header: Dict[str, Any]) -> Dict[str, Any]:
        token = os.getenv("DEXTER_CLB_AUTH_TOKEN")
        header["Authorization"] = f"Token {token}"
        return header

    @staticmethod
    def auth_via_jwt_token(header: Dict[str, Any]) -> Dict[str, Any]:
        token = os.getenv("DEXTER_CLB_AUTH_TOKEN")
        header["Authorization"] = f"Bearer {token}"
        return header

    @staticmethod
    def auth_via_resource_owner_header(header: Dict[str, Any]) -> Dict[str, Any]:
        uid = os.getenv(core.SUB_ENVVAR)
        orgids = os.getenv(core.ORGIDS_ENVVAR)
        if uid and orgids:
            header[core.ORGIDS_HEADER_KEY] = orgids
            header[core.SUB_HEADER_KEY] = uid
        return header

    @staticmethod
    def init_header() -> Dict[str, Any]:
        auth_method = core.CallbackAuthMethod.get_method()
        h: Dict[str, Any] = {}
        if auth_method == core.CallbackAuthMethod.GATEWAY_TOKEN:
            h = HeaderBuilder.auth_via_resource_owner_header(h)
        elif auth_method == core.CallbackAuthMethod.JWT_TOKEN:
            h = HeaderBuilder.auth_via_jwt_token(h)
        else:
            h = HeaderBuilder.auth_via_static_token(h)
        return h


def _fire_callback_to_dexter(
    clb: types.Callback,
    logger: logger.Logger,
    dexter_clb_url: Optional[str] = None,
    dexter_host: Optional[str] = None,
    dexter_port: Optional[str] = None,
) -> bool:
    headers = HeaderBuilder.init_header()

    headers["Content-Type"] = "application/json"

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])  # type: ignore
    session.mount("http://", HTTPAdapter(max_retries=retries))

    run_type = os.getenv(types._CommonEnvvars.DEXTER_RUN_TYPE.value, core.RunType.WORKFLOW.value)
    if run_type == core.RunType.WORKFLOW.value:
        data = {"data": clb.model_dump(by_alias=True, exclude_none=True)}
        logger.debug(f"Data for callback: {data}")

        # check if `dexter_clb_url` is set
        if dexter_clb_url is None or dexter_clb_url == "":
            logger.warning(f"found `dexter_clb_url` as {dexter_clb_url}. Hence not firing callback")
            return False

        resp = session.post(url=dexter_clb_url, json=data, headers=headers)
    else:
        # TODO: Refactor this to use clb.model_dump
        data = {
            "status": clb.State.value,
            "output": clb.Result,
            "failure_type": clb.FailureType,
        }
        logger.debug(f"Data for callback: {data}")

        if dexter_host is None or dexter_port is None or dexter_host == "" or dexter_port == "":
            logger.warning("found invalid values for `dexter_host` and / or `dexter_port` hence not firing callback.")
            return False

        resp = session.post(
            url="{0}:{1}/v1alpha1/inferences/{2}".format(dexter_host, dexter_port, clb.Id),
            json=data,
            headers=headers,
        )

    if (
        resp.status_code == HTTPStatus.ACCEPTED
        or resp.status_code == HTTPStatus.NO_CONTENT
        or resp.status_code == HTTPStatus.OK
    ):
        logger.info("successfully update state")
    else:
        logger.error(f"state update failed with status code: {resp.status_code}")
        return False
    return True
