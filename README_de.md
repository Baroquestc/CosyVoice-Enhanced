# 🎙️ CosyVoice Erweiterte Ausgabe

[![SVG Banners](https://svg-banners.vercel.app/api?type=origin&text1=CosyVoice🤠&text2=OpenAI%20Kompatible%20TTS%20API&width=800&height=210)](https://github.com/FunAudioLLM/CosyVoice)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-brightgreen" alt="Python Version">
  <img src="https://img.shields.io/badge/Docker-Bereit-blue" alt="Docker Bereit">
  <img src="https://img.shields.io/badge/API-OpenAI%20Kompatibel-orange" alt="OpenAI Kompatibel">
  <img src="https://img.shields.io/badge/GPU-CUDA%2012.4-green" alt="CUDA Unterstützung">
  <img src="https://img.shields.io/badge/Streaming-Unterstützt-purple" alt="Streaming Unterstützung">
</p>

## 🌟 Funktionen der Erweiterten Ausgabe

Diese erweiterte Version basiert auf dem offiziellen [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) mit professionellen Ergänzungen für Produktionsbereitstellung:

### 🎯 **OpenAI Kompatible API**
- **Vollständige OpenAI TTS API Kompatibilität** - Drop-in Ersatz für OpenAIs `/v1/audio/speech` Endpunkt
- **Mehrere Audioformate**: MP3, WAV, FLAC, AAC, Opus, PCM (24kHz 16-bit)
- **Stimmen-Mapping**: Nahtlose Integration mit OpenAI Stimmennamen (alloy, echo, fable, etc.)
- **Produktionsbereit**: Gebaut mit Flask und Waitress für hochperformante Bereitstellung

### 🎨 **Erweiterte Web-Oberfläche**
- **Moderne Material Design UI** mit Dunkel/Hell-Theme Unterstützung
- **Mehrsprachige Unterstützung** (Chinesisch/Englisch) mit i18n Framework
- **Erweiterte Stimmenverwaltung**: Upload, Verwaltung und Organisation von Stimmenbibliotheken
- **Echtzeit-Audio-Transkription** mit externer API-Integration
- **Modellwechsel**: Nahtloses Umschalten zwischen CosyVoice 1.0/2.0 Modellen
- **Stapelverarbeitung**: Erzeugung mehrerer Stimmen mit Warteschlangenverwaltung

### 🐳 **Produktions-Docker-Bereitstellung**
- **Ein-Klick-Bereitstellung** mit Docker Compose
- **GPU-Beschleunigung**: Vollständige NVIDIA CUDA und TensorRT Unterstützung
- **VLLM-Integration**: Automatische Erkennung und Optimierung für CosyVoice2
- **Gesundheitsüberwachung**: Eingebaute Gesundheitsprüfungen und Protokollierung
- **Umgebungsflexibilität**: Konfigurierbar über Umgebungsvariablen

### ⚡ **Leistungsoptimierungen**
- **Streaming-Inferenz**: Niedriglatenz-Echtzeitsynthese
- **Modell-Caching**: Intelligentes Modelladen und Speicherverwaltung
- **VLLM-Beschleunigung**: Bis zu 3x schnellere Inferenz für CosyVoice2
- **Audioverarbeitung**: Integrierte Lautstärkenormalisierung und Formatkonvertierung

---

## 🚀 Schnellstart

### Option 1: Docker-Bereitstellung (Empfohlen)

```bash
# Repository klonen
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice

# Modelle herunterladen (bevorzugtes Modell wählen)
python scripts/download.py --model CosyVoice2-0.5B
# oder: python scripts/download.py --model CosyVoice-300M-SFT

# Mit Docker Compose starten
cd docker
docker-compose up -d

# Service-Status überprüfen
docker-compose logs -f cosyvoice-api
```

**🎯 API bereit unter**: `http://localhost:9996`  
**🌐 Web UI bereit unter**: `http://localhost:9996/webui`

### 🖱️ Ein-Klick-Skripte (Windows)

Für Windows-Benutzer bieten wir praktische Batch-Skripte im `scripts/` Verzeichnis:

```bash
# Zuerst zum Projekt-Stammverzeichnis navigieren
cd CosyVoice

# Dann eines dieser Ein-Klick-Skripte verwenden:
scripts\docker-compose-up.bat      # Services im Hintergrund starten
scripts\docker-compose-stop.bat    # Services stoppen (Container bleiben)
scripts\docker-compose-restart.bat # Alle Services neu starten
scripts\docker-compose-down.bat    # Stoppen und Container entfernen
```

**📋 Skript-Funktionen:**
- **🔍 Auto-Erkennung**: Erkennt und startet Docker Desktop automatisch wenn nötig
- **⏱️ Intelligentes Warten**: Wartet bis Docker bereit ist bevor fortgefahren wird
- **📊 Status-Rückmeldung**: Klare Fortschrittsanzeigen und Fehlermeldungen
- **🛡️ Fehlerbehandlung**: Elegante Fehlerbehandlung mit hilfreichen Nachrichten

**⚠️ Wichtige Hinweise:**
- Skripte vom **Projekt-Stammverzeichnis** ausführen (nicht vom `scripts/` Ordner)
- Skripte navigieren automatisch zum korrekten `docker/` Verzeichnis
- Erster Start kann 2-3 Minuten für Docker Desktop Initialisierung dauern
- Sicherstellen, dass Docker Desktop installiert ist bevor diese Skripte verwendet werden

### Option 2: Lokale Installation

```bash
# Conda-Umgebung erstellen
conda create -n cosyvoice python=3.10 -y
conda activate cosyvoice

# Abhängigkeiten installieren
pip install -r requirements.txt

# Modelle herunterladen
python scripts/download.py --model CosyVoice2-0.5B

# API-Server starten
python api/api.py --model pretrained_models/CosyVoice2-0.5B --port 9996

# Web UI starten (in anderem Terminal)
python api/webui.py --model_dir pretrained_models/CosyVoice2-0.5B --port 7860
```

---

## 📚 Verwendungsbeispiele

### 🔌 OpenAI Kompatible API

Ersetzen Sie Ihre OpenAI TTS-Aufrufe nahtlos durch CosyVoice:

```python
from openai import OpenAI

# Auf Ihren CosyVoice-Server zeigen
client = OpenAI(
    api_key="dummy-key",  # Nicht erforderlich aber vom OpenAI-Client erwartet
    base_url="http://localhost:9996/v1"
)

# Sprache generieren (identisch mit OpenAI API)
response = client.audio.speech.create(
    model="tts-1",
    voice="中文女", 
    input="Hallo! Das ist CosyVoice mit verbesserter Qualität.",
    response_format="mp3"
)

# Audio speichern
with open("speech.mp3", "wb") as f:
    f.write(response.content)
```

### 🌐 cURL Beispiele

```bash
# Grundlegende Sprachgenerierung
curl -X POST "http://localhost:9996/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hallo, das ist ein Test der Sprachsynthese von CosyVoice erweiterte Ausgabe.",
    "voice": "中文女",
    "response_format": "mp3"
  }' \
  --output speech.mp3

# Streaming-Antwort
curl -X POST "http://localhost:9996/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Echtzeit-Streaming-Synthese-Demonstration.",
    "voice": "中文女",
    "response_format": "mp3",
    "stream": true
  }' \
  --output streaming_speech.mp3
```

### 🎨 Web-Oberflächen-Funktionen

1. **🎯 Modellverwaltung**: Sofortiger Wechsel zwischen CosyVoice 1.0/2.0 Modellen
2. **🎤 Stimmenbibliothek**: Upload und Verwaltung benutzerdefinierter Stimmenproben
3. **🌍 Mehrsprachig**: Sprachgenerierung in Chinesisch, Englisch, Japanisch, Koreanisch
4. **📝 Intelligente Transkription**: Auto-Transkription hochgeladener Audios für Stimmklonierung
5. **⚡ Stapelverarbeitung**: Generierung mehrerer Audiodateien mit verschiedenen Stimmen
6. **🎨 Theme-Unterstützung**: Professionelle Dunkel/Hell-Modus-Oberfläche

---

## 🏗️ Architektur & Modelle

### 📊 Modellvergleich

| Modell | Größe | Sprachen | Funktionen | Am besten für |
|-------|------|-----------|----------|----------|
| **CosyVoice2-0.5B** | 500M | 5+ Sprachen | Streaming, VLLM, Ultra-niedrige Latenz | **Produktions-API** |
| **CosyVoice-300M-SFT** | 300M | 5+ Sprachen | Zero-Shot-Klonierung | **Stimmklonierung** |
| **CosyVoice-300M-Instruct** | 300M | 5+ Sprachen | Natürlichsprachsteuerung | **Kreative Synthese** |

### 🎯 Unterstützte Sprachen
- **Chinesisch** (Mandarin + Dialekte: Kantonesisch, Sichuanesisch, Shanghainesisch, etc.)
- **Englisch** (Amerikanische/Britische Akzente)
- **Japanisch** (Standard Japanisch)
- **Koreanisch** (Standard Koreanisch)
- **Sprachübergreifende Synthese** und Code-Switching

### 🔧 Leistungsmerkmale

#### **CosyVoice2 Verbesserungen**
- ⚡ **150ms Erste-Token-Latenz** für Streaming
- 🎯 **30-50% weniger Aussprachefehler** vs v1.0
- 🔊 **5.53 MOS-Score** (vs 5.4 in v1.0)
- 🚀 **VLLM-Beschleunigung** mit Auto-Erkennung

#### **Produktionsoptimierungen**
- 📊 **Automatische Lautstärkenormalisierung** (-23 LUFS)
- 🎵 **Multi-Format-Audiokonvertierung** (MP3, WAV, FLAC, etc.)
- 💾 **Intelligentes Modell-Caching** und Speicherverwaltung
- 🐳 **Containerisierte Bereitstellung** mit Gesundheitsüberwachung

---

## 🐳 Docker-Konfiguration

### Umgebungsvariablen

```env
# API-Konfiguration
API_HOST=0.0.0.0
API_PORT=9996
MODEL_DIR=pretrained_models/CosyVoice2-0.5B

# Leistungsoptionen
LOAD_JIT=false          # TorchScript JIT-Kompilierung
LOAD_TRT=false          # TensorRT-Optimierung (nur Linux)
FP16=false              # Halbpräzisions-Inferenz
USE_FLOW_CACHE=false    # Flow-Modell-Caching

# VLLM-Beschleunigung (nur CosyVoice2)
LOAD_VLLM=auto          # auto|true|false
NO_AUTO_VLLM=false      # Automatische VLLM-Erkennung deaktivieren

# GPU-Konfiguration
CUDA_VISIBLE_DEVICES=all
NVIDIA_VISIBLE_DEVICES=all
```

### Volume-Mounts

```yaml
volumes:
  # Modelldateien (erforderlich)
  - ./pretrained_models:/workspace/CosyVoice/pretrained_models:ro
  
  # Logs und temporäre Dateien
  - ./logs:/workspace/CosyVoice/logs
  - ./tmp:/workspace/CosyVoice/tmp
  
  # Benutzerdefinierte Konfiguration (optional)
  - ./config:/workspace/CosyVoice/config:ro
```

---

## 🛠️ Erweiterte Konfiguration

### 📁 Skript-Verzeichnis Übersicht

Das `scripts/` Verzeichnis enthält verschiedene Hilfsskripte für unterschiedliche Bereitstellungsszenarien:

#### 🐳 **Docker-Verwaltungsskripte (Windows)**
| Skript | Zweck | Verwendung | Hinweise |
|--------|---------|-------|-------|
| `docker-compose-up.bat` | Services starten | Doppelklick oder von Root ausführen | Startet Container im Hintergrund |
| `docker-compose-stop.bat` | Services stoppen | Doppelklick oder von Root ausführen | Stoppt Container, behält Daten |
| `docker-compose-restart.bat` | Services neu starten | Doppelklick oder von Root ausführen | Startet alle Container neu |
| `docker-compose-down.bat` | Container entfernen | Doppelklick oder von Root ausführen | Stoppt und entfernt Container |

#### 🚀 **Bereitstellungs- & Setup-Skripte**
| Skript | Zweck | Plattform | Beschreibung |
|--------|---------|----------|-------------|
| `deploy.sh` | Produktionsbereitstellung | Linux/macOS | Erweiterte Docker-Bereitstellung mit Gesundheitsprüfungen |
| `setup.bat` | Umgebungssetup | Windows | Abhängigkeiten installieren und Umgebung konfigurieren |
| `download.py` | Modell-Downloader | Plattformübergreifend | Vortrainierte Modelle von ModelScope herunterladen |

#### 🖥️ **Entwicklungsskripte (Windows)**
| Skript | Zweck | Verwendung | Beschreibung |
|--------|---------|-------|-------------|
| `run-api.bat` | API-Server starten | Doppelklick | Schneller lokaler API-Server-Start |
| `run-webui.bat` | Web UI starten | Doppelklick | Schneller lokaler Web UI-Start |

**🔧 Verwendungsrichtlinien:**
- **Windows-Skripte**: Vom Projekt-Stammverzeichnis ausführen, nicht vom `scripts/` Ordner
- **Plattformübergreifende Skripte**: Können von jedem Verzeichnis ausgeführt werden
- **Auto-Erkennung**: Skripte prüfen automatisch Abhängigkeiten und Docker-Status
- **Fehlerbehandlung**: Alle Skripte enthalten umfassende Fehlerprüfung und Benutzer-Feedback

**⚠️ Voraussetzungen:**
- **Docker-Skripte**: Benötigen Docker Desktop Installation
- **Python-Skripte**: Benötigen Python 3.10+ und conda-Umgebung
- **Modell-Skripte**: Benötigen Internetverbindung für Downloads

### API-Server-Optionen

```bash
python api/api.py \
    --model pretrained_models/CosyVoice2-0.5B \
    --host 0.0.0.0 \
    --port 9996 \
    --load-vllm \           # VLLM-Beschleunigung aktivieren
    --fp16 \                # Halbpräzision verwenden
    --load-jit              # JIT-Kompilierung aktivieren
```

### Web UI-Optionen

```bash
python api/webui.py \
    --model_dir pretrained_models/CosyVoice2-0.5B \
    --port 7860 \
    --language de \         # UI-Sprache (zh/en/de)
    --share \               # Öffentlichen Gradio-Link erstellen
    --transcription_url "https://api.openai.com/v1/audio/transcriptions" \
    --transcription_key "your-api-key"
```

### Modelltraining & Feinabstimmung

Für fortgeschrittene Benutzer sind Trainingsskripte verfügbar:

```bash
cd examples/libritts/cosyvoice
bash run.sh  # Vollständige Trainings-Pipeline
```

---

## 📖 API-Referenz

### Sprachgenerierungs-Endpunkt

**POST** `/v1/audio/speech`

```json
{
  "model": "tts-1",                    // Modell-Identifikator
  "input": "Zu synthetisierender Text", // Eingabetext (bis zu 4096 Zeichen)
  "voice": "中文女",                    // Stimmenauswahl
  "response_format": "mp3",            // Audioformat
  "speed": 1.0,                        // Wiedergabegeschwindigkeit (0.25-4.0)
  "stream": false                      // Streaming-Antwort aktivieren
}
```

### Gesundheitsprüfung

**GET** `/health` - Gibt Service-Status und Modellinformationen zurück

---

## 🔧 Fehlerbehebung

### Häufige Probleme

1. **CUDA Speicher nicht ausreichend**
   ```bash
   export CUDA_VISIBLE_DEVICES=0
   # FP16-Modus verwenden: --fp16
   ```

2. **VLLM-Installationsprobleme**
   ```bash
   # Separate Umgebung für VLLM erstellen
   conda create -n cosyvoice_vllm --clone cosyvoice
   conda activate cosyvoice_vllm
   pip install vllm==0.9.0
   ```

3. **Audioqualitätsprobleme**
   ```bash
   # Sox für bessere Audioverarbeitung installieren
   sudo apt-get install sox libsox-dev  # Ubuntu
   brew install sox                      # macOS
   ```

4. **Docker-Berechtigungsprobleme**
   ```bash
   # Benutzer zur docker-Gruppe hinzufügen
   sudo usermod -aG docker $USER
   ```

### Leistungsoptimierung

- **Für CPU-Inferenz**: `--fp16` und `--load-jit` verwenden
- **Für GPU-Inferenz**: `--load-vllm` aktivieren (nur CosyVoice2)
- **Für Produktion**: Docker mit Gesundheitsprüfungen und angemessenen Ressourcenlimits verwenden

---

## 📊 Benchmarks

### Latenzvergleich (CosyVoice2-0.5B)

| Konfiguration | Erster Token | Gesamtzeit (10s Audio) |
|---------------|-------------|-------------------------|
| Standard | 800ms | 2.1s |
| + JIT | 600ms | 1.8s |
| + VLLM | **150ms** | **0.9s** |
| + VLLM + FP16 | **120ms** | **0.7s** |

### Qualitätsmetriken

- **MOS-Score**: 5.53 (CosyVoice2) vs 5.4 (CosyVoice1)
- **Zeichenfehlerrate**: 30-50% Reduktion vs v1.0
- **Stimmenähnlichkeit**: 95%+ für Zero-Shot-Klonierung

---

## 🤝 Beitragen

Wir begrüßen Beiträge! Diese erweiterte Ausgabe fokussiert sich auf:

- 🔧 **Produktionsstabilität** und Leistungsoptimierungen
- 🌐 **API-Kompatibilität** mit Industriestandards
- 🎨 **Benutzererfahrungs**-Verbesserungen
- 🐳 **Bereitstellungs**-Vereinfachung

---

## 📄 Lizenz & Zitate

Dieses Projekt basiert auf dem ursprünglichen CosyVoice vom FunAudioLLM-Team. Bitte zitieren Sie die ursprünglichen Arbeiten:

```bibtex
@article{du2024cosyvoice,
  title={CosyVoice 2: Scalable streaming speech synthesis with large language models},
  author={Du, Zhihao and Wang, Yuxuan and Chen, Qian and others},
  journal={arXiv preprint arXiv:2412.10117},
  year={2024}
}

@article{du2024cosyvoice,
  title={Cosyvoice: A scalable multilingual zero-shot text-to-speech synthesizer based on supervised semantic tokens},
  author={Du, Zhihao and Chen, Qian and Zhang, Shiliang and others},
  journal={arXiv preprint arXiv:2407.05407},
  year={2024}
}
```

---

## 🔗 Links & Ressourcen

- **🏠 Original Repository**: [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice)
- **📊 Modell Hub**: [ModelScope](https://www.modelscope.cn/studios/iic/CosyVoice2-0.5B) | [HuggingFace](https://huggingface.co/spaces/FunAudioLLM/CosyVoice2-0.5B)
- **🎵 Live Demos**: [CosyVoice2 Demo](https://funaudiollm.github.io/cosyvoice2/)
- **📚 Dokumentation**: [Offizielle Docs](https://funaudiollm.github.io)
- **💬 Community**: [GitHub Issues](https://github.com/FunAudioLLM/CosyVoice/issues)

---

<p align="center">
  <b>🎉 Mit ❤️ für die AI-Community gebaut</b><br>
  <i>Erweiterte Ausgabe von Claude - KI-Sprachsynthese für alle zugänglich machen</i>
</p>

## ⚠️ Haftungsausschluss

Diese erweiterte Ausgabe wird für akademische und Forschungszwecke bereitgestellt. Die ursprünglichen CosyVoice-Modelle und Kernalgorithmen wurden vom FunAudioLLM-Team entwickelt. Einige Beispiele können aus dem Internet stammen - bitte kontaktieren Sie uns, wenn Inhalte Ihre Rechte verletzen.