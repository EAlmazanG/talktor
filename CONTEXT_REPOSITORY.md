# TALKTOR - CONTEXTO COMPLETO DEL REPOSITORIO

## 📋 RESUMEN GENERAL
**Talktor** es una aplicación de tutoría de inglés con agentes de IA que ayuda a los usuarios a mejorar su inglés a través de conversaciones. La aplicación proporciona retroalimentación sobre conversaciones, rastrea el progreso en diferentes pilares del idioma y ofrece rutas de aprendizaje personalizadas.

## 🏗️ ARQUITECTURA TÉCNICA
- **Backend**: FastAPI + PostgreSQL + OpenAI APIs
- **Agentes**: RealtimeAgent (voz) + StandardAgent (texto/análisis)
- **Base de datos**: PostgreSQL con SQLAlchemy
- **Contenedores**: Docker y docker-compose
- **APIs**: OpenAI GPT-4o, Whisper, TTS, Realtime API

## 📁 ESTRUCTURA DEL REPOSITORIO

### 📂 **ROOT DIRECTORY** (`/`)
```
├── .env                          # Variables de entorno (no en git)
├── .gitignore                    # Archivos ignorados por git
├── LICENSE                       # Licencia del proyecto
├── README.md                     # Documentación básica (solo título)
├── docker-compose.yml            # Configuración Docker producción
├── docker-compose.dev.yml        # Configuración Docker desarrollo
├── CONTEXT_REPOSITORY.md         # Este archivo de contexto
├── backend/                      # Código del backend
├── frontend/                     # Frontend (vacío actualmente)
├── scripts/                      # Scripts de desarrollo y POC
├── tests/                        # Tests de nivel raíz (vacío)
└── talktor-env/                  # Entorno virtual Python
```

### 📂 **BACKEND** (`/backend/`)
**Arquitectura modular con separación clara de responsabilidades**

#### 📁 **Core** (`/backend/core/`)
- `config.py` - Configuración centralizada con Pydantic Settings
- `logging.py` - Sistema de logging estructurado
- `colors.py` - Utilidades para colores en terminal

#### 📁 **Services** (`/backend/services/`)
**Capa de servicios de negocio**
- `session_state.py` - Gestión de estado de sesiones (SessionState, SessionManager)
- `audio_service.py` - Manejo de PyAudio (micrófono, altavoces)
- `openai_service.py` - Integración con APIs de OpenAI
- `conversation_service.py` - Lógica de conversación y function calls
- `conversation_flow.py` - Flujo completo de conversación con feedback
- `persistence_service.py` - Servicio centralizado para operaciones de BD

#### 📁 **Agents** (`/backend/agents/`)
**Capa de orquestación de alto nivel**
- `realtime_agent.py` - Agente principal para conversaciones de voz
- `standard_agent.py` - Agente GPT-4o para feedback, tareas, ejercicios

#### 📁 **Database** (`/backend/db/`)
**Capa de persistencia**
- `models.py` - Modelos SQLAlchemy (sessions, transcripts, feedback, homework, vocabulary)
- `database.py` - Configuración de base de datos
- `crud.py` - Operaciones CRUD completas

#### 📁 **API** (`/backend/api/`)
**Endpoints REST/WebSocket (vacío actualmente)**

#### 📁 **Schemas** (`/backend/schemas/`)
**Esquemas Pydantic (vacío actualmente)**

#### 📁 **Tests** (`/backend/tests/`)
**Tests específicos del backend**
- `test_realtime_agent.py` - Tests del agente principal
- `test_standard_agent.py` - Tests del agente de análisis
- `test_database.py` - Tests de base de datos
- `test_persistence_service.py` - Tests del servicio de persistencia
- `test_config_validation.py` - Tests de configuración
- `test_complete_flow.py` - Tests de flujo completo
- `test_real_voice_conversation.py` - Tests de conversación real
- `test_simple_flow.py` - Tests de flujo simple
- `test_termination_commands.py` - Tests de comandos de terminación

#### 📄 **Archivos principales**
- `main.py` - Aplicación FastAPI con endpoints básicos
- `requirements.txt` - Dependencias Python completas
- `Dockerfile` - Imagen Docker del backend
- `start.sh` - Script de inicio del contenedor
- `README_ARCHITECTURE.md` - Documentación detallada de arquitectura

### 📂 **SCRIPTS** (`/scripts/`)
**Scripts de desarrollo y POC**
- `realtime_poc.py` - POC original funcional (referencia)
- `dev_start.sh` - Iniciar entorno de desarrollo
- `dev_stop.sh` - Parar entorno de desarrollo
- `prod_start.sh` - Iniciar entorno de producción
- `prod_stop.sh` - Parar entorno de producción

### 📂 **FRONTEND** (`/frontend/`)
**Frontend (vacío actualmente)**
- Pendiente de implementación (Streamlit/Gradio planificado)

### 📂 **TESTS** (`/tests/`)
**Tests de nivel raíz (vacío actualmente)**

## 🗄️ MODELOS DE BASE DE DATOS

### **Sessions** - Metadatos de conversación
- `session_id` (UUID) - Identificador único
- `user_id` (String) - ID del usuario
- `agent_type` (Enum) - REALTIME/STANDARD
- `conversation_mode` (Enum) - FREE_TOPIC/REVIEW_PREVIOUS/SITUATIONAL/DYNAMIC/CHALLENGE
- `duration_seconds` (Float) - Duración de la conversación
- `message_count` (Integer) - Número de mensajes
- `total_cost` (Float) - Costo total de APIs
- `total_tokens` (Integer) - Tokens totales utilizados
- `created_at`, `updated_at` (DateTime) - Timestamps

### **Transcripts** - Contenido de conversaciones
- `transcript_id` (UUID) - Identificador único
- `session_id` (UUID) - FK a sessions
- `conversation_json` (JSON) - Conversación estructurada con mensajes individuales
- `created_at` (DateTime) - Timestamp

### **Feedback** - Retroalimentación estructurada
- `feedback_id` (UUID) - Identificador único
- `session_id` (UUID) - FK a sessions
- `pillar` (Enum) - PRONUNCIATION/FLUENCY/GRAMMAR/EXPRESSIONS/VOCABULARY/COMPREHENSION
- `score` (Integer) - Puntuación 1-10
- `specific_examples` (Text) - Ejemplos específicos
- `improvement_areas` (Text) - Áreas de mejora
- `created_at` (DateTime) - Timestamp

### **Homework Items** - Tareas asignadas
- `homework_id` (UUID) - Identificador único
- `session_id` (UUID) - FK a sessions
- `category` (String) - Categoría de la tarea
- `title` (String) - Título de la tarea
- `description` (Text) - Descripción detallada
- `difficulty` (String) - Nivel de dificultad
- `estimated_time` (Integer) - Tiempo estimado en minutos
- `priority` (String) - Prioridad de la tarea
- `created_at` (DateTime) - Timestamp

### **Vocabulary Items** - Vocabulario para aprender
- `vocabulary_id` (UUID) - Identificador único
- `session_id` (UUID) - FK a sessions
- `word` (String) - Palabra/expresión
- `definition` (Text) - Definición
- `example_sentence` (Text) - Ejemplo de uso
- `difficulty` (String) - Nivel de dificultad
- `created_at` (DateTime) - Timestamp

## 🔧 CONFIGURACIÓN DOCKER

### **Producción** (`docker-compose.yml`)
- **backend** - Aplicación FastAPI (puerto 8000)
- **db** - PostgreSQL 16 (puerto 5432)
- **pgadmin** - Administrador de BD (puerto 5050)
- **frontend** - Comentado hasta implementación

### **Desarrollo** (`docker-compose.dev.yml`)
- Solo **db** y **pgadmin**
- Backend se ejecuta localmente para desarrollo rápido

## 🚀 FUNCIONALIDADES IMPLEMENTADAS

### ✅ **RealtimeAgent** - Conversaciones de voz
- Integración completa con OpenAI Realtime API
- Manejo de audio bidireccional (micrófono/altavoces)
- Gestión de interrupciones naturales
- Transcripción estructurada con timestamps
- Persistencia automática en base de datos

### ✅ **StandardAgent** - Análisis y feedback
- Análisis de conversaciones en 6 pilares
- Generación de tareas personalizadas
- Creación de ejercicios por dificultad
- Consejos de aprendizaje personalizados
- Generación de flashcards (en desarrollo)

### ✅ **PersistenceService** - Operaciones de BD
- Transacciones atómicas
- API de alto nivel para operaciones complejas
- Logging centralizado
- Manejo de errores consistente
- Separación clara de responsabilidades

### ✅ **Sistema de transcripción estructurada**
- Mensajes individuales con timestamps
- Orden cronológico preservado
- Almacenamiento JSON eficiente
- Sin concatenación de mensajes

### ✅ **Configuración robusta**
- Variables de entorno centralizadas
- Validación de configuración
- Sin valores hardcodeados
- Configuración específica por entorno

## 🧪 ESTADO DE TESTING

### ✅ **Tests funcionales**
- PersistenceService: Todos los métodos funcionando
- ConversationFlow: Integración con transacciones atómicas
- RealtimeAgent: Conversaciones de voz completas
- StandardAgent: 4/5 características funcionando
- Base de datos: Persistencia verificada

### ✅ **Flujo completo verificado**
- Entrada de voz real → Transcripción → Análisis → BD
- 18+ sesiones de prueba completadas
- Más de 60 transcripciones guardadas
- Sistema de analytics funcionando

## 🔄 FLUJO DE DATOS ACTUAL

```
Usuario (voz) 
    ↓
RealtimeAgent 
    ↓
ConversationService (gestión de estado)
    ↓
ConversationFlow (análisis y feedback)
    ↓
PersistenceService (transacciones atómicas)
    ↓
Base de datos PostgreSQL
```

## 📋 PENDIENTES IDENTIFICADOS

### 🚧 **Próximos pasos**
1. **Endpoints FastAPI** - API REST/WebSocket para frontend
2. **Frontend** - Interfaz de usuario (Streamlit/Gradio)
3. **Comandos de terminación** - Comandos de voz para finalizar
4. **API Key OpenAI** - Configuración para feedback real
5. **Flashcards** - Corrección menor en StandardAgent

### 🎯 **Arquitectura preparada para**
- Microservicios
- Múltiples usuarios concurrentes
- Escalabilidad horizontal
- Integración con más APIs
- Análisis avanzados de progreso

## 🔐 SEGURIDAD Y CONFIGURACIÓN

### **Variables de entorno requeridas** (`.env`)
```
# OpenAI
OPENAI_API_KEY=

# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=

# pgAdmin
PGADMIN_DEFAULT_EMAIL=
PGADMIN_DEFAULT_PASSWORD=
```

### **Puertos utilizados**
- `8000` - Backend FastAPI
- `5432` - PostgreSQL
- `5050` - pgAdmin

## 📊 MÉTRICAS Y ANALYTICS

### **Datos capturados**
- Duración de conversaciones
- Número de mensajes por sesión
- Costos de API por sesión
- Tokens utilizados
- Progreso por pilares del idioma
- Historial completo de conversaciones

### **Analytics disponibles**
- Progreso del usuario a lo largo del tiempo
- Estadísticas por pillar de idioma
- Resúmenes de sesiones completos
- Tracking de mejoras

## 🎯 CONCLUSIÓN

El repositorio Talktor tiene una **arquitectura sólida y modular** con:
- ✅ **Sistema de conversaciones de voz funcional**
- ✅ **Base de datos completa y normalizada**
- ✅ **Servicios bien separados y testeable**
- ✅ **Transacciones atómicas y persistencia robusta**
- ✅ **Configuración flexible por entornos**
- ✅ **Testing comprehensivo**

**Estado actual**: Sistema core completamente funcional, listo para desarrollo de frontend y características avanzadas.
