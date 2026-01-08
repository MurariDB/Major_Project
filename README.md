
# EdgeLearn: Offline Multimodal AI Science Tutor

**EdgeLearn** is a privacy-first, offline-capable AI tutoring assistant designed to help students master science topics. It utilizes a **Hybrid RAG (Retrieval-Augmented Generation)** architecture to answer questions based *strictly* on uploaded course materials (PDFs).

The system features a **Next.js** frontend for a modern UI and a **FastAPI** backend that orchestrates local LLMs, Speech-to-Text, Text-to-Speech, and Multimodal (Text + Image) retrieval.

---

## 🚀 Key Features

* **Offline Capability:** Runs entirely locally using `GPT4All` and local embedding models. No internet required after setup.
* **Hybrid RAG Retrieval:** Combines three retrieval methods for maximum accuracy:
    * **Dense Retrieval:** Semantic search using FAISS and `sentence-transformers`.
    * **Sparse Retrieval:** Keyword matching using BM25.
    * **Knowledge Graph:** Graph-based expansion to find related concepts across documents.
* **Multimodal Answers:** Retrieves and displays relevant **images** and diagrams from your PDFs alongside text answers.
* **Voice Interaction:** Full voice-to-voice support using:
    * **Input:** Faster-Whisper / Transformers for speech-to-text.
    * **Output:** Hybrid TTS engine (Coqui TTS / EdgeTTS).
* **Interactive Dashboard:** A study room interface with real-time transcription, chat history, and document management.

---

## 🛠 Tech Stack

### **Backend (Python)**
* **Core Framework:** FastAPI
* **LLM:** GPT4All (`Llama-3.2-1B-Instruct-Q4_0.gguf`)
* **Vector DB:** FAISS (Dense) & SQLite (Metadata/Images)
* **Audio:** PyAudio, SoundDevice, Whisper, Coqui TTS
* **Computer Vision:** OpenCV, Pillow, PyTesseract (OCR)

### **Frontend (TypeScript)**
* **Framework:** Next.js 16 (App Router)
* **Language:** TypeScript
* **Styling:** Tailwind CSS
* **UI Components:** Shadcn UI, Radix UI, Lucide React
* **State Management:** React Hooks

---

## 📋 Prerequisites

* **OS:** Windows, macOS, or Linux
* **Python:** 3.10+
* **Node.js:** 18.17+ (Required for Next.js 16)
* **Hardware:**
    * RAM: 8GB minimum (16GB recommended for smooth LLM/TTS performance).
    * Disk: ~5GB free space for models.

---

## 📦 Installation Guide

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/EdgeLearn.git](https://github.com/yourusername/EdgeLearn.git)
cd EdgeLearn

```

### 2. Backend Setup (Python)

It is highly recommended to use a virtual environment.

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

**System Dependencies (Linux only):**
If you are on Linux, you may need to install audio and vision libraries:

```bash
sudo apt-get install portaudio19-dev python3-pyaudio ffmpeg tesseract-ocr

```

**Download Models:**
Run the setup scripts to download the necessary LLM and embedding models.

```bash
python setup_offline.py
python setup_voices.py

```

### 3. Frontend Setup (Next.js)

Navigate to the project root (where `package.json` is located).

```bash
# Install dependencies
npm install
# OR
pnpm install

```

---

## 🏃‍♂️ Usage

To run the full application, you need to run the **Backend API** and the **Frontend Client** simultaneously in two separate terminals.

### Terminal 1: Start API Server

This starts the FastAPI server which handles the AI logic.

```bash
# Make sure your venv is activated
uvicorn api_server:app --host 0.0.0.0 --port 8080 --reload

```

* **Status:** The API will be available at `http://localhost:8080`
* **Docs:** Swagger UI available at `http://localhost:8080/docs`

### Terminal 2: Start Frontend

This launches the user interface.

```bash
npm run dev

```

* **Access:** Open your browser and go to `http://localhost:3000`

---

## 📂 Project Structure

```text
EdgeLearn/
├── api_server.py          # FastAPI entry point (Bridges Frontend & Logic)
├── main.py                # Core RAG Assistant Logic
├── create_dataset.py      # Script to process PDFs for RAG
├── requirements.txt       # Python dependencies
├── package.json           # Frontend dependencies
├── src/
│   ├── audio/             # Speech-to-Text & Text-to-Speech modules
│   ├── llm/               # GPT4All Handler
│   ├── rag/               # Retrieval logic (Vector DB, Image Processor)
│   └── utils/             # Config, Logger, Knowledge Graph
├── app/                   # Next.js App Router pages
│   ├── page.tsx           # Main Landing/Home Controller
│   ├── layout.tsx         # Root layout
│   └── api/               # Next.js API Routes (Proxy)
├── components/            # React UI Components
│   ├── dashboard.tsx      # Main User Dashboard
│   ├── study-room.tsx     # Chat & Voice Interface
│   └── ...
└── data/
    ├── pdfs/              # Place your PDF textbooks here
    └── images/            # Extracted images from PDFs

```

---

## ⚙️ Configuration

You can customize the application behavior in `src/utils/config.py` or by setting Environment Variables.

| Variable | Description | Default |
| --- | --- | --- |
| `GPT4ALL_MODEL_NAME` | The LLM model filename | `Llama-3.2-1B-Instruct-Q4_0.gguf` |
| `PDF_DIR` | Directory to watch for documents | `./data/pdfs` |
| `OMP_NUM_THREADS` | Thread limit for PyTorch (Fixes macOS crash) | `1` |

---

## 🔍 How it Works

1. **Ingestion:** When you upload a PDF via the dashboard, `src/rag/text_processor.py` chunks the text and `src/rag/image_processor.py` extracts images/diagrams.
2. **Indexing:** Text chunks are embedded into FAISS; Images are analyzed (OCR) and stored in SQLite.
3. **Query:** When you ask a question (Voice or Text), the `RetrievalSystem` performs a hybrid search (Dense + Sparse + Graph).
4. **Generation:** The retrieved context + the user query are sent to the local `GPT4All` model.
5. **Response:** The LLM generates an answer, citing the specific PDF pages. Relevant images are displayed alongside the text.

---

## 🤝 Troubleshooting

* **"Service not initialized"**: Ensure `api_server.py` is running and that it successfully loaded `main.py` without import errors.
* **Audio issues**: Ensure you have a working microphone and that `sounddevice` / `portaudio` are installed correctly on your system.
* **Slow performance**: This runs on CPU. Performance depends on your processor. Using a smaller quantization (e.g., `q4_0`) helps.

```

```