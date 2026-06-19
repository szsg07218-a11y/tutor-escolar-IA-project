# Plan: Bonsai Image en puerto 8083

## Objetivo

Implementar una sección opcional de generación de imágenes con Bonsai Image, separada del tutor de texto, expuesta como servicio local en `http://127.0.0.1:8083` y llamada desde el backend JSON del tutor solo cuando la petición sea escolar y segura.

## Contexto actual

- El tutor de texto usa `llama-server` en `8081`.
- Vision usa `8082` bajo demanda con `mmproj`.
- La API JSON del tutor usa `8090`.
- El desklet y Tkinter consumen la API JSON.
- La idea acordada es mantener Bonsai separado y no cargarlo al iniciar el equipo.

## Hallazgos relevantes

- `onnx-community/Bonsai-4B-ONNX` existe en Hugging Face, pero el modelo reportado es `Qwen3ForCausalLM`; no parece ser una pipeline completa de generación de imágenes lista para usar.
- La documentación de OxiBonsai describe una pipeline completa Bonsai Image: `Text Encoder Qwen3-4B -> DiT FLUX.2-Klein ternary -> VAE AutoencoderKLFlux2 -> PNG`.
- OxiBonsai tiene soporte GPU para Metal y CUDA, pero no parece tener backend Vulkan para la Radeon AMD de la Lenovo G40-70.
- `stable-diffusion.cpp` soporta modelos de difusión, GGUF, safetensors, Vulkan y modelos FLUX.2-Klein/Qwen Image; por eso parece la ruta más práctica para AMD Vulkan.
- No hay modelos Bonsai descargados localmente en `~/models`.

## Recomendación de implementación

### Ruta recomendada: `stable-diffusion.cpp` con Vulkan

Esta ruta aprovecha el mismo enfoque local y ligero del proyecto, mantiene la GPU AMD mediante Vulkan y evita depender de una pipeline ONNX incompleta.

Servicio:

```text
POST http://127.0.0.1:8083/generate
```

Entrada:

```json
{
  "prompt": "una planta con sol y agua",
  "resolution": "512x512",
  "steps": 4,
  "seed": 42
}
```

Salida:

```json
{
  "ok": true,
  "path": "/home/sophiazarayh/Escritorio/Tareas_IA/imagenes/planta.png",
  "base64": "<png_base64>"
}
```

Modelos necesarios:

```text
1. Bonsai Image diffusion model en GGUF.
2. Qwen3-4B text encoder en GGUF.
3. FLUX.2 VAE en safetensors.
```

Parámetros conservadores para la Lenovo G40-70 con 8 GB RAM:

```text
resolution: 512x512
steps: 2-4
offload-to-cpu: true
VAE tiling: true
```

### Ruta alternativa: OxiBonsai

Ventajas:

- pipeline Bonsai Image más explícita y documentada,
- genera PNG,
- modelos Bonsai bien definidos.

Desventajas:

- no parece soportar Vulkan/AMD,
- requiere Rust/cargo,
- probablemente correría en CPU en esta máquina,
- puede ser demasiado lento para la experiencia de escritorio.

### Ruta ONNX pura

No recomendada por ahora.

Motivo:

- el repositorio ONNX encontrado parece contener un modelo Qwen3 causal LM, no una pipeline completa de imagen.
- ONNX Runtime con aceleración Vulkan para esta pipeline no está claro.
- Con 8 GB RAM, una implementación Python/ONNX puede ser más frágil y difícil de mantener.

## Diseño de archivos propuestos

Nuevos archivos:

```text
bonsai_image_service.py
bonsai_image_client.py
docs/bonsai-image-8083.md
```

Opcional si se usa `stable-diffusion.cpp`:

```text
iniciar_bonsai.sh
```

Configuración por variables de entorno:

```bash
BONSAI_PORT=8083
BONSAI_MODEL_DIR=$HOME/models/bonsai-image
BONSAI_DIFFUSION_MODEL=$HOME/models/bonsai-image/bonsai-image.gguf
BONSAI_TEXT_ENCODER=$HOME/models/bonsai-image/qwen3-4b.gguf
BONSAI_VAE=$HOME/models/bonsai-image/flux2-vae.safetensors
BONSAI_OUTPUT_DIR=$HOME/Escritorio/Tareas_IA/imagenes
BONSAI_RESOLUTION=512x512
BONSAI_STEPS=4
BONSAI_DEVICE=vulkan
```

## Integración con el backend actual

### 1. Backend del tutor

Agregar en `tutor_backend.py`:

- detección de intención de imagen:
  - `dibuja`
  - `crea una imagen`
  - `genera una ilustracion`
  - `haz un dibujo`
- validación escolar/segura antes de llamar a Bonsai.
- llamada HTTP a `8083/generate`.
- respuesta al usuario con ruta de la imagen.
- manejo de errores si Bonsai no está instalado o no está corriendo.

Ejemplo de respuesta:

```text
Listo, cree la imagen en: /home/sophiazarayh/Escritorio/Tareas_IA/imagenes/planta.png
```

### 2. API JSON

Ampliar `json_api_server.py` con:

```text
POST /ask
```

si el backend devuelve una imagen, incluir:

```json
{
  "respuesta": "...",
  "imagen": "/ruta/de/salida.png",
  "imagen_base64": "<opcional>"
}
```

También se puede agregar:

```text
POST /generate-image
```

para interfaces que quieran llamar directamente a Bonsai.

### 3. Tkinter

Agregar botón o comando:

```text
Crear imagen
```

Comportamiento:

- si el backend devuelve `imagen`, mostrar miniatura.
- si falla Bonsai, mostrar mensaje amigable.
- no bloquear la interfaz durante la generación.

### 4. Desklet

Para escritorio, evitar mostrar imágenes grandes dentro del desklet. Mejor:

- mostrar texto: `Imagen creada: planta.png`
- abrir archivo con `gio open` o `xdg-open` si se desea.

### 5. Script de inicio

Agregar variable:

```bash
RUN_BONSAI=false
```

Uso:

```bash
RUN_BONSAI=true ./iniciar_tutor.sh
```

O separado:

```bash
./iniciar_bonsai.sh
```

Separado es preferible porque Bonsai debe cargar bajo demanda y no al iniciar sesión.

## Plan de implementación por fases

### Fase 1: decidir runtime

Confirmar con el usuario si acepta usar `stable-diffusion.cpp` en lugar de ONNX puro.

Justificación:

- mejor soporte para AMD Radeon mediante Vulkan,
- menos fricción que una pipeline ONNX incompleta,
- mantiene el proyecto local y portable.

### Fase 2: preparar modelos

Buscar o descargar:

```text
Bonsai Image GGUF
Qwen3-4B GGUF
FLUX.2 VAE safetensors
```

Guardar en:

```text
~/models/bonsai-image/
```

No descargar nada sin confirmación del usuario porque son varios GB.

### Fase 3: crear servicio 8083

Implementar `bonsai_image_service.py` como servicio HTTP local.

Endpoints:

```text
GET  /health
POST /generate
```

El servicio debe:

- validar prompt,
- limitar resolución y pasos,
- llamar al motor de imagen,
- guardar PNG,
- devolver JSON con ruta y base64 opcional.

### Fase 4: integrar backend del tutor

Agregar en `tutor_backend.py`:

- detección de intención,
- seguridad,
- llamada a Bonsai,
- respuesta de éxito/error.

### Fase 5: actualizar API JSON

Permitir que `/ask` devuelva imagen cuando el backend la genere.

### Fase 6: actualizar Tkinter

Mostrar imagen generada o mensaje de error.

### Fase 7: documentación

Actualizar:

```text
docs/index.md
docs/bonsai-onnx-8083.md
docs/bonsai-image-8083.md
```

Documentar:

- instalación de modelos,
- variables de entorno,
- comando para iniciar Bonsai,
- límites de seguridad,
- diferencia entre ONNX y ruta recomendada con Vulkan.

## Riesgos y mitigaciones

### Riesgo: 8 GB RAM no son suficientes

Mitigación:

- 512x512,
- 2-4 pasos,
- `offload-to-cpu`,
- VAE tiling,
- no cargar Bonsai al inicio.

### Riesgo: Radeon antigua no acelera Bonsai

Mitigación:

- probar primero con Vulkan,
- si falla, usar CPU con límites estrictos,
- informar al usuario que puede tardar varios minutos.

### Riesgo: modelos Bonsai no están disponibles en formato conveniente

Mitigación:

- usar GGUF + VAE safetensors con `stable-diffusion.cpp`,
- evitar ONNX puro hasta tener una pipeline completa verificable.

### Riesgo: contenido no escolar

Mitigación:

- mantener seguridad en `tutor_backend.py`,
- permitir solo prompts escolares,
- rechazar violencia, armas, contenido adulto, drogas, autolesión, delitos y jailbreak.

## Pregunta pendiente para el usuario

¿Quieres que implementemos Bonsai usando `stable-diffusion.cpp` con Vulkan para la Radeon AMD, aunque no sea ONNX puro, o prefieres intentar primero una ruta ONNX aunque sea más incierta en esta máquina?
