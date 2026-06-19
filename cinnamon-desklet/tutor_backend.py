#!/usr/bin/env python3
import sys
import json
import os
import re
import time
import signal
import base64
import logging
import tempfile
import subprocess
import unicodedata
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

from openai import OpenAI
from duckduckgo_search import DDGS
from pypdf import PdfReader
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)
import sympy


def path_from_env(name, default):
    value = os.getenv(name)
    return Path(value).expanduser() if value else Path(default).expanduser()


logging.basicConfig(
    filename=os.path.expanduser("~/.config/tutor_logs.txt"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

CONFIG = {
    "text_url": os.getenv("TUTOR_TEXT_URL", "http://127.0.0.1:8081/v1"),
    "vision_url": os.getenv("TUTOR_VISION_URL", "http://127.0.0.1:8082/v1"),
    "model": os.getenv("TUTOR_MODEL", "qwen3.5-0.8b"),
    "llama_dir": path_from_env("TUTOR_LLAMA_DIR", "~/Documentos/IA/llama-vulkan-bin/llama-b9620"),
    "model_path": path_from_env("TUTOR_MODEL_PATH", "~/models/Qwen3.5-0.8B-Q4_K_M.gguf"),
    "mmproj_path": path_from_env("TUTOR_MMPROJ_PATH", "~/models/qwen35-mmproj-BF16.gguf"),
    "vision_port": int(os.getenv("TUTOR_VISION_PORT", "8082")),
    "vulkan_device": os.getenv("TUTOR_VULKAN_DEVICE", "Vulkan0"),
    "ngpu_layers": os.getenv("TUTOR_NGPU_LAYERS", "99"),
    "ctx_size": os.getenv("TUTOR_CTX_SIZE", "1024"),
    "fit_target": os.getenv("TUTOR_FIT_TARGET", "256"),
    "vision_start_timeout": int(os.getenv("TUTOR_VISION_START_TIMEOUT", "180")),
    "openai_timeout": int(os.getenv("TUTOR_OPENAI_TIMEOUT", "180")),
}

client = OpenAI(base_url=CONFIG["text_url"], api_key="local", timeout=CONFIG["openai_timeout"])
vision_client = None
vision_process = None
vision_log_handle = None

PIPER_BIN = os.path.expanduser("~/piper-tts/piper/piper")
PIPER_VOICE = os.path.expanduser("~/piper-tts/voices/es_ES-davefx-medium.onnx")
WHISPER_MODEL = "tiny"

CARPETA_ESCOLAR = os.path.expanduser("~/Escritorio/Tareas_IA")
os.makedirs(CARPETA_ESCOLAR, exist_ok=True)

CATEGORIAS_PROHIBIDAS = {
    "contenido adulto": ["sexo", "pornografia", "porno", "desnudo", "desnuda", "ereccion"],
    "drogas y alcohol": ["droga", "drogas", "cigarro", "fumar", "alcohol", "cerveza", "vino", "whisky"],
    "armas y explosivos": ["arma", "armas", "pistola", "rifle", "escopeta", "bala", "balas", "bomba", "bombas", "explosivo", "explosivos"],
    "autolesion": ["suicidio", "suicidarme", "matarme", "matar", "matare", "maten"],
    "violencia grafica": ["gore", "sangre", "tortura", "degollar"],
    "delitos": ["hackear", "hackeo", "robar", "robo", "crimen"],
    "jailbreak": ["jailbreak", "ignorar reglas", "romper reglas", "actua como", "actuar como", "system prompt", "prompt del sistema"],
}

FRASES_ESCOLARES_PERMITIDAS = [
    "muerte de las estrellas",
    "muerte de los dinosaurios",
    "extincion de los dinosaurios",
    "ciclo de vida",
]

ESQUEMA_HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_en_internet_seguro",
            "description": "Busca datos escolares actualizados, eventos historicos o dudas de cultura general en internet de forma segura.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Frase clave o pregunta a buscar en la web."}
                },
                "required": ["consulta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_matematicas_exactas",
            "description": "Ejecuta calculos matematicos avanzados, ecuaciones, fracciones o algebra usando un motor de computo numerico real.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expresion": {"type": "string", "description": "La operacion matematica en texto plano (ej: '5/4 + 3/2' o 'x + 10 = 25')."}
                },
                "required": ["expresion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "leer_archivo_de_tarea",
            "description": "Lee el contenido de un archivo PDF o TXT guardado en la carpeta de tareas local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {"type": "string", "description": "Nombre exacto del archivo con extension (ej: 'cuento.pdf' o 'historia.txt')."}
                },
                "required": ["nombre_archivo"]
            }
        }
    }
]

SYSTEM_PROMPT = """Eres un tutor escolar para ninos de 8 anos. Responde en espanol, corto, claro y amable.

Formato obligatorio:
- Usa maximo 4 lineas.
- No uses emojis.
- No muestres pensamientos internos ni etiquetas como .
- Si no sabes algo, di que no lo sabes y sugiere preguntarle a tu maestro.

REGLAS OBLIGATORIAS PARA HERRAMIENTAS:
- Para buscar informacion, usa buscar_en_internet_seguro.
- Para leer archivos, usa leer_archivo_de_tarea.
- Despues de recibir el resultado de una herramienta, explicalo al nino de forma simple.
- Si la pregunta parece matematica con numeros u operaciones, el backend ya la resolvio antes de llamarte.

Seguridad: No respondas temas inapropiados. Solo materias escolares."""

MATH_PREFIX_RE = re.compile(
    r"^(calcula|resuelve|cuanto es|cuanto da|resultado de|evalua|la ecuacion|ecuacion)\s*",
    re.IGNORECASE,
)
MATH_ALLOWED_RE = re.compile(r"^[0-9+\-*/().,= xXyYzZ]+$", re.IGNORECASE)
MATH_DETECT_RE = [
    re.compile(r"\d\s*[+\-*/^]\s*\d"),
    re.compile(r"\d\s*=\s*\d"),
    re.compile(r"\b[xxyz]\b\s*[+\-*/=]\s*\d"),
    re.compile(r"\d\s*[+\-*/=]\s*\b[xxyz]\b"),
    re.compile(r"(calcula|resuelve|cuanto es|cuanto da|resultado de|evalua)\s*.*\d"),
]


def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.lower()


def limpiar_respuesta(texto):
    if not texto:
        return ""
    think_open = "<" + "think" + ">"
    think_close = "</" + "think" + ">"
    texto = re.sub(re.escape(think_open) + r".*?" + re.escape(think_close), "", texto, flags=re.DOTALL)
    texto = texto.replace(think_open, "").replace(think_close, "")
    texto = re.sub(r"[\U00010000-\U0010ffff]", "", texto)
    return texto.strip()


def patrones_categoria(categoria):
    return [re.compile(rf"(?<!\w){re.escape(normalizar_texto(term))}(?!\w)") for term in categoria]


PATTERNS_PROHIBIDOS = {
    categoria: patrones_categoria(terms)
    for categoria, terms in CATEGORIAS_PROHIBIDAS.items()
}


def es_pregunta_segura(texto_usuario):
    texto = normalizar_texto(texto_usuario)
    if not texto.strip():
        return True, ""

    frases_permitidas = any(frase in texto for frase in FRASES_ESCOLARES_PERMITIDAS)
    for categoria, patrones in PATTERNS_PROHIBIDOS.items():
        if frases_permitidas and categoria in {"autolesion", "violencia grafica"}:
            continue
        for patron in patrones:
            if patron.search(texto):
                return False, f"Esa pregunta toca un tema de {categoria}. Preguntemos algo de tus materias escolares."
    return True, ""


def base_url(url):
    return url[:-3] if url.endswith("/v1") else url


def props_ready(url, timeout=2):
    try:
        with urllib.request.urlopen(f"{base_url(url)}/props", timeout=timeout) as response:
            return b"supports_tool_calls" in response.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_props(url, timeout_seconds):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if props_ready(url, timeout=2):
            return True
        time.sleep(1)
    return False


def ensure_vision_server():
    global vision_client, vision_process, vision_log_handle

    if props_ready(CONFIG["vision_url"], timeout=3):
        if vision_client is None:
            vision_client = OpenAI(base_url=CONFIG["vision_url"], api_key="local", timeout=CONFIG["openai_timeout"])
        return vision_client

    if vision_process is not None and vision_process.poll() is None:
        if wait_props(CONFIG["vision_url"], 10):
            vision_client = OpenAI(base_url=CONFIG["vision_url"], api_key="local", timeout=CONFIG["openai_timeout"])
            return vision_client
        raise RuntimeError("El servidor de vision estaba iniciando, pero no respondio a tiempo.")

    if not CONFIG["model_path"].exists():
        raise RuntimeError(f"No existe el modelo: {CONFIG['model_path']}")
    if not CONFIG["mmproj_path"].exists():
        raise RuntimeError(f"No existe el mmproj: {CONFIG['mmproj_path']}")

    cmd = [
        str(CONFIG["llama_dir"] / "llama-server"),
        "-m", str(CONFIG["model_path"]),
        "--mmproj", str(CONFIG["mmproj_path"]),
        "-c", CONFIG["ctx_size"],
        "--host", "127.0.0.1",
        "--port", str(CONFIG["vision_port"]),
        "-ngl", CONFIG["ngpu_layers"],
        "--device", CONFIG["vulkan_device"],
        "--fit", "on",
        "--fit-target", CONFIG["fit_target"],
        "--reasoning", "off",
        "--reasoning-budget", "0",
        "--reasoning-format", "deepseek",
        "--jinja",
        "--no-warmup",
        "--cache-ram", "0",
        "--prio", "-1",
        "-np", "1",
    ]

    log_dir = Path.home() / ".config"
    log_dir.mkdir(parents=True, exist_ok=True)
    vision_log_handle = open(log_dir / "llama-vision.log", "ab")
    pid_file = log_dir / "tutor_vision_server.pid"

    vision_process = subprocess.Popen(
        cmd,
        stdout=vision_log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    pid_file.write_text(str(vision_process.pid))

    if not wait_props(CONFIG["vision_url"], CONFIG["vision_start_timeout"]):
        stop_vision_server()
        raise RuntimeError("El servidor de vision no quedo listo. Revisa ~/.config/llama-vision.log")

    vision_client = OpenAI(base_url=CONFIG["vision_url"], api_key="local", timeout=CONFIG["openai_timeout"])
    return vision_client


def stop_vision_server():
    global vision_client, vision_process, vision_log_handle

    if vision_process is None:
        return

    try:
        os.kill(vision_process.pid, signal.SIGTERM)
        vision_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.kill(vision_process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass

    pid_file = Path.home() / ".config" / "tutor_vision_server.pid"
    try:
        pid_file.unlink()
    except FileNotFoundError:
        pass

    if vision_log_handle is not None:
        vision_log_handle.close()
        vision_log_handle = None

    vision_process = None
    vision_client = None


def buscar_en_internet_seguro(consulta):
    try:
        with DDGS() as ddgs:
            resultados = ddgs.text(consulta, max_results=3)
            if not resultados:
                return "No encontre resultados seguros para esa busqueda en la web."
            texto_encontrado = "\n".join([f"- {r['body']}" for r in resultados])
            return f"[Resultados Web Seguros para '{consulta}']:\n{texto_encontrado}"
    except Exception as e:
        return f"Error al conectar con el buscador web: {str(e)}"


def detectar_matematica(pregunta):
    texto = normalizar_texto(pregunta)
    return any(patron.search(texto) for patron in MATH_DETECT_RE)


def extraer_expresion_matematica(pregunta):
    texto = pregunta.replace("×", "*").replace("÷", "/")
    texto = normalizar_texto(texto)
    texto = texto.replace("igual", "=").replace("mas", "+").replace("menos", "-").replace("por", "*").replace("entre", "/")
    texto = MATH_PREFIX_RE.sub("", texto).strip()
    texto = re.sub(r"[?.!;:].*$", "", texto).strip()
    texto = re.sub(r"\b(a|la|el|los|las|de|del|ayuda|con|para|favor|por favor)\b", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    if "=" in texto:
        match = re.search(r"[A-Za-z0-9+\-*/().,=\s]{2,120}", texto)
        return match.group(0).strip() if match else texto

    match = re.search(r"[+\-]?\d+(?:[.,]\d+)?(?:\s*[+\-*/^]\s*[+\-]?\d+(?:[.,]\d+)?)+", texto)
    return match.group(0).strip() if match else texto


def parse_math_side(side, symbols):
    side = side.replace(",", ".")
    side = side.replace("^", "**")
    side = re.sub(r"\s+", "", side)
    if not MATH_ALLOWED_RE.fullmatch(side):
        raise ValueError("expresion no permitida")
    transformations = standard_transformations + (implicit_multiplication_application,)
    return parse_expr(side, transformations=transformations, local_dict=symbols)


def resolver_matematica_backend(pregunta):
    if not detectar_matematica(pregunta):
        return None

    expresion = extraer_expresion_matematica(pregunta)
    if not expresion or not MATH_ALLOWED_RE.fullmatch(expresion.replace(" ", "")):
        return "[Math Engine]: No pude identificar una operacion matematica clara. Escribe algo como x + 10 = 25 o 5/4 + 3/2."

    symbols = {letter: sympy.Symbol(letter) for letter in "xyz"}
    try:
        if "=" in expresion:
            left, right = expresion.split("=", 1)
            ecuacion = sympy.Eq(parse_math_side(left, symbols), parse_math_side(right, symbols))
            variables = sorted([s.name for s in ecuacion.free_symbols if s.name in symbols], key=lambda n: "xyz".index(n))
            variable = variables[0] if variables else "x"
            solucion = sympy.solve(ecuacion, symbols[variable])
            if not solucion:
                return f"[Math Engine]: La ecuacion {expresion} no tiene una solucion simple."
            valor = solucion[0]
            comprobacion = expresion.replace(variable, f"({valor})")
            return f"[Math Engine]: La ecuacion es {expresion}. Despejando {variable}, el valor es {variable} = {valor}. Compruebalo sustituyendo: {comprobacion}."

        resultado = parse_math_side(expresion, symbols)
        return f"[Math Engine]: La expresion es {expresion}. El resultado exacto es {resultado}."
    except Exception:
        return "[Math Engine]: No pude resolver esa expresion de forma segura. Escribe la operacion con numeros, signos y una sola incognita."


def calcular_matematicas_exactas(expresion):
    return resolver_matematica_backend(expresion) or "[Math Engine]: No pude resolver esa expresion de forma segura."


def leer_archivo_de_tarea(nombre_archivo):
    ruta_completa = os.path.join(CARPETA_ESCOLAR, nombre_archivo)
    if not os.path.exists(ruta_completa):
        return f"El archivo '{nombre_archivo}' no existe en tu carpeta de tareas. Asegurate de guardarlo en: {CARPETA_ESCOLAR}"
    try:
        if nombre_archivo.lower().endswith('.txt'):
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                return f"[Contenido de {nombre_archivo}]:\n{f.read()[:3000]}"
        elif nombre_archivo.lower().endswith('.pdf'):
            reader = PdfReader(ruta_completa)
            texto_pdf = ""
            for pagina in reader.pages[:5]:
                texto_pdf += pagina.extract_text() or ""
            return f"[Contenido extraido de {nombre_archivo}]:\n{texto_pdf[:3000]}"
        else:
            return "Formato de archivo no soportado. Por favor usa solo archivos .txt o .pdf."
    except Exception as e:
        return f"No se pudo leer el archivo escolar por un error tecnico: {str(e)}"


def speech_to_text(audio_path):
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, language="es")
        texto = " ".join([seg.text for seg in segments])
        return texto.strip()
    except Exception as e:
        logging.error(f"STT error: {e}")
        return None


def text_to_speech(texto):
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
        proc = subprocess.run(
            [PIPER_BIN, "--model", PIPER_VOICE, "--output_file", wav_path],
            input=texto.encode("utf-8"),
            capture_output=True,
            timeout=30
        )
        if proc.returncode == 0 and os.path.exists(wav_path):
            with open(wav_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode()
            os.unlink(wav_path)
            return audio_b64
        return None
    except Exception as e:
        logging.error(f"TTS error: {e}")
        return None


def orquestar_chat(pregunta_usuario, imagen_b64=None):
    logging.info(f"Usuario: {pregunta_usuario}")

    respuesta_matematica = resolver_matematica_backend(pregunta_usuario)
    if respuesta_matematica:
        logging.info(f"Tutor math: {respuesta_matematica}")
        return respuesta_matematica

    vision_started = False
    try:
        current_client = client
        if imagen_b64:
            current_client = ensure_vision_server()
            vision_started = True
            user_content = [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{imagen_b64}"}},
                {"type": "text", "text": pregunta_usuario}
            ]
        else:
            user_content = pregunta_usuario

        mensajes = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        respuesta = current_client.chat.completions.create(
            model=CONFIG["model"],
            messages=mensajes,
            tools=ESQUEMA_HERRAMIENTAS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=300,
            timeout=CONFIG["openai_timeout"],
        )

        mensaje_ia = respuesta.choices[0].message

        if mensaje_ia.tool_calls:
            mensajes.append(mensaje_ia.model_dump())

            for llamada in mensaje_ia.tool_calls:
                nombre_funcion = llamada.function.name
                argumentos = json.loads(llamada.function.arguments)

                if nombre_funcion == "buscar_en_internet_seguro":
                    resultado_herramienta = buscar_en_internet_seguro(argumentos.get("consulta"))
                elif nombre_funcion == "calcular_matematicas_exactas":
                    resultado_herramienta = calcular_matematicas_exactas(argumentos.get("expresion"))
                elif nombre_funcion == "leer_archivo_de_tarea":
                    resultado_herramienta = leer_archivo_de_tarea(argumentos.get("nombre_archivo"))
                else:
                    resultado_herramienta = "Herramienta no encontrada."

                mensajes.append({
                    "role": "tool",
                    "tool_call_id": llamada.id,
                    "name": nombre_funcion,
                    "content": resultado_herramienta
                })

            respuesta_final = current_client.chat.completions.create(
                model=CONFIG["model"],
                messages=mensajes,
                temperature=0.7,
                max_tokens=500,
                timeout=CONFIG["openai_timeout"],
            )
            reply = limpiar_respuesta(respuesta_final.choices[0].message.content or "")
        else:
            reply = limpiar_respuesta(mensaje_ia.content or "")

        logging.info(f"Tutor: {reply}")
        return reply
    finally:
        if vision_started:
            stop_vision_server()


if __name__ == "__main__":
    try:
        linea_entrada = sys.stdin.readline()
        if linea_entrada:
            datos_json = json.loads(linea_entrada)
            pregunta = datos_json.get("texto", "")
            audio_b64 = datos_json.get("audio", None)
            imagen_b64 = datos_json.get("imagen", None)
            voz = datos_json.get("voz", False)

            if audio_b64:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    audio_path = f.name
                    f.write(base64.b64decode(audio_b64))
                pregunta = speech_to_text(audio_path)
                os.unlink(audio_path)
                if not pregunta:
                    print(json.dumps({"respuesta": "No pude entender tu voz. Intenta de nuevo mas despacio."}))
                    sys.exit(0)

            if pregunta.strip():
                seguro, motivo = es_pregunta_segura(pregunta)
                if not seguro:
                    respuesta = motivo
                else:
                    respuesta = orquestar_chat(pregunta, imagen_b64)
            else:
                respuesta = "Hola! Escribeme una pregunta sobre tu tarea."

            resultado = {"respuesta": respuesta}

            if voz:
                audio_respuesta = text_to_speech(respuesta)
                if audio_respuesta:
                    resultado["audio"] = audio_respuesta

            print(json.dumps(resultado))
        else:
            print(json.dumps({"respuesta": "No se recibio ninguna pregunta."}))
    except Exception as e:
        print(json.dumps({"respuesta": f"Lo siento, ocurrio un error en el sistema de tutoria: {str(e)}"}))
