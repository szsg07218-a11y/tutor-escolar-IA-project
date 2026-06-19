# 🎓 Tutor Escolar IA / AI School Tutor

![Version](https://img.shields.io/badge/version-1.0-blue)
![Model](https://img.shields.io/badge/model-Qwen3.5--0.8B-orange)
![Hardware](https://img.shields.io/badge/hardware-AMD_Vulkan-green)

Este es un asistente educativo local diseñado específicamente para niños, integrando capacidades multimodales y herramientas de apoyo escolar.

This is a local educational assistant specifically designed for children, integrating multimodal capabilities and school support tools.

---

## 🇪🇸 Español

### 🌟 Características
- **Interacción Multimodal**: Soporte para texto, imágenes y voz (entrada y salida).
- **Herramientas Integradas**:
  - 🔍 **Búsqueda Web**: Consultas seguras en internet vía DuckDuckGo.
  - 🧮 **Motor Matemático**: Resolución exacta de ecuaciones y operaciones mediante SymPy.
  - 📄 **Lector de Tareas**: Análisis de archivos PDF y TXT locales.
- **Optimización de Hardware**: Aceleración mediante Vulkan para GPUs AMD, logrando respuestas fluidas en hardware modesto.
- **Seguridad Infantil**: Filtros estrictos de contenido para asegurar un entorno educativo seguro.

### 🚀 Instalación y Uso
1. **Requisitos**: Linux Mint (Cinnamon), GPU AMD con soporte Vulkan.
2. **Inicio del Servidor**:
   ```bash
   bash ~/Documentos/IA/iniciar_tutor.sh
   ```
3. **Interfaz**: Una vez iniciado el servidor, el widget (desklet) se activará automáticamente en tu escritorio de Cinnamon.

### 🛠️ Componentes Técnicos
- **LLM**: Qwen3.5-0.8B (vía `llama.cpp`).
- **STT**: `faster-whisper` (Modelo tiny).
- **TTS**: `Piper TTS` (Voz en español).
- **Backend**: Python con OpenAI-compatible API.

---

## 🇺🇸 English

### 🌟 Features
- **Multimodal Interaction**: Support for text, images, and voice (input and output).
- **Integrated Tools**:
  - 🔍 **Web Search**: Safe internet queries via DuckDuckGo.
  - 🧮 **Math Engine**: Exact resolution of equations and operations using SymPy.
  - 📄 **Homework Reader**: Analysis of local PDF and TXT files.
- **Hardware Optimization**: Vulkan acceleration for AMD GPUs, ensuring smooth responses on modest hardware.
- **Child Safety**: Strict content filters to ensure a safe educational environment.

### 🚀 Installation and Usage
1. **Requirements**: Linux Mint (Cinnamon), AMD GPU with Vulkan support.
2. **Start Server**:
   ```bash
   bash ~/Documentos/IA/iniciar_tutor.sh
   ```
3. **Interface**: Once the server is running, the desklet will automatically activate on your Cinnamon desktop.

### 🛠️ Technical Components
- **LLM**: Qwen3.5-0.8B (via `llama.cpp`).
- **STT**: `faster-whisper` (Tiny model).
- **TTS**: `Piper TTS` (Spanish voice).
- **Backend**: Python with OpenAI-compatible API.

---

## 💻 Hardware Requirements
- **CPU**: Intel i3 or equivalent.
- **GPU**: AMD Radeon (Vulkan compatible).
- **RAM**: 8GB minimum.
- **OS**: Linux Mint 22.x / Ubuntu.
