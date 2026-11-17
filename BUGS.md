## Guardrails Integration: Root Cause Analysis & Fixes

### 1. Root Cause Analysis

The application returned `"No response."` due to failures across the Guardrails engine, FastAPI backend, and Streamlit frontend.

**Issue 1: Inaccessible Groq Model (`app/guardrails/rails.py`)**

- The Guardrails engine used a hardcoded model: `llama-3.1-8b-instant`.
- Groq returned a `404 model_not_found` error because the model was inaccessible.
- Updated the configuration to use `settings.GROQ_MODEL`.

**Issue 2: Unhandled Backend Exception (`app/main.py`)**

- Guardrails failures caused FastAPI to return HTTP 500.
- The frontend received an error response without an `answer` field.

**Issue 3: Missing UI Error Handling (`Ui/app.py`)**

- Streamlit did not validate HTTP response status codes.
- Missing `answer` fields silently displayed `"No response."`.

### 2. Guardrails Detection Logic

The original implementation relied on five exact response phrases to identify triggered guardrails.

```python
fired = any(indicator in content for indicator in RAIL_INDICATORS)
```

This failed when NeMo Guardrails generated dynamically worded refusal messages.

**Improvements:**

- Added case-insensitive matching.
- Expanded `RAIL_INDICATORS` with common refusal phrases.
- Added lifestyle and food-related off-topic examples to Colang rules.
- Improved detection of dynamically generated refusal responses.

### 3. Implemented Changes

| File                             | Changes                                                                           |
| -------------------------------- | --------------------------------------------------------------------------------- |
| `app/guardrails/rails.py`        | Replaced hardcoded model, added case-insensitive matching and exception handling. |
| `app/guardrails/colang_rules.py` | Expanded refusal indicators and added off-topic examples.                         |
| `Ui/app.py`                      | Added HTTP status validation and backend error handling.                          |
| `app/agents/nodes/responder.py`  | Added enterprise-domain restrictions for conversational responses.                |

### 4. Verification Results

| Test Query                   | Expected Behavior        | Result |
| ---------------------------- | ------------------------ | ------ |
| How to make coffee           | Blocked by guardrails    | PASS   |
| Tell me a joke               | Blocked by guardrails    | PASS   |
| Who won the World Cup?       | Blocked by guardrails    | PASS   |
| Hi                           | Direct greeting response | PASS   |
| What is a Kubernetes Pod?    | Passed to RAG pipeline   | PASS   |
| Explain SR-IOV on Intel NICs | Passed to RAG pipeline   | PASS   |

### 5. Final API Response

**Example: Off-topic query — `how to make coffee`**

```json
{
  "question": "how to make coffee",
  "answer": "I specialize in Enterprise IT topics such as Kubernetes, Intel hardware, and enterprise networking. I cannot assist with questions about making coffee. How can I help you with your IT infrastructure today?",
  "thought_process": ["Intent: Guardrails Fired", "Retrieval: Skipped"],
  "status": "Handled by guardrails.",
  "sources": []
}
```

### 6. Final Outcome

- Fixed Groq model configuration.
- Improved NeMo Guardrails refusal detection.
- Prevented off-topic queries from reaching the RAG pipeline.
- Added error handling across FastAPI and Streamlit.
- Implemented defense-in-depth domain restrictions in the conversational responder.
- Verified that technical queries continue through the LangGraph RAG pipeline successfully.

**Status:** Successfully implemented and verified.
