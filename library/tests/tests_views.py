import json
import hashlib
import requests
from unittest.mock import patch, MagicMock

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from library.models import Entry

User = get_user_model()

class HealthEndpointTests(APITestCase):
    def test_health(self):
        response = self.client.get("/api/health/")

        # Código HTTP correcto
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # JSON esperado
        expected = {"status": "ok"}
        self.assertEqual(response.json(), expected)

        # Clave presente
        self.assertIn("status", response.json())

        # Valor correcto
        self.assertEqual(response.json()["status"], "ok")

        # No debe contener claves inesperadas
        self.assertNotIn("paco", response.json())

class LibraryEntriesListTests(APITestCase):
    url = "/api/library/entries/"

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="pablo",
            password="password_segura_123"
        )
        self.user2 = User.objects.create_user(
            username="ana",
            password="password_segura_456"
        )

        # Entradas de user1
        Entry.objects.create(external_id="1", title="Entrada 1", content="...", owner=self.user1)
        Entry.objects.create(external_id="2", title="Entrada 2", content="...", owner=self.user1)

        # Entradas de user2
        Entry.objects.create(external_id="A", title="Entrada A", content="...", owner=self.user2)

    def test_list_without_auth(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertTrue(response.data.get("detail"))

    def test_list_with_auth(self):
        self.client.force_login(self.user1)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # solo las suyas

    def test_list_two_users_isolated(self):
        # User1
        self.client.login(username="pablo", password="password_segura_123")
        response1 = self.client.get(self.url)
        self.assertEqual(len(response1.data), 2)
        self.client.logout()

        # User2
        self.client.login(username="ana", password="password_segura_456")
        response2 = self.client.get(self.url)
        self.assertEqual(len(response2.data), 1)

class LibraryEntryDetailTests(APITestCase):
    def setUp(self):
        # Usuarios
        self.user1 = User.objects.create_user(
            username="pablo",
            password="password_segura_123"
        )
        self.user2 = User.objects.create_user(
            username="ana",
            password="password_segura_456"
        )

        # Entradas
        self.entry_user1 = Entry.objects.create(
            title="Entrada de Pablo",
            content="Contenido",
            owner=self.user1
        )

        self.entry_user2 = Entry.objects.create(
            title="Entrada de Ana",
            content="Contenido",
            owner=self.user2
        )

    def test_detail_without_auth(self):
        url = f"/api/library/entries/{self.entry_user1.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_with_auth_own_entry(self):
        self.client.force_login(self.user1)

        url = f"/api/library/entries/{self.entry_user1.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.entry_user1.id)

    def test_detail_with_auth_other_user_entry(self):
        self.client.force_login(self.user1)

        url = f"/api/library/entries/{self.entry_user2.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "not_found")

class LibraryEntryCreateTests(APITestCase):
    url = "/api/library/entries/"

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="pablo",
            password="password_segura_123"
        )
        self.user2 = User.objects.create_user(
            username="ana",
            password="password_segura_456"
        )

    def test_create_without_auth(self):
        data = {
            "external_id": "123"
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_with_auth(self):
        self.client.force_login(self.user1)

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = [{"title": "Test Game", "shortDescription": "Descripción"}]

        data = {
            "external_id": "123",
            "hours_played": 10,
            "notes": "Notas de prueba"
        }

        with patch('library.views.requests.get', return_value=fake_response):
            response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["external_id"], "123")
        self.assertEqual(response.data["hours_played"], 10)

        # Verificar que realmente se creó en la BD
        self.assertEqual(Entry.objects.filter(owner=self.user1).count(), 1)

    def test_isolation_between_users(self):
        fake_response1 = MagicMock()
        fake_response1.status_code = 200
        fake_response1.json.return_value = [{"title": "Entrada Pablo", "shortDescription": "Contenido"}]

        fake_response2 = MagicMock()
        fake_response2.status_code = 200
        fake_response2.json.return_value = [{"title": "Entrada Ana", "shortDescription": "Contenido"}]

        # User1 crea una entrada
        self.client.force_login(self.user1)
        with patch('library.views.requests.get', return_value=fake_response1):
            self.client.post(self.url, {"external_id": "pablo", "hours_played": 5}, format="json")
        self.client.logout()

        # User2 crea otra entrada
        self.client.force_login(self.user2)
        with patch('library.views.requests.get', return_value=fake_response2):
            self.client.post(self.url, {"external_id": "A-123", "hours_played": 2}, format="json")

        # Listado de user2 → solo debe ver su entrada
        response = self.client.get("/api/library/entries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["external_id"], "A-123")

class CatalogSearchTests(APITestCase):
    url = "/api/catalog/search/"

    def test_search_query_returns_list(self):
        sample_response = [
            {
                "gameID": "123",
                "external": "Test Game",
                "thumb": "https://example.com/thumb.jpg",
            }
        ]

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = sample_response

        with patch('library.catalog_service.requests.get', return_value=fake_response):
            response = self.client.get(self.url, {"q": "mario"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(response.json(), [
            {
                "external_game_id": "123",
                "title": "Test Game",
                "thumb": "https://example.com/thumb.jpg",
            }
        ])

    def test_search_empty_q_returns_validation_error(self):
        response = self.client.get(self.url, {"q": ""})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"error": "validation_error", "message": "El parámetro 'q' es obligatorio y no puede estar vacío"})

    def test_search_missing_q_returns_validation_error(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"error": "validation_error", "message": "El parámetro 'q' es obligatorio y no puede estar vacío"})

    def test_search_results_are_cached(self):
        sample_response = [
            {
                "gameID": "123",
                "external": "Test Game",
                "thumb": "https://example.com/thumb.jpg",
            }
        ]

        expected_results = [
            {
                "external_game_id": "123",
                "title": "Test Game",
                "thumb": "https://example.com/thumb.jpg",
            }
        ]

        cache_key = "catalog_search:" + hashlib.sha256("mario".encode("utf-8")).hexdigest()

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = sample_response

        with patch('library.catalog_service.cache') as fake_cache, patch('library.catalog_service.requests.get', return_value=fake_response) as fake_requests_get:
            fake_cache.get.return_value = None
            response = self.client.get(self.url, {"q": "mario"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), expected_results)
            fake_cache.set.assert_called_once_with(cache_key, expected_results, timeout=300)
            fake_requests_get.assert_called_once()

        with patch('library.catalog_service.cache') as fake_cache, patch('library.catalog_service.requests.get') as fake_requests_get:
            fake_cache.get.return_value = expected_results
            response = self.client.get(self.url, {"q": "mario"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), expected_results)
            fake_requests_get.assert_not_called()

    def test_search_falls_back_to_cache_when_provider_unavailable(self):
        expected_results = [
            {
                "external_game_id": "123",
                "title": "Test Game",
                "thumb": "https://example.com/thumb.jpg",
            }
        ]

        with patch('library.catalog_service.cache') as fake_cache, patch('library.catalog_service.requests.get', side_effect=requests.exceptions.RequestException):
            fake_cache.get.return_value = expected_results
            response = self.client.get(self.url, {"q": "mario"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), expected_results)

    def test_search_returns_503_when_provider_unavailable_and_no_cache(self):
        with patch('library.catalog_service.cache') as fake_cache, patch('library.catalog_service.requests.get', side_effect=requests.exceptions.RequestException):
            fake_cache.get.return_value = None
            response = self.client.get(self.url, {"q": "mario"})

            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertEqual(response.json(), {
                "error": "external_service_unavailable",
                "message": "El catálogo externo no está disponible. Inténtalo más tarde."
            })

    def test_search_returns_502_when_provider_returns_error_and_no_cache(self):
        fake_response = MagicMock()
        fake_response.status_code = 500
        fake_response.json.return_value = {}

        with patch('library.catalog_service.cache') as fake_cache, patch('library.catalog_service.requests.get', return_value=fake_response):
            fake_cache.get.return_value = None
            response = self.client.get(self.url, {"q": "mario"})

            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
            self.assertEqual(response.json(), {
                "error": "external_service_error",
                "message": "Error al consultar el catálogo externo."
            })
