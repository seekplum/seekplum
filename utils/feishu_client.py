import base64
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Collection, Optional
from pathlib import Path
import requests
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

FEISHU_DOMAIN = "https://open.feishu.cn/open-apis"
FEISHU_APP_ID = os.environ["FEISHU_APP_ID"]
FEISHU_APP_SECRET = os.environ["FEISHU_APP_SECRET"]


def requests_retry_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: Collection[int] = (500, 502, 503, 504),
) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["POST", "GET", "PUT"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def dumps(data: Any, ensure_ascii: bool = False, separators: Optional[tuple[str, str]] = None, **kwargs: Any) -> str:
    if separators is None:
        separators = (",", ":")
    return json.dumps(data, ensure_ascii=ensure_ascii, separators=separators, **kwargs)


def optional_loads(value: Optional[str | dict]) -> Optional[dict]:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


class FeishuUser(BaseModel):
    token: str = Field(..., description="token")
    expired: datetime = Field(..., description="过期时间")


class FeishuAPIError(Exception):
    def __init__(self, code: int = 0, msg: str = "", error: Optional[dict] = None, **kwargs: dict) -> None:
        super().__init__()
        self.code = code
        self.msg = msg
        self.error = error
        self.kwargs = kwargs
        self.str = ": ".join(str(i) for i in [self.code, self.msg, self.error] if i)

    def __repr__(self) -> str:
        return self.str

    def __str__(self) -> str:
        return self.str


class FeishuClient:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        app_id: str = FEISHU_APP_ID,
        app_secret: str = FEISHU_APP_SECRET,
        *,
        user_path: str = "/tmp/test_feishu_user.txt",  # nosec B108
        default_headers: Optional[dict] = None,
        default_timeout: Optional[int] = None,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.default_headers = {"Content-Type": "application/json"} if default_headers is None else default_headers
        self.default_timeout = default_timeout or 5

        self.user: Optional[FeishuUser] = None
        self.user_path = user_path
        self._session: Optional[requests.Session] = None
        self.x_ogw_ratelimit_limit = 0
        self.x_ogw_ratelimit_reset = 0

    @property
    def session(self) -> requests.Session:
        if not self._session:
            self._session = requests_retry_session()
        return self._session

    def gen_headers(self, headers: Optional[dict] = None) -> dict:
        return self.default_headers | (headers or {})

    def gen_timeout(self, timeout: Optional[int] = None) -> int:
        return self.default_timeout if timeout is None else timeout

    def post(
        self, url: str, headers: Optional[dict] = None, timeout: Optional[int] = None, **kwargs: Any
    ) -> requests.Response:
        return self.session.post(url, headers=self.gen_headers(headers), timeout=self.gen_timeout(timeout), **kwargs)

    def save_user(self, user: FeishuUser) -> None:
        with open(self.user_path, "w+", encoding="utf-8") as fp:
            fp.write(user.model_dump_json())

    def fetch_user(self) -> FeishuUser:
        logger.info("fetch_user")
        ret: dict = self.post(
            f"{FEISHU_DOMAIN}/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        ).json()
        token = ret.get("tenant_access_token")
        if not token:
            raise FeishuAPIError(msg=ret.get("msg", "unknown error"))
        user = FeishuUser(token=token, expired=datetime.now() + timedelta(seconds=ret.get("expire", 0)))
        self.save_user(user)
        return user

    def get_user_by_cache(self) -> Optional[FeishuUser]:
        if not Path(self.user_path).exists():
            return None
        try:
            with open(self.user_path, "r", encoding="utf-8") as fp:
                user_json = fp.read()
            if user_json:
                return FeishuUser.model_validate_json(user_json)
        except Exception as e:
            logger.warning("load user from file error: %s", e)
        return None

    def get_token(self) -> str:
        if self.user is not None and self.user.expired > datetime.now():
            return self.user.token
        user = self.get_user_by_cache()
        if user is None or user.expired < datetime.now():
            user = self.fetch_user()
        self.user = user
        return user.token

    def request(
        self,
        path: str,
        params: Optional[dict] = None,
        path_params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }
        logger.info(
            "[FeishuApi]request path: %s, path_params: %s, params: %s, data: %s",
            path,
            path_params,
            params,
            data,
        )
        try:
            request_path = re.sub(r":([A-Za-z0-9_]+)", "{\1}", path).format(**path_params or {})
        except KeyError as e:
            raise FeishuAPIError(code=-1, msg=f"路径参数{e.args[0]}未设置") from e
        resp = self.post(
            f"{FEISHU_DOMAIN}{request_path}",
            params=params,
            json=data,
            headers=headers,
        )
        logger.info("[FeishuApi]response path: %s, headers: %s, data: %s", path, resp.headers, resp.text)
        self.x_ogw_ratelimit_limit = int(resp.headers.get("X-Ogw-Ratelimit-Limit", 0))
        self.x_ogw_ratelimit_reset = int(resp.headers.get("X-Ogw-Ratelimit-Reset", 0))
        try:
            ret: dict = resp.json()
        except ValueError as e:
            raise FeishuAPIError(code=-2, msg=f"feishu api json-error: {str(e)} || {resp.text}") from e
        if resp.status_code != 200 or ret.get("code") != 0:
            raise FeishuAPIError(**ret)
        return ret

    def image_ocr(self, image: str) -> dict:
        # https://open.feishu.cn/document/server-docs/ai/optical_char_recognition-v1/basic_recognize
        ret = self.request("/optical_char_recognition/v1/image/basic_recognize", data={"image": image})
        return ret.get("data", {})

    def translate(
        self, text: str, source_language: str = "zh", target_language: str = "en", glossary: Optional[list[dict]] = None
    ) -> dict:
        # https://open.feishu.cn/document/server-docs/ai/translation-v1/translate
        data: dict[str, Any] = {"source_language": source_language, "target_language": target_language, "text": text}
        if glossary:
            data["glossary"] = glossary
        ret = self.request("/translation/v1/text/translate", data=data)
        return ret.get("data", {})

    def batch_get_id(
        self,
        user_id_type: str = "user_id",
        emails: Optional[list[str]] = None,
        mobiles: Optional[list[str]] = None,
        include_resigned: bool = True,
    ) -> dict:
        # 通过手机号或邮箱获取用户 ID, https://open.feishu.cn/document/server-docs/contact-v3/user/batch_get_id
        if not emails and not mobiles:
            raise TypeError("")
        data = {
            "user_id_type": user_id_type,
            "emails": emails,
            "mobiles": mobiles,
            "include_resigned": include_resigned,
        }
        ret = self.request("/contact/v3/users/batch_get_id", data=data)
        return ret.get("data", {})


client = FeishuClient()


def test1() -> None:
    token = client.get_token()
    print("token:", token)


def test2() -> None:
    with open("test-ocr1.png", "rb") as f:
        image_content = base64.encodebytes(f.read()).decode("utf-8")
    res = client.image_ocr(image_content)
    print("ocr result:", res)


def test3() -> None:
    max_retry = 100
    for i in range(max_retry):
        if client.x_ogw_ratelimit_limit == 0:
            time.sleep(client.x_ogw_ratelimit_reset)
        try:
            res = client.translate("你好，世界！", source_language="zh", target_language="en")
        except FeishuAPIError as e:
            if i == max_retry - 1:
                raise e
            if e.code == 99991400:
                print("retry...", i, client.x_ogw_ratelimit_limit, client.x_ogw_ratelimit_reset)
                continue
            logger.error("%d, %s", i, e)
            break
        print("success...", i, res)
        break


def test4() -> None:
    res = client.batch_get_id(mobiles=["xxx"])
    print(res)


if __name__ == "__main__":
    try:
        test4()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
