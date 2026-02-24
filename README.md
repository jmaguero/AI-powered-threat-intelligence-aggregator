<div align="center">
  <h1>🛡️ AI-Powered Threat Intelligence Aggregator</h1>
  <p>
    <strong>A local, offline-first threat intelligence platform that leverages LLMs to aggregate, summarize, enrich, and semantically search security feeds.</strong>
  </p>
  <p>
    <img alt="Django" src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" />
    <img alt="React" src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
    <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
    <img alt="Docker" src="https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white" />
    <img alt="Celery" src="https://img.shields.io/badge/celery-%2337814A.svg?style=for-the-badge&logo=celery&logoColor=white" />
    <img alt="Redis" src="https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white" />
  </p>
</div>

---

## 📖 Overview

The **AI-Powered Threat Intelligence Aggregator** is designed to help security professionals sort through the noise of constant security alerts, news, and feeds. It fetches articles from multiple trusted sources (like CISA, Krebs, etc.), leverages local Large Language Models (LLMs) to automatically generate concise summaries, assigns threat labels and severities, and enables natural language (semantic) search over your entire threat data repository.

**Privacy-first & local-by-design:** The entire stack—including the LLM, vector database, and PostgreSQL—can run seamlessly on a single host (your local machine or a private server). No data needs to be sent to external cloud APIs, making it inherently secure for internal operations and sensitive analysis. You can fetch feeds while online, and perform all enrichment and search operations offline.

**Deploy Anywhere:** While designed to work fully locally for privacy, the entire project is containerized with Docker Compose, making it trivial to deploy to a VPS, home lab, or cloud environment if you choose to host it centrally for a team.

---

## ✨ Key Features

- **🌐 Multi-Source Feed Ingestion:** Automatically pull in RSS/Atom feeds from various trusted threat intellect sources.
- **🤖 Local LLM Enrichment (Ollama):** Generates single-paragraph summaries, identifies threat types (e.g., ransomware, phishing), and tags affected technologies, completely offline.
- **🧠 Semantic Search (RAG):** Built-in vector database (ChromaDB) to query against historical threat data using natural language queries (e.g., *"recent ransomware targeting healthcare"*).
- **⚙️ Asynchronous Processing:** Uses Celery & Redis to handle article fetching, heavy LLM processing, and text embedding in the background.
- **🐳 Containerized Stack:** Simple one-command deployment using Docker Compose.

---

## 🛠️ Tech Stack

### Backend
- **Framework:** Django & Django REST Framework (DRF)
- **Database:** PostgreSQL
- **Background Tasks:** Celery + Redis
- **AI / LLM Integration:** Ollama (Local Models), ChromaDB (Vector DB)

### Frontend
- **Framework:** React + Vite
- **Routing:** React Router
- **HTTP Client:** Axios

### DevOps
- **Containerization:** Docker & Docker Compose
- **Dependency Management:** Poetry & npm (and pnpm)

---

## 🏗️ Architecture Flow

1. **Ingest:** A recurring Celery task attempts to fetch RSS feeds.
2. **Store:** Articles are deduplicated and saved into PostgreSQL.
3. **Enrich:** Asynchronous task triggers an Ollama model (e.g., Mistral/Llama) to parse, summarize, and categorize the article text.
4. **Embed:** Post-enrichment, text is vectorized and embedded into ChromaDB for semantic search.
5. **Serve:** React dashboard & comprehensive REST APIs expose the data so security analysts can easily browse, filter, or chat with their aggregated intelligence.

---

## 🚀 Getting Started

### Prerequisites

Before starting, ensure you have the following installed:
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Ollama](https://ollama.com/) (running locally on your host machine)

**1. Set up Ollama**
Ensure your local Ollama instance is up and running, then pull your desired model (e.g., `mistral` or `llama3`):
```bash
ollama pull mistral
```

**2. Clone the Repository**
```bash
git clone https://github.com/yourusername/AI-powered-threat-intelligence-aggregator.git
cd AI-powered-threat-intelligence-aggregator
```

**3. Environment Variables**
Copy the sample environment configuration:
```bash
cp .env.example .env
```
*(Optionally modify the `.env` file to customize database credentials or pointing the Ollama host if it does not reside on standard `localhost:11434`)*

### Quick Start with Docker

Run the complete stack with a single command:
```bash
docker compose up --build
```

**What happens?**
- Django API binds to `http://localhost:8000`
- React Frontend binds to `http://localhost:5173`
- PostgreSQL & Redis boot up and wire themselves automatically to the background Celery workers.
- **Auto-Initialization:** If the database is empty on the first run, the backend will automatically migrate and run the `fetch_feed` and `enrich_articles` background tasks.

---

## 💡 Usage Examples

### REST API

The Django backend exposes various endpoints for consuming or managing intelligence.

**Search via Vector/RAG query:**
```bash
curl "http://localhost:8000/api/articles/search/?q=ransomware attacks on healthcare"
```

**Filtering with standard parameters:**
```bash
curl "http://localhost:8000/api/articles/search/?q=critical&severity=critical&limit=5"
```

### Administrative Commands

You can manually trigger specific pipelines through `manage.py` (either locally via Poetry or within the Django container):

```bash
# Force a feed refresh
python manage.py fetch_feed

# Embed enriched articles into the Vector Database
python manage.py embed_articles --enriched-only

# View Vector Database Statistics
curl "http://localhost:8000/api/articles/vector-stats/"
```

---

## 🗺️ Roadmap & Future Enhancements

The platform is designed in iterative phases. Here is what is on the horizon:

- [ ] **Advanced Frontend Dashboard:** Complete the React-based UI to feature graphical timelines, advanced multi-tag filtering, and deep-dive views on specific IOCs.
- [ ] **Production Deployment Patterns:** Helm charts and Kubernetes manifests for enterprise-scale deployments.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
Feel free to check the [issues page](https://github.com/yourusername/AI-powered-threat-intelligence-aggregator/issues) if you want to contribute.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPLv3) - see the `LICENSE` file for details. This means you are free to use, modify, and distribute this software, but any derivative works must also be open source and licensed under GPLv3.

---

> Built with 💻 by [JM Aguero](https://github.com/yourusername)
