# Tutor Escolar IA - Documentación

Este proyecto usa una arquitectura local por capas:

1. `llama-server` de texto en `http://127.0.0.1:8081`.
2. Backend Python escolar en `~/.local/share/cinnamon/desklets/tutor-escolar@mint/tutor_backend.py`.
3. API JSON local en `http://127.0.0.1:8090/ask`.
4. Interfaz Tkinter opcional en `tutor_tkinter.py`.
5. Desklet de Cinnamon para Linux Mint.
6. Servicio separado de generación de imágenes Bonsai ONNX, previsto en `http://127.0.0.1:8083`.

Archivos principales:

- `iniciar_tutor.sh`: inicia Qwen3.5-0.8B con llama.cpp y Vulkan AMD. Puede activar el desklet con `AUTO_ENABLE_DESKLET=true` y lanzar Tkinter con `LAUNCH_CLIENT=tkinter`.
- `json_api_server.py`: expone el backend por HTTP para Tkinter u otra interfaz.
- `tutor_tkinter.py`: interfaz ligera multiplataforma.
- `docs/backend-json-api.md`: contrato JSON del backend.
- `docs/systemd-user-service.md`: arranque automático al iniciar sesión.
- `docs/cinnamon-desklet.md`: activación manual y automática del desklet.
- `docs/bonsai-onnx-8083.md`: plan para Bonsai Image ONNX en puerto 8083.
