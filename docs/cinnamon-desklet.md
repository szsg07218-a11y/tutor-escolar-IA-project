# Desklet de Cinnamon

El desklet vive en:

```text
~/.local/share/cinnamon/desklets/tutor-escolar@mint/
```

Archivos:

```text
metadata.json
desklet.js
tutor_backend.py
```

## Activación manual

1. Abrir `Configuración del sistema`.
2. Ir a `Desklets`.
3. Buscar `Mi Tutor Escolar IA`.
4. Agregarlo al escritorio.
5. Moverlo a la posición deseada.

## Activación automática desde iniciar_tutor.sh

`iniciar_tutor.sh` ahora intenta activar el desklet con:

```bash
gsettings set org.cinnamon enabled-desklets ...
```

Variable:

```bash
AUTO_ENABLE_DESKLET=true
```

Valor por defecto:

```bash
AUTO_ENABLE_DESKLET=true
```

Para desactivar:

```bash
AUTO_ENABLE_DESKLET=false ./iniciar_tutor.sh
```

UUID del desklet:

```bash
DESKLET_UUID=tutor-escolar@mint
```

ID interno usado por Cinnamon:

```text
tutor-escolar@mint:0
```

## Ver desklets activados

```bash
gsettings get org.cinnamon enabled-desklets
```

Si está vacío, el desklet no aparecerá aunque los archivos existan.

## Lanzar Tkinter desde iniciar_tutor.sh

Opcional:

```bash
LAUNCH_CLIENT=tkinter ./iniciar_tutor.sh
```

Esto inicia el servidor de texto y luego abre `tutor_tkinter.py`.

## Diferencia entre desklet y Tkinter

- Desklet: nativo de Linux Mint Cinnamon, vive en el escritorio.
- Tkinter: ventana portable para Linux, Windows y macOS.
- Ambos usan el mismo backend JSON.
