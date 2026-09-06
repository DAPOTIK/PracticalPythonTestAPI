import allure
import pytest

from constants import CURRENT_USER, LOGIN, REGISTER
from models import ErrorResponse, HTTPValidationError, TokenResponse, UserResponse


@allure.feature("Авторизация")
class TestAuth:

    @allure.story("Регистрация")
    @allure.title("Позитивный тест. Успешная регистрация нового пользователя")
    @allure.description("Регистрация с валидными данными. Ожидается 200 и совпадение полей ответа с отправленными")
    @pytest.mark.positive
    @pytest.mark.smoke
    def test_register_success(self, api_client, test_user_credentials) -> None:
        with allure.step("Данные нового пользователя"):
            user_data = {
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
                "first_name": test_user_credentials["first_name"],
                "last_name": test_user_credentials["last_name"],
                "phone": test_user_credentials["phone"],
            }

        with allure.step("POST /api/auth/register возвращает 200"):
            response = api_client.post(REGISTER, json = user_data, expected_status = 200)

        with allure.step("Тело ответа соответствует модели UserResponse"):
            user = UserResponse(**response.json())

        with allure.step("Поля ответа совпадают с отправленными данными"):
            assert user.id > 0
            assert user.email == test_user_credentials["email"]
            assert user.first_name == test_user_credentials["first_name"]
            assert user.last_name == test_user_credentials["last_name"]
            assert user.phone == test_user_credentials["phone"]
            assert user.created_at is not None

    @allure.story("Регистрация")
    @allure.title("Негативный тест. Регистрация с уже существующим email")
    @allure.description("Повторная регистрация пользователя. Ожидается 400 и сообщение об ошибке")
    @pytest.mark.negative
    def test_register_existing_email(self, api_client, registered_user) -> None:
        with allure.step("Данные уже зарегистрированного пользователя"):
            user_data = {
                "email": registered_user["email"],
                "password": registered_user["password"],
                "first_name": registered_user["first_name"],
                "last_name": registered_user["last_name"],
                "phone": registered_user["phone"],
            }

        with allure.step("Повторная регистрация возвращает 400"):
            response = api_client.post(REGISTER, json = user_data, expected_status = 400)

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Регистрация")
    @allure.title("Негативный тест. Регистрация с некорректным email")
    @allure.description("В поле email строка без домена. Ожидается 422 по полю email")
    @pytest.mark.negative
    def test_register_invalid_email(self, api_client, test_user_credentials) -> None:
        with allure.step("Данные с email без домена"):
            user_data = {
                "email": "example",
                "password": test_user_credentials["password"],
                "first_name": test_user_credentials["first_name"],
                "last_name": test_user_credentials["last_name"],
            }

        with allure.step("POST /api/auth/register возвращает 422"):
            response = api_client.post(REGISTER, json = user_data, expected_status = 422)

        with allure.step("Ошибка валидации"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("email" in detail.loc for detail in error.detail)

    @allure.story("Регистрация")
    @allure.title("Негативный тест. Регистрация со слишком коротким паролем")
    @allure.description("Пароль короче минимальной длины. Ожидается 422 по полю password")
    @pytest.mark.negative
    def test_register_short_password(self, api_client, test_user_credentials) -> None:
        with allure.step("Пароль из трёх символов"):
            user_data = {
                "email": test_user_credentials["email"],
                "password": "1BS",
                "first_name": test_user_credentials["first_name"],
                "last_name": test_user_credentials["last_name"],
            }

        with allure.step("POST /api/auth/register возвращает 422"):
            response = api_client.post(REGISTER, json = user_data, expected_status = 422)

        with allure.step("Ошибка валидации"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("password" in detail.loc for detail in error.detail)

    @allure.story("Регистрация")
    @allure.title("Негативный тест. Регистрация без обязательного поля")
    @allure.description("Из тела поочерёдно удаляется каждое обязательное поле. Ожидается 422 по этому полю")
    @pytest.mark.negative
    @pytest.mark.parametrize("missing_field", ["email", "password", "first_name", "last_name"])
    def test_register_without_required_field(self, api_client, test_user_credentials, missing_field: str) -> None:
        with allure.step(f"Данные без поля {missing_field}"):
            user_data = {
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
                "first_name": test_user_credentials["first_name"],
                "last_name": test_user_credentials["last_name"],
            }
            user_data.pop(missing_field)

        with allure.step("POST /api/auth/register возвращает 422"):
            response = api_client.post(REGISTER, json = user_data, expected_status = 422)

        with allure.step(f"Ошибка валидации на поле {missing_field}"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any(missing_field in detail.loc for detail in error.detail)

    @allure.story("Вход в систему")
    @allure.title("Позитивный тест. Успешный вход в систему")
    @allure.description("Вход с валидными данными. Ожидается 200")
    @pytest.mark.positive
    @pytest.mark.smoke
    def test_login_success(self, api_client, registered_user) -> None:
        with allure.step("Валидные учетные данные"):
            login_data = {
                "username": registered_user["email"],
                "password": registered_user["password"],
            }

        with allure.step("POST /api/auth/login возвращает 200"):
            response = api_client.post(LOGIN, data = login_data, expected_status = 200)

        with allure.step("Тело ответа соответствует модели TokenResponse"):
            token = TokenResponse(**response.json())
            assert token.access_token is not None
            assert len(token.access_token) > 20
            assert token.token_type == "bearer"

        with allure.step("Токен даёт доступ к данным пользователя"):
            api_client.set_token(token.access_token)
            user_response = api_client.get(CURRENT_USER, expected_status = 200)
            user = UserResponse(**user_response.json())
            assert user.email == registered_user["email"]
            assert user.first_name == registered_user["first_name"]
            assert user.last_name == registered_user["last_name"]

    @allure.story("Вход в систему")
    @allure.title("Негативный тест. Вход с валидным email и неверным паролем")
    @allure.description("Пользователь существует, пароль неверный. Ожидается 401")
    @pytest.mark.negative
    def test_login_wrong_password(self, api_client, registered_user) -> None:
        with allure.step("Данные с неверным паролем"):
            login_data = {
                "username": registered_user["email"],
                "password": "IBSPassword123",
            }

        with allure.step("POST /api/auth/login возвращает 401"):
            response = api_client.post(LOGIN, data = login_data, expected_status = 401)

        with allure.step("Тело содержит ошибку"):
            error = ErrorResponse(**response.json())
            assert error.detail
            assert "access_token" not in response.json()

    @allure.story("Вход в систему")
    @allure.title("Негативный тест. Вход с некорректным форматом email")
    @allure.description("В поле username передаётся example вместо example@mail.com. Ожидается 401")
    @pytest.mark.negative
    def test_login_invalid_email(self, api_client, registered_user) -> None:
        with allure.step("Данные с логином example вместо email"):
            login_data = {
                "username": "example",
                "password": registered_user["password"],
            }

        with allure.step("POST /api/auth/login возвращает 401"):
            response = api_client.post(LOGIN, data = login_data, expected_status = 401)

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Вход в систему")
    @allure.title("Негативный тест. Вход несуществующего пользователя")
    @allure.description("Тест валидного незарегистрированный email. Ожидается 401")
    @pytest.mark.negative
    def test_login_not_existing_user(self, api_client, test_user_credentials) -> None:
        with allure.step("Данные незарегистрированного пользователя"):
            login_data = {
                "username": test_user_credentials["email"],
                "password": test_user_credentials["password"],
            }

        with allure.step("POST /api/auth/login возвращает 401"):
            response = api_client.post(LOGIN, data = login_data, expected_status = 401)

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Вход в систему")
    @allure.title("Негативный тест. Вход без пароля")
    @allure.description("В форме отсутствует обязательное поле password. Ожидается 422 по этому полю")
    @pytest.mark.negative
    def test_login_without_password(self, api_client, registered_user) -> None:
        with allure.step("Форма без поля password"):
            login_data = {"username": registered_user["email"]}

        with allure.step("POST /api/auth/login возвращает 422"):
            response = api_client.post(LOGIN, data = login_data, expected_status = 422)

        with allure.step("Ошибка валидации указывает на поле password"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("password" in detail.loc for detail in error.detail)

    @allure.story("Вход в систему")
    @allure.title("Негативный тест. Вход без email")
    @allure.description("В форме отсутствует обязательное поле username. Ожидается 422 по этому полю")
    @pytest.mark.negative
    def test_login_without_email(self, api_client, registered_user) -> None:
        with allure.step("Форма без поля username"):
            login_data = {"password": registered_user["password"]}

        with allure.step("POST /api/auth/login возвращает 422"):
            response = api_client.post(LOGIN, data = login_data, expected_status = 422)

        with allure.step("Ошибка валидации указывает на поле username"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("username" in detail.loc for detail in error.detail)

    @allure.story("Вход в систему")
    @allure.title("Негативный тест. Вход с пустыми учётными данными")
    @allure.description("Оба поля формы переданы пустыми строками. Ожидается 401, токен не выдаётся")
    @pytest.mark.negative
    def test_login_empty_credentials(self, api_client) -> None:
        with allure.step("Форма с пустыми значениями"):
            login_data = {"username": "", "password": ""}

        with allure.step("POST /api/auth/login возвращает 401"):
            response = api_client.post(LOGIN, data = login_data, expected_status = 401)

        with allure.step("Тело содержит ошибку, токен не выдан"):
            error = ErrorResponse(**response.json())
            assert error.detail
            assert "access_token" not in response.json()