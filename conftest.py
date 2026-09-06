import logging
import uuid
from typing import Dict
from pathlib import Path

import pytest
import requests
from faker import Faker

from constants import BASE_URL, LOGIN, REGISTER
from models import TokenResponse, UserResponse

logger = logging.getLogger("archiscope")

IMAGE_PATH = Path(__file__).parent / "data" / "test_image.png"
fake = Faker("ru_RU")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="function")
def test_user_credentials() -> Dict[str, str]:
    unique = uuid.uuid4().hex[:8]
    return {
        "email": f"test{unique}@example.com",
        "password": f"password{unique}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "phone": "+79001234567"
    }


@pytest.fixture(scope="function")
def api_client(base_url: str, test_user_credentials: Dict):

    class APIClient:
        def __init__(self):
            self.base_url = base_url
            self.test_user_credentials = test_user_credentials
            self.session = requests.Session()
            self.token = None
            self.user_id = None

        def set_token(self, token: str):
            self.token = token
            self.session.headers.update({
                "Authorization": f"Bearer {token}"
            })

        def clear_token(self):
            self.token = None
            self.session.headers.pop("Authorization", None)

        def _get_headers(self) -> Dict:
            headers = {"Content-Type": "application/json"}
            return headers

        def request(self, method: str, endpoint: str,
                    expected_status: int = 200, **kwargs) -> requests.Response:
            url = f"{self.base_url}{endpoint}"

            if "headers" not in kwargs:
                kwargs["headers"] = self._get_headers()

            if "files" in kwargs or "data" in kwargs:
                kwargs["headers"].pop("Content-Type", None)

            logger.info(f"{method} {url}")

            response = self.session.request(method, url, **kwargs)

            logger.info(f"Ответ {response.status_code} на {method} {url}")

            assert response.status_code == expected_status, (
                f"Expected {expected_status}, got {response.status_code}. "
                f"Response: {response.text[:300]}"
            )

            return response

        def post(self, endpoint: str, **kwargs):
            return self.request("POST", endpoint, **kwargs)

        def get(self, endpoint: str, **kwargs):
            return self.request("GET", endpoint, **kwargs)

    return APIClient()


@pytest.fixture(scope="function")
def registered_user(api_client, test_user_credentials) -> Dict[str, str]:
    api_client.post(
        REGISTER,
        json={
            "email": test_user_credentials["email"],
            "password": test_user_credentials["password"],
            "first_name": test_user_credentials["first_name"],
            "last_name": test_user_credentials["last_name"],
            "phone": test_user_credentials["phone"],
        },
        expected_status=200,
    )
    logger.info(f"Зарегистрирован пользователь {test_user_credentials['email']}")
    return test_user_credentials


@pytest.fixture(scope="function")
def auth_client(api_client, registered_user):
    login_data = {
        "username": registered_user["email"],
        "password": registered_user["password"],
    }
    response = api_client.post(
        LOGIN,
        data = login_data,
        expected_status = 200,
    )

    token_data = TokenResponse(**response.json())
    api_client.set_token(token_data.access_token)

    user_response = api_client.get("/api/users/me", expected_status=200)
    user_data = UserResponse(**user_response.json())
    api_client.user_id = user_data.id

    logger.info(f"Авторизован пользователь {registered_user['email']}")
    return api_client


@pytest.fixture(scope="function")
def news_data() -> Dict[str, str]:
    news = {
        "title": f"{fake.sentence(nb_words = 6).rstrip('.')}",
        "subtitle": fake.sentence(nb_words = 5).rstrip("."),
        "text": fake.sentence(nb_words = 30),
        "tags": ", ".join(fake.words(nb = 3, unique = True)),
    }
    logger.info(f"создана новость {news['title']}")
    return news


@pytest.fixture(scope="function")
def comment_data() -> Dict[str, str]:
    comment = {"text": fake.sentence(nb_words = 8).rstrip(".")}
    logger.info(f"создан комментарий: {comment['text']}")
    return comment


@pytest.fixture(scope="function")
def image_file() -> tuple:
    return "test_image.png", IMAGE_PATH.read_bytes(), "image/png"