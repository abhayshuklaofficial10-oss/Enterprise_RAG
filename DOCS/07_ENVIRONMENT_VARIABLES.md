# 🔑 Environment Variables & Configuration

The project uses a `.env` file for configuration. All configuration is centralized in `app/config.py`.

---

## 🧠 AI & LLM (The Brain)
| Variable | Description | Example |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Key for Llama 3.3 models | `gsk_...` |
| `GROQ_MODEL` | Specific model version | `llama-3.3-70b-versatile` |
| `GROQ_FALLBACK_API_KEY` | Backup Groq key for fallback | `gsk_...` |
| `PORTKEY_API_KEY` | Portkey Gateway API key | `pk_...` |
| `PORTKEY_CONFIG_ID` | Portkey routing config ID | `pc-...` |

## 📐 Embeddings
| Variable | Description | Default |
| :--- | :--- | :--- |
| `EMBEDDING_MODEL_NAME` | Local SentenceTransformers model | `all-MiniLM-L6-v2` |

## 🗄️ Vector Database (Qdrant)
| Variable | Description | Example |
| :--- | :--- | :--- |
| `QDRANT_CLUSTER_ENDPOINT` | Cloud / Local Qdrant Endpoint | `https://...` |
| `QDRANT_API_KEY` | Qdrant Access Token | `xyz...` |

## 🕵️ Observability (The Vision)
| Variable | Description | Example |
| :--- | :--- | :--- |
| `LOGFIRE_TOKEN` | Token for system tracing | `pylf_...` |
| `LANGSMITH_API_KEY` | Token for agent logic tracing | `lsv2_...` |
| `LANGSMITH_TRACING` | Enable LangSmith tracing | `true` |
| `LANGSMITH_PROJECT` | LangSmith project name | `enterprise_rag` |

---

## 🔒 Security Best Practices
1.  **Never** commit your `.env` file to Git.
2.  In **Cloud Run**, use the "Variables & Secrets" tab to inject these values at runtime.
3.  Use the `commands_example.md` as a template when setting up a new developer environment.
