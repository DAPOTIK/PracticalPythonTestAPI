import allure
import pytest

from constants import NEWS, NEWS_COMMENTS
from models import CommentResponse, ErrorResponse, HTTPValidationError, NewsResponse

@allure.feature("Комментарии")
class TestComments:

    @allure.story("Создание комментария")
    @allure.title("Позитивный тест. Создание комментария к новости")
    @allure.description("Комментирование созданной новости. Ожидается 200, автором указан текущий пользователь")
    @pytest.mark.positive
    @pytest.mark.smoke
    def test_create_comment(self, auth_client, news_data, comment_data) -> None:
        with allure.step("Создание новости"):
            create_response = auth_client.post(NEWS, data = news_data, expected_status = 200)
            news = NewsResponse(**create_response.json())

        with allure.step("POST /api/news/{news_id}/comments возвращает 200"):
            response = auth_client.post(
                NEWS_COMMENTS.format(news_id = news.id),
                json = comment_data,
                expected_status = 200,
            )

        with allure.step("Тело ответа соответствует модели CommentResponse"):
            comment = CommentResponse(**response.json())

        with allure.step("Поля комментария совпадают с отправленными"):
            assert comment.id > 0
            assert comment.text == comment_data["text"]
            assert comment.created_at is not None

        with allure.step("Автором комментария указан текущий пользователь"):
            assert comment.author.id == auth_client.user_id

    @allure.story("Получение комментариев")
    @allure.title("Позитивный тест. Получение списка комментариев к новости")
    @allure.description("Запрос комментариев новости из предусловия. Ожидается 200 и список")
    @pytest.mark.positive
    def test_get_comments_list(self, auth_client, news_data, comment_data) -> None:
        with allure.step("Создание новости и комментария к ней"):
            create_response = auth_client.post(NEWS, data = news_data, expected_status = 200)
            news = NewsResponse(**create_response.json())
            auth_client.post(
                NEWS_COMMENTS.format(news_id = news.id),
                json = comment_data,
                expected_status = 200,
            )

        with allure.step("GET /api/news/{news_id}/comments возвращает 200"):
            response = auth_client.get(
                NEWS_COMMENTS.format(news_id = news.id), expected_status = 200
            )

        with allure.step("Все элементы списка соответствует модели CommentResponse"):
            body = response.json()
            assert isinstance(body, list)
            comments = [CommentResponse(**item) for item in body]

        with allure.step("Созданный комментарий присутствует в списке"):
            assert len(comments) == 1
            assert comments[0].text == comment_data["text"]
            assert comments[0].author.id == auth_client.user_id

    @allure.story("Создание комментария")
    @allure.title("Негативный тест. Создание комментария без токена")
    @allure.description("После сброса авторизации комментарий не создаётся. Ожидается 401")
    @pytest.mark.negative
    def test_create_comment_without_token(self, auth_client, news_data, comment_data) -> None:
        with allure.step("Создание новости авторизованным пользователем"):
            create_response = auth_client.post(NEWS, data = news_data, expected_status = 200)
            news = NewsResponse(**create_response.json())

        with allure.step("Сброс авторизации"):
            auth_client.clear_token()

        with allure.step("POST комментария без авторизации возвращает 401"):
            response = auth_client.post(
                NEWS_COMMENTS.format(news_id = news.id),
                json = comment_data,
                expected_status = 401,
            )

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Создание комментария")
    @allure.title("Негативный тест. Создание комментария с некорректным токеном")
    @allure.description("Комментирование с невалидным Bearer-токеном. Ожидается 401")
    @pytest.mark.negative
    def test_create_comment_with_invalid_token(self, auth_client, news_data, comment_data) -> None:
        with allure.step("Создание новости"):
            create_response = auth_client.post(NEWS, data = news_data, expected_status = 200)
            news = NewsResponse(**create_response.json())

        with allure.step("Установка невалидного токена"):
            auth_client.set_token("invalid.token.value")

        with allure.step("POST комментария возвращает 401"):
            response = auth_client.post(
                NEWS_COMMENTS.format(news_id = news.id),
                json = comment_data,
                expected_status = 401,
            )

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Создание комментария")
    @allure.title("Негативный тест. Создание комментария к несуществующей новости")
    @allure.description("Комментирование новости с id=0. Ожидается 404")
    @pytest.mark.negative
    def test_create_comment_to_not_existing_news(self, auth_client, comment_data) -> None:
        with allure.step("POST комментария к новости id = 0 возвращает 404"):
            response = auth_client.post(
                NEWS_COMMENTS.format(news_id = 0),
                json = comment_data,
                expected_status = 404,
            )

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Создание комментария")
    @allure.title("Негативный тест. Создание комментария с некорректным ID новости")
    @allure.description("В пути передаётся строка вместо id. Ожидается 422 по параметру news_id")
    @pytest.mark.negative
    def test_create_comment_with_invalid_news_id(self, auth_client, comment_data) -> None:
        with allure.step("POST комментария к новости id=aaa возвращает 422"):
            response = auth_client.post(
                NEWS_COMMENTS.format(news_id = "aaa"),
                json = comment_data,
                expected_status = 422,
            )

        with allure.step("Ошибка валидации указывает на параметр news_id"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("news_id" in detail.loc for detail in error.detail)

    @allure.story("Создание комментария")
    @allure.title("Негативный тест. Создание комментария без обязательного поля text")
    @allure.description("Тело запроса пустое. Ожидается 422 по полю text")
    @pytest.mark.negative
    def test_create_comment_without_text(self, auth_client, news_data) -> None:
        with allure.step("Создание новости"):
            create_response = auth_client.post(NEWS, data=news_data, expected_status=200)
            news = NewsResponse(**create_response.json())

        with allure.step("POST комментария с пустым телом возвращает 422"):
            response = auth_client.post(
                NEWS_COMMENTS.format(news_id = news.id),
                json = {},
                expected_status = 422,
            )

        with allure.step("Ошибка валидации указывает на поле text"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("text" in detail.loc for detail in error.detail)

    @allure.story("Получение комментариев")
    @allure.title("Негативный тест. Получение комментариев с некорректным ID новости")
    @allure.description("В пути передаётся строка вместо id. Ожидается 422 по параметру news_id")
    @pytest.mark.negative
    def test_get_comments_with_invalid_news_id(self, api_client) -> None:
        with allure.step("GET /api/news/aaa/comments возвращает 422"):
            response = api_client.get(
                NEWS_COMMENTS.format(news_id = "aaa"), expected_status = 422
            )

        with allure.step("Ошибка валидации"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("news_id" in detail.loc for detail in error.detail)