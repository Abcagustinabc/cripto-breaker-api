# 🔓 Cripto Breaker API

Una API RESTful desarrollada en Python (FastAPI) que detecta y rompe automáticamente cifrados clásicos mediante heurísticas y análisis estadístico.

## 🚀 Demo en vivo
Puedes probar la API en funcionamiento aquí: 
👉 **[https://cripto-breaker-api.onrender.com/docs](https://cripto-breaker-api.onrender.com/docs)**

*(Nota: Al estar en el plan gratuito de Render, el servidor puede tardar hasta 50 segundos en despertar en la primera petición).*

## 🧠 ¿Qué cifrados rompe?

El algoritmo es capaz de detectar y descifrar automáticamente:
1. **César:** Fuerza bruta con scoring de frecuencia en español.
2. **Vigenère:** Análisis de Kasiski e Índice de Coincidencia.
3. **Sustitución Simple:** Hill climbing (búsqueda local) con mapeo de frecuencias.
4. **XOR:** Fuerza bruta para claves cortas y análisis heurístico de bytes.

## 🛠️ Tecnologías utilizadas
- **Python 3.12**
- **FastAPI** (Backend y documentación interactiva)
- **Uvicorn** (Servidor ASGI)
- **Render** (Despliegue en la nube)
- **Git / GitHub** (Control de versiones)

## 💻 Uso local

Si quieres correr este proyecto en tu propia computadora:

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Abcagustinabc/cripto-breaker-api.git