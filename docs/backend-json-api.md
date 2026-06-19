# Backend JSON

El backend escolar acepta JSON para que pueda ser usado por el desklet de Cinnamon, Tkinter u otra interfaz.

## Entrada por stdin

Uso directo:

```bash
echo '{"texto": "Que es la fotosintesis?"}' | python3 ~/.local/share/cinnamon/desklets/tutor-escolar@mint/tutor_backend.py
```

Entrada:

```json
{
  "texto": "Que es la fotosintesis?"
}
```

Salida:

```json
{
  "respuesta": "La fotosintesis es..."
}
```

## API HTTP local

Inicia el servidor API:

```bash
python3 ~/Documentos/IA/json_api_server.py
```

Por defecto escucha en:

```text
http://127.0.0.1:8090
```

Endpoint:

```text
POST /ask
```

Entrada:

```json
{
  "texto": "Que es la fotosintesis?"
}
```

Salida:

```json
{
  "respuesta": "La fotosintesis es..."
}
```

Prueba con curl:

```bash
curl -s http://127.0.0.1:8090/health
curl -s -X POST http://127.0.0.1:8090/ask \
  -H "Content-Type: application/json" \
  -d '{"texto":"Que es la fotosintesis?"}'
```

## Campos soportados

```json
{
  "texto": "Que ves en esta imagen?",
  "imagen": "<base64_png>",
  "voz": false
}
```

Campos:

- `texto`: obligatorio para texto.
- `imagen`: opcional, PNG/JPG en base64. Activa el servidor vision con `mmproj` bajo demanda.
- `voz`: opcional. Si es `true`, intenta generar audio con Piper si está instalado.

## Seguridad

El backend filtra categorías antes de llamar al modelo:

- contenido adulto
- drogas y alcohol
- armas y explosivos
- autolesión
- violencia gráfica
- delitos
- jailbreak

También permite frases escolares como:

```text
muerte de las estrellas
muerte de los dinosaurios
extincion de los dinosaurios
ciclo de vida
```

## Matemáticas

Las matemáticas con números, operaciones o ecuaciones se resuelven en Python antes de llamar al modelo.

Ejemplo:

```json
{"texto":"Calcula x + 10 = 25"}
```

Respuesta esperada:

```json
{
  "respuesta": "[Math Engine]: La ecuacion es x + 10 = 25. Despejando x, el valor es x = 15. Compruebalo sustituyendo: (15) + 10 = 25."
}
```
