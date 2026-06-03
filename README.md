# Paperless-ngx (AI-Enhanced)

**Paperless-ngx** is a document management system that transforms your physical documents into a searchable online archive. This version includes **integrated local AI (Ollama)** for automatic summarization and tagging.

## Quick Setup (Recommended)

The easiest way to get started is using **Docker**. No complex installation required!

### 1. Simple Docker Start (Standard Version)
> (Note: This runs the standard Paperless without the AI enhancements.)

1. **Copy configuration files**:
   ```bash
   cp docker/compose/docker-compose.sqlite.yml docker-compose.yml
   cp docker/compose/docker-compose.env docker-compose.env
   ```
2. **Start the application**:
   ```bash
   docker compose up -d
   ```
3. **Create your login**:
   ```bash
   docker exec -it paperless-webserver-1 python3 manage.py createsuperuser
   ```
   *Follow the prompts to set your username and password.*

4. **Access Paperless**: Open `http://localhost:8000` in your browser.

---

## 🚀 How to Run Your Enhanced Code on Another System

To ensure all the **AI features** I added (Smart Model Selection, Auto-Start, etc.) work on a new system, you have two choices:

### Option 1: Using Docker (Recommended)
If you want to use Docker but keep my AI enhancements, you **must clone the code** because the standard Docker image doesn't include my custom changes.

1.  **Clone your repository:**
    ```bash
    git clone https://github.com/azharhussaincs/PaperLess.git
    cd PaperLess
    ```
2.  **Setup Configuration:**
    ```bash
    cp docker/compose/docker-compose.sqlite.yml docker-compose.yml
    cp docker/compose/docker-compose.env docker-compose.env
    ```
3.  **Modify `docker-compose.yml` to use your code:**
    The `docker-compose.yml` file is located in the root of your `PaperLess` folder. Open it with a text editor (like Notepad, TextEdit, or VS Code).

    **Find the "volumes" section**: Look for the `webserver:` section, then the `volumes:` list underneath it.

    **Add the line**: Copy and paste the line so it looks like this:
    ```yaml
    services:
      webserver:
        # ... other settings ...
        volumes:
          - data:/usr/src/paperless/data
          - media:/usr/src/paperless/media
          - ./src:/usr/src/paperless/src  # <-- ADD THIS LINE HERE
    ```

    **Why is this done?**
    By adding this line to the file, you are telling Docker: *"Instead of using the default code inside the download, use the AI-Enhanced code I have in my local `src` folder."*

    **Summary:**
    - **File Location:** `docker-compose.yml` (in project root)
    - **File Edit:** Add `- ./src:/usr/src/paperless/src` inside `volumes` section.
    - **Terminal Command:** Once saved, run `docker compose up -d`.

4.  **Start and Create User:**
    ```bash
    docker compose up -d
    docker exec -it paperless-webserver-1 python3 manage.py createsuperuser
    ```

### Option 2: Clone and Run Locally (Development)
If you don't want to use Docker:
1.  **Clone the code:** `git clone ...`
2.  **Install dependencies:** `uv sync --all-extras`
3.  **Run migrations:** `python3 manage.py migrate`
4.  **Start server:** `python3 manage.py runserver`

---

## AI Features (Zero-Config)
If you have **Ollama** installed on your computer, Paperless-ngx will **automatically detect and start it** (if possible) and use your largest available model to:
- 📝 **Summarize** your documents automatically.
- 🏷️ **Suggest Tags** for better organization.
- 📂 **Auto-Title** files based on content.

### How it works:
1. **Auto-Start**: During startup, Paperless-ngx checks if Ollama is running. If it's installed but idle, it will wait for it to wake up.
2. **Smart Model Selection**: It scans all your installed models (e.g., `llama3:8b`, `deepseek:32b`) and **automatically picks the largest/best one** to ensure high-quality AI results.
3. **Automatic Fallback**: If no models are found, it will warn you in the logs and suggest pulling a default model.

*No setup needed—it just works if Ollama is installed!*

---

# Getting Started (Detailed)

There are two ways to setup this project:
1. **Docker (Easiest)**
2. **Django (For Developers)**

---

## 1. Setup using Docker

### Step-by-Step
1. **Download the configuration**:
   ```bash
   cp docker/compose/docker-compose.sqlite.yml docker-compose.yml
   cp docker/compose/docker-compose.env docker-compose.env
   ```
2. **Configure environment**:
   Edit `docker-compose.env` and set `PAPERLESS_SECRET_KEY` to any long random string.
3. **Run**:
   ```bash
   docker compose up -d
   ```
4. **Create Admin User**:
   ```bash
   docker exec -it paperless-webserver-1 python3 manage.py createsuperuser
   ```

### Using the Install Script
Alternatively, use the official interactive script:
```bash
bash -c "$(curl -L https://raw.githubusercontent.com/paperless-ngx/paperless-ngx/main/install-paperless-ngx.sh)"
```
**Tips for the script:**
- **URL []:** Just press **Enter** (leave blank).
- **Database:** Choose `sqlite` for simplicity or `postgres` for performance.

---

## 2. Setup as a Django Project (Local)
For those who want to run it without Docker:

### Prerequisites
- Python 3.12+
- Redis server running (`sudo apt install redis-server`)

### Installation
1. **Clone & Enter**:
   ```bash
   git clone https://github.com/azharhussaincs/PaperLess.git
   cd PaperLess
   ```
2. **Install dependencies**:
   ```bash
   pip install uv
   uv sync --all-extras
   source .venv/bin/activate
   ```
3. **Setup Database & Secret Key**:
   Copy `paperless.conf.example` to `paperless.conf`. Set a `PAPERLESS_SECRET_KEY`.
   ```bash
   cd src
   python3 manage.py migrate
   python3 manage.py createsuperuser
   ```
4. **Start Services**:
   - Webserver: `python3 manage.py runserver`
   - Worker: `python3 manage.py document_consumer`

---

## Ollama & AI Setup

To enable AI features, simply install Ollama:
1. **Install Ollama**: [ollama.com](https://ollama.com)
2. **Download a model**: `ollama pull llama3.1` (or any model you prefer).
3. **Done!** Paperless-ngx will find it automatically and pick the largest one if you have several.

### Linux Users (Docker)
If your AI isn't working in Docker on Linux, run:
```bash
sudo systemctl edit ollama.service
# Add:
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
# Save and restart:
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

---

# Features
- **OCR**: Digitalize your PDFs and images.
- **Search**: Full-text search across all documents.
- **Tags & Folders**: Organized your documents effortlessly.
- **AI Powered**: Summaries and insights provided by local LLMs.

# Important Note
> Paperless-ngx stores documents in clear text. Only run it on a trusted network (like your home).

---
# PaperLess
