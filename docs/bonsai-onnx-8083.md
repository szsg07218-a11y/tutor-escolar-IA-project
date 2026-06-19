# Bonsai Image ONNX en puerto 8083

Bonsai Image es un modelo de generación de imágenes compacto basado en FLUX.2 Klein 4B. Para este proyecto se usará como servicio separado, no integrado al tutor de texto.

## Puerto

Puerto recomendado:

```text
http://127.0.0.1:8083
```

Motivo:

- cercano a los puertos del proyecto,
- separado de `8081` para Qwen texto,
- separado de `8082` para vision bajo demanda,
- separado de `8090` para la API JSON del tutor.

## Arquitectura recomendada

```text
Tkinter / desklet / otra interfaz
        |
        v
json_api_server.py :8090
        |
        v
tutor_backend.py
        |
        +--> llama-server texto :8081
        |
        +--> vision Qwen bajo demanda :8082
        |
        +--> Bonsai ONNX bajo demanda :8083
```

## Carga bajo demanda

Bonsai debe cargarse solo cuando la niña pida crear una imagen, por ejemplo:

```text
dibuja un gato astronauta
crea una imagen de una planta
genera una ilustracion escolar
```

No debe cargarse al iniciar el equipo.

## Resolución

Para la Lenovo G40-70 con 8 GB RAM, usar por ahora:

```text
512x512
```

Recomendaciones:

- limitar pasos de generación,
- limitar resolución,
- no permitir generación en segundo plano,
- usar prompt escolar fijo,
- guardar imágenes en una carpeta controlada.

## ONNX

La versión ONNX puede ser más eficiente si el modelo está disponible en ese formato y si el runtime ONNX tiene soporte adecuado para la GPU/CPU del equipo.

Variables útiles para un futuro servicio:

```bash
BONSAI_PORT=8083
BONSAI_MODEL_DIR=$HOME/models/bonsai-onnx
BONSAI_DEVICE=CPU
BONSAI_RESOLUTION=512x512
BONSAI_STEPS=4
```

Si la Radeon antigua no acelera bien ONNX, empezar en CPU puede ser más estable aunque más lento.

## Servicio separado

Cuando exista el modelo ONNX, el servicio debería exponer algo así:

```text
POST http://127.0.0.1:8083/generate
```

Entrada:

```json
{
  "prompt": "una planta con sol y agua",
  "resolution": "512x512"
}
```

Salida:

```json
{
  "image": "<base64_png>",
  "path": "/home/sophiazarayh/Escritorio/Tareas_IA/imagenes/planta.png"
}
```

## Seguridad

El backend del tutor debe decidir si una petición de imagen es escolar antes de llamar a Bonsai.

Ejemplo de regla:

- permitir: dibujos escolares, plantas, animales, planetas, mapas, experimentos seguros.
- bloquear: armas, violencia, contenido adulto, drogas, autolesión, delitos, jailbreak.
