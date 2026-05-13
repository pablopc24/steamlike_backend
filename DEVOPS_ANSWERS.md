# Respuestas Ejercicios DevOps (Semana 7)

## Ejercicio 1: Revisión del Pipeline
*   **Flujo actual:** El pipeline se dispara ante `push` en ramas principales. Realiza el checkout del código, configura Python 3.11, instala dependencias de `requirements.txt` y ejecuta los tests unitarios de Django.
*   **Punto de ejecución de tests:** Step "Run backend tests" (ahora actualizado a "Run backend tests with coverage").
*   **Estado correcto:** Se verifica mediante el código de salida del comando de tests. Si hay fallos, el pipeline se detiene.
*   **Momento del despliegue:** El despliegue debe ocurrir justo después de pasar los tests. Se ha implementado como un job `deploy` que depende de `test`.

## Ejercicio 2 & 3: Despliegue Automático y Control de Estado
*   **Relación CI y Despliegue:** El despliegue está condicionado al éxito del CI (`needs: test`). Si los tests fallan, el job `deploy` no se ejecuta, evitando subir código defectuoso a producción.
*   **Render Hook:** Se utiliza el "Deploy Hook" de Render para notificar al servicio que debe realizar un nuevo despliegue.

## Ejercicio 4: Métricas de Calidad (Coverage)
Se ha integrado `coverage` en el pipeline.
*   **Fragmento del workflow:**
    ```yaml
    - name: Run backend tests with coverage
      run: |
        coverage run manage.py test
        coverage report
    ```
*   Esto genera un informe detallado en los logs de GitHub Actions mostrando el porcentaje de líneas cubiertas por los tests.

## Ejercicio 5: Verificación de Migraciones
Se ha añadido un paso previo a los tests para asegurar que no hay cambios en los modelos sin su correspondiente migración.
*   **Fragmento del workflow:**
    ```yaml
    - name: Check for pending migrations
      run: python manage.py makemigrations --check --dry-run
    ```
*   **Importancia:** Evita errores en producción donde la base de datos y el código podrían estar desincronizados, lo cual causaría errores de ejecución inmediatos.

## Ejercicio 6: Conclusiones
*   **¿Qué ocurre tras un commit?** Se dispara el workflow de GitHub. Primero se instalan dependencias, se comprueban migraciones y se corren tests con cobertura. Si todo es correcto (verde), se lanza una petición POST al hook de Render, que inicia la construcción y despliegue de la nueva versión.
*   **Errores detectados:** Código que rompe funcionalidades existentes (tests), falta de migraciones necesarias, y baja calidad/cobertura si se pusieran umbrales.
*   **Ventajas:** Mayor confianza en el despliegue, eliminación de errores humanos en el proceso manual, y ciclos de entrega mucho más rápidos y seguros.
