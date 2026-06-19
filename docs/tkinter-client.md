# Cliente Tkinter

Tkinter es una buena opción para una interfaz ligera en Linux, Windows y macOS. Consume menos memoria que PyQt y no requiere empaquetado web como Tauri.

## Requisitos

Python 3 con Tkinter instalado.

En Linux Mint normalmente ya viene instalado. Si falta:

```bash
sudo apt install python3-tk
```

## Ejecutar

Primero inicia el servidor API:

```bash
python3 ~/Documentos/IA/json_api_server.py
```

En otra terminal:

```bash
python3 ~/Documentos/IA/tutor_tkinter.py
```

La ventana debe mostrar un estado inicial como `API: comprobando...`. Si aparece vacía, revisa que `python3-tk` esté instalado y que el servidor API esté corriendo antes de abrir Tkinter.

## Variables de entorno

```bash
TUTOR_API_URL=http://127.0.0.1:8090/ask python3 tutor_tkinter.py
```

## Diseño

La app Tkinter:

- muestra historial de conversación,
- envía JSON a `/ask`,
- no llama directamente a `llama-server`,
- funciona igual en escritorio, laptop u otro SO si el backend está disponible.

## Flujo

```text
Tkinter -> json_api_server.py -> tutor_backend.py -> llama-server texto
                                      |
                                      -> vision server bajo demanda si hay imagen
```
