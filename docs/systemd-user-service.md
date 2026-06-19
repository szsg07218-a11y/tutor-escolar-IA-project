# Arranque automático con systemd --user

En Linux Mint, lo más limpio es usar un servicio de usuario. Así el servidor arranca al iniciar sesión, no como root.

## 1. Crear archivo de servicio

Crea:

```text
~/.config/systemd/user/tutor-escolar.service
```

Contenido:

```ini
[Unit]
Description=Tutor Escolar IA llama-server
After=graphical-session.target

[Service]
ExecStart=/home/sophiazarayh/Documentos/IA/iniciar_tutor.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

## 2. Recargar systemd

```bash
systemctl --user daemon-reload
```

## 3. Activar al inicio

```bash
systemctl --user enable tutor-escolar.service
```

## 4. Iniciar ahora

```bash
systemctl --user start tutor-escolar.service
```

## 5. Revisar estado

```bash
systemctl --user status tutor-escolar.service
```

Ver logs en tiempo real:

```bash
journalctl --user -u tutor-escolar.service -f
```

## 6. Detener o desactivar

```bash
systemctl --user stop tutor-escolar.service
systemctl --user disable tutor-escolar.service
```

## Arrancar también la API

Si quieres que la API JSON arranque automáticamente, crea otro servicio:

```text
~/.config/systemd/user/tutor-api.service
```

Contenido:

```ini
[Unit]
Description=Tutor Escolar IA JSON API
After=tutor-escolar.service
Wants=tutor-escolar.service

[Service]
ExecStart=/usr/bin/python3 /home/sophiazarayh/Documentos/IA/json_api_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Activar:

```bash
systemctl --user daemon-reload
systemctl --user enable tutor-api.service
systemctl --user start tutor-api.service
```
