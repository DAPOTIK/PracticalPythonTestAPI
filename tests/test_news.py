import allure
import pytest
from constants import NEWS, NEWS_BY_ID, NEWS_TAGS
from models import ErrorResponse, HTTPValidationError, NewsListResponse, NewsResponse, TagResponse


@allure.feature("Новости")
class TestNews:

    @allure.story("Создание новости")
    @allure.title("Позитивный тест. Создание новости без изображения")
    @allure.description("Создание новости с валидными полями без файла картинки. Ожидается 200 и пустой image_path")
    @pytest.mark.positive
    def test_create_news_without_image(self, auth_client, news_data) -> None:
        with allure.step("POST /api/news/ без файла возвращает 200"):
            response = auth_client.post(NEWS, data = news_data, expected_status = 200)

        with allure.step("Тело ответа соответствует модели NewsResponse"):
            news = NewsResponse(**response.json())

        with allure.step("Поля новости совпадают с отправленными"):
            assert news.id > 0
            assert news.title == news_data["title"]
            assert news.subtitle == news_data["subtitle"]
            assert news.text == news_data["text"]
            assert news.author.id == auth_client.user_id
            assert news.comments_count == 0

        with allure.step("Путь к изображению не заполнен"):
            assert news.image_path is None

    @allure.story("Создание новости")
    @allure.title("Позитивный тест. Создание новости с изображением")
    @allure.description("Создание новости с приложенным png. Ожидается 200 и заполненный image_path")
    @pytest.mark.positive
    def test_create_news_with_image(self, auth_client, news_data, image_file) -> None:
        with allure.step("POST /api/news/ с файлом png возвращает 200"):
            response = auth_client.post(
                NEWS,
                data = news_data,
                files = {"image": image_file},
                expected_status = 200,
            )

        with allure.step("Тело ответа соответствует модели NewsResponse"):
            news = NewsResponse(**response.json())

        with allure.step("Поля новости совпадают с отправленными"):
            assert news.id > 0
            assert news.title == news_data["title"]
            assert news.text == news_data["text"]

        with allure.step("Путь к загруженному изображению заполнен"):
            assert news.image_path is not None
            assert news.image_path.endswith(".png")

    @allure.story("Получение списка новостей")
    @allure.title("Позитивный тест. Получение списка всех новостей")
    @allure.description("Запрос ленты без параметров. Ожидается 200")
    @pytest.mark.positive
    @pytest.mark.smoke
    def test_get_news_list(self, auth_client, news_data) -> None:
        with allure.step("Создание новости"):
            auth_client.post(NEWS, data = news_data, expected_status = 200)

        with allure.step("GET /api/news/ возвращает 200"):
            response = auth_client.get(NEWS, expected_status = 200)

        with allure.step("Тело ответа соответствует модели NewsListResponse"):
            news_list = NewsListResponse(**response.json())

        with allure.step("Лента не пуста и счётчики пагинации заполнены"):
            assert news_list.total > 0
            assert news_list.page > 0
            assert news_list.per_page > 0
            assert news_list.total_pages > 0
            assert len(news_list.items) > 0

    @allure.story("Получение списка новостей")
    @allure.title("Позитивный тест. Получение новостей с фильтрами page и per_page")
    @allure.description("Запрос ленты с page = 1 и per_page = 1. Ожидается страница ровно из одной новости")
    @pytest.mark.positive
    def test_get_news_with_pagination(self, auth_client, news_data) -> None:
        with allure.step("Создание новости"):
            auth_client.post(NEWS, data = news_data, expected_status = 200)

        with allure.step("GET /api/news/ с page=1 и per_page=1 возвращает 200"):
            response = auth_client.get(
                NEWS, params={"page": 1, "per_page": 1}, expected_status = 200
            )

        with allure.step("Тело ответа соответствует модели NewsListResponse"):
            page = NewsListResponse(**response.json())

        with allure.step("Параметры пагинации применены к выдаче"):
            assert page.page == 1
            assert page.per_page == 1
            assert len(page.items) == 1
            assert page.total_pages == page.total

    @allure.story("Получение списка новостей")
    @allure.title("Позитивный тест. Получение новостей с фильтром tag")
    @allure.description("Запрос ленты с фильтром по одному из тегов созданной новости")
    @pytest.mark.positive
    def test_get_news_with_tag_filter(self, auth_client, news_data) -> None:
        with allure.step("Создание новости с тремя тегами"):
            auth_client.post(NEWS, data = news_data, expected_status = 200)
            tag = news_data["tags"].split(", ")[0]

        with allure.step(f"GET /api/news/ с фильтром tag = {tag} возвращает 200"):
            response = auth_client.get(NEWS, params = {"tag": tag}, expected_status = 200)

        with allure.step("Тело ответа соответствует модели NewsListResponse"):
            by_tag = NewsListResponse(**response.json())

        with allure.step("Выдача не пуста и содержит только новости с указанным тегом"):
            assert len(by_tag.items) > 0
            for item in by_tag.items:
                assert tag in [tag_item.name for tag_item in item.tags]

    @allure.story("Получение списка новостей")
    @allure.title("Позитивный тест. Получение новостей с фильтром")
    @allure.description("Запрос ленты с поиском по заголовку созданной новости")
    @pytest.mark.positive
    def test_get_news_with_search_filter(self, auth_client, news_data) -> None:
        with allure.step("Создание новости"):
            auth_client.post(NEWS, data = news_data, expected_status = 200)

        with allure.step("GET /api/news/ с фильтром search возвращает 200"):
            response = auth_client.get(
                NEWS, params = {"search": news_data["title"]}, expected_status = 200
            )

        with allure.step("Тело ответа соответствует модели NewsListResponse"):
            by_search = NewsListResponse(**response.json())

        with allure.step("Новость найдена по заголовку"):
            assert len(by_search.items) > 0
            assert news_data["title"] in [item.title for item in by_search.items]

    @allure.story("Получение новости по ID")
    @allure.title("Позитивный. Получение детальной информации о новости по ID")
    @allure.description("Запрос созданной новости по её id. Ожидается 200")
    @pytest.mark.positive
    def test_get_news_by_id(self, auth_client, news_data) -> None:
        with allure.step("Создание новости"):
            create_response = auth_client.post(NEWS, data = news_data, expected_status = 200)
            created = NewsResponse(**create_response.json())

        with allure.step("GET /api/news/{news_id} возвращает 200"):
            response = auth_client.get(NEWS_BY_ID.format(news_id = created.id), expected_status = 200)

        with allure.step("Тело ответа соответствует модели NewsResponse"):
            news = NewsResponse(**response.json())

        with allure.step("Данные новости совпадают с созданной"):
            assert news.id == created.id
            assert news.title == news_data["title"]
            assert news.subtitle == news_data["subtitle"]
            assert news.text == news_data["text"]
            assert news.author.id == auth_client.user_id

    @allure.story("Теги")
    @allure.title("Позитивный тест. Получение списка всех тегов")
    @allure.description("Запрос справочника тегов. Ожидается 200 и список объектов TagResponse")
    @pytest.mark.positive
    def test_get_tags(self, auth_client, news_data) -> None:
        with allure.step("Создание новости с тегами"):
            auth_client.post(NEWS, data = news_data, expected_status = 200)

        with allure.step("GET /api/news/tags возвращает 200"):
            response = auth_client.get(NEWS_TAGS, expected_status = 200)

        with allure.step("Каждый элемент списка соответствует модели TagResponse"):
            body = response.json()
            assert isinstance(body, list)
            tags = [TagResponse(**item) for item in body]

        with allure.step("Список тегов не пуст"):
            assert len(tags) > 0
            assert all(tag.id > 0 for tag in tags)

    @allure.story("Создание новости")
    @allure.title("Негативный. Создание новости без токена")
    @allure.description("Создание новости неавторизованным клиентом. Ожидается 401.")
    @pytest.mark.negative
    def test_create_news_without_token(self, api_client, news_data) -> None:
        with allure.step("POST /api/news/ без авторизации возвращает 401"):
            response = api_client.post(NEWS, data =  news_data, expected_status = 401)

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Создание новости")
    @allure.title("Негативный тест. Создание новости с некорректным токеном")
    @allure.description("Создание новости с невалидным Bearer-токеном. Ожидается 401")
    @pytest.mark.negative
    def test_create_news_with_invalid_token(self, api_client, news_data) -> None:
        with allure.step("Невалидный токена"):
            api_client.set_token("invalid.token.value")

        with allure.step("POST /api/news/ возвращает 401"):
            response = api_client.post(NEWS, data = news_data, expected_status = 401)

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Получение новости по ID")
    @allure.title("Негативный тест. Получение новости по несуществующему ID")
    @allure.description("Запрос новости с id=0. Ожидается 404.")
    @pytest.mark.negative
    def test_get_news_by_not_existing_id(self, api_client) -> None:
        with allure.step("GET /api/news/0 возвращает 404"):
            response = api_client.get(NEWS_BY_ID.format(news_id = 0), expected_status = 404)

        with allure.step("Тело ответа содержит сообщение об ошибке"):
            error = ErrorResponse(**response.json())
            assert error.detail

    @allure.story("Получение новости по ID")
    @allure.title("Негативный тест. Получение новости по некорректному ID")
    @allure.description("Запрос новости со строкой вместо id. Ожидается 422 по параметру news_id")
    @pytest.mark.negative
    def test_get_news_by_invalid_id(self, api_client) -> None:
        with allure.step("GET /api/news/aaa возвращает 422"):
            response = api_client.get(NEWS_BY_ID.format(news_id = "aaa"), expected_status = 422)

        with allure.step("Ошибка валидации указывает на параметр news_id"):
            error = HTTPValidationError(**response.json())
            assert error.detail
            assert any("news_id" in detail.loc for detail in error.detail)

    @allure.story("Получение списка новостей")
    @allure.title("Негативный тест. Список новостей с некорректной пагинацией")
    @allure.description("Запрос ленты с параметрами вне допустимого диапазона. Ожидается 422")
    @pytest.mark.negative
    @pytest.mark.parametrize( "params", [{"page": 0}, {"page": -1}, {"per_page": 0}, {"page": "abc"}],
        ids=["page=0", "page=-1", "per_page=0", "page=abc"],
    )
    def test_get_news_with_invalid_pagination(self, api_client, params) -> None:
        with allure.step(f"GET /api/news/ с параметрами {params} возвращает 422"):
            response = api_client.get(NEWS, params = params, expected_status = 422)

        with allure.step("Тело ответа содержит ошибку валидации"):
            error = HTTPValidationError(**response.json())
            assert error.detail