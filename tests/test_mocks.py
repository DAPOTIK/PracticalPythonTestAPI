from unittest.mock import Mock, patch
import allure
import pytest



@allure.feature("Новости")
class TestNewsMocks:

    @allure.story("Получение списка новостей")
    @allure.title("Негативный тест. Ошибка сервера при получении ленты")
    @allure.description("сервер стабилен и 5xx не воспроизводится. Ответ 500 подменён заглушкой, проверяется наличие сообщения об ошибке.")
    @pytest.mark.negative
    @pytest.mark.negative
    def test_news_feed_server_error(self, api_client):
        with allure.step("Мок с ответом 500"):
            mock_response = Mock(status_code = 500)
            mock_response.text = '{"detail": "Internal Server Error"}'
            mock_response.json.return_value = {"detail": "Internal Server Error"}

        with allure.step("GET /api/news/ возвращает 500"):
            with patch.object(api_client.session, "request", return_value = mock_response):
                response = api_client.get("/api/news/", expected_status=500)

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            assert response.json()["detail"]