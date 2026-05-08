#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'steamlike_backend.settings')
django.setup()

User = get_user_model()

def test_full_flow():
    client = Client()

    print("=== Paso 1: Buscar juegos en el catálogo ===")
    response = client.get('/api/catalog/search/', {'q': 'mario'})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Resultados encontrados: {len(data)}")
        if data:
            first_game = data[0]
            print(f"Primer juego: {first_game['title']} (ID: {first_game['external_game_id']})")
            game_id = first_game['external_game_id']
        else:
            print("No se encontraron juegos")
            return
    else:
        print(f"Error: {response.json()}")
        return

    print("\n=== Paso 2: Crear usuario y añadir juego a biblioteca ===")
    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("Usuario creado")
    else:
        print("Usuario ya existía")

    # Forzar login en el cliente de Django
    client.force_login(user)
    print("Usuario autenticado en cliente")

    # Añadir a biblioteca
    import json
    add_response = client.post('/api/library/entries/', 
                              json.dumps({
                                  'external_id': str(game_id) + '_test',  # Añadir sufijo para evitar duplicados
                                  'hours_played': 5,
                                  'notes': 'Test game'
                              }), 
                              content_type='application/json')
    print(f"Add to library status: {add_response.status_code}")
    if add_response.status_code == 201:
        print("Juego añadido a biblioteca")
    else:
        print(f"Error añadiendo: {add_response.json()}")

    print("\n=== Paso 3: Limpiar caché y repetir búsqueda (debería usar fallback) ===")
    from django.core.cache import cache
    cache.clear()
    print("Caché limpiado")
    
    response2 = client.get('/api/catalog/search/', {'q': 'mario'})
    print(f"Status: {response2.status_code}")
    print(f"Resultados: {len(response2.json())}")

    print("\n=== Flujo completado ===")

if __name__ == '__main__':
    test_full_flow()