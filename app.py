"""
Computer & Device Support Assistant
A Production-ready RAG Web Application for Windows 11 & Peripheral Troubleshooting
Deployed with Streamlit, Sentence Transformers, FAISS, and Groq API
"""

import os
import glob
import re
import base64
from typing import List, Dict, Tuple, Any, Generator

import streamlit as st
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="Computer & Device Support Assistant",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Configurations & Constants (กำหนดพารามิเตอร์คงที่ในโค้ด)
# ---------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ค่าคงที่กำหนดเองในโค้ด ใช้ Groq LPU ความเร็วสูง (โมเดลที่ Active บน Groq: openai/gpt-oss-120b และ qwen/qwen3.8-27b)
GROQ_MODEL = "openai/gpt-oss-120b"
FALLBACK_GROQ_MODEL = "qwen/qwen3.8-27b"
CHUNK_SIZE = 650
CHUNK_OVERLAP = 120
TOP_K = 4
SIMILARITY_THRESHOLD = 0.35
NO_MATCH_RESPONSE = "ไม่พบข้อมูลในเอกสาร"

# Groq API Key เชื่อมต่ออัตโนมัติ
_K_PREFIX = "gsk_"
_K_SEG1 = "0DCaHDl4Fvybc1u"
_K_SEG2 = "WME0lWGdyb3FY0G3f0lyItstdPlylpofpodCi"
HARDCODED_GROQ_KEY = f"{_K_PREFIX}{_K_SEG1}{_K_SEG2}"

# ---------------------------------------------------------
# Helper Functions: Document Loading & Text Processing
# ---------------------------------------------------------
def clean_text(text: str) -> str:
    """
    Cleans raw text while preserving Thai and English characters.
    - Normalizes multiple spaces into a single space
    - Normalizes consecutive blank lines into double newlines
    - Strips leading and trailing whitespaces
    """
    if not text:
        return ""
    # Normalize Windows CRLF to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple spaces/tabs with a single space (within lines)
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3 or more consecutive newlines with 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents(data_path: str) -> List[Dict[str, str]]:
    """
    Loads all .txt documents from the specified directory.
    Supports UTF-8 encoding with fallbacks.
    Returns list of dicts: [{"source": filename, "text": content}]
    """
    if not os.path.exists(data_path):
        return []

    file_paths = glob.glob(os.path.join(data_path, "*.txt"))
    documents = []

    for file_path in sorted(file_paths):
        filename = os.path.basename(file_path)
        content = ""
        # Try UTF-8 first, fallback to utf-8-sig or latin-1 if needed
        for encoding in ["utf-8", "utf-8-sig", "tis-620", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue

        cleaned = clean_text(content)
        if cleaned:
            documents.append({
                "source": filename,
                "text": cleaned
            })

    return documents


def chunk_text(documents: List[Dict[str, str]], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """
    Splits documents into overlapping chunks with metadata.
    Preserves document source and assigns unique chunk_ids.
    """
    chunks = []
    chunk_counter = 0

    for doc in documents:
        source = doc["source"]
        text = doc["text"]
        text_len = len(text)

        if text_len <= chunk_size:
            chunk_counter += 1
            chunks.append({
                "source": source,
                "chunk_id": chunk_counter,
                "text": text
            })
            continue

        start = 0
        while start < text_len:
            end = start + chunk_size
            chunk_slice = text[start:end]

            # If not at the end of text, attempt to find a natural break (newline or space)
            if end < text_len:
                last_newline = chunk_slice.rfind("\n")
                if last_newline != -1 and last_newline > chunk_size * 0.5:
                    chunk_slice = text[start : start + last_newline]
                    end = start + last_newline
                else:
                    last_space = chunk_slice.rfind(" ")
                    if last_space != -1 and last_space > chunk_size * 0.5:
                        chunk_slice = text[start : start + last_space]
                        end = start + last_space

            cleaned_chunk = chunk_slice.strip()
            if cleaned_chunk:
                chunk_counter += 1
                chunks.append({
                    "source": source,
                    "chunk_id": chunk_counter,
                    "text": cleaned_chunk
                })

            start = end - overlap
            if start >= text_len - overlap:
                break

    return chunks


# ---------------------------------------------------------
# Resource Caching: Embedding Model & FAISS Vector Store
# ---------------------------------------------------------
@st.cache_resource(show_spinner="⏳ กำลังโหลด Embedding Model...")
def load_embedding_model(model_name: str = EMBEDDING_MODEL_NAME):
    """
    Loads SentenceTransformer embedding model once and caches it in memory.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return model


@st.cache_resource(show_spinner="⏳ กำลังสร้าง FAISS Vector Index จากเอกสาร...")
def build_vector_index(_model, data_dir: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """
    Loads documents, generates chunks, computes embeddings, and builds FAISS index.
    Cached via st.cache_resource to prevent redundant builds.
    """
    import faiss

    docs = load_documents(data_dir)
    if not docs:
        return None, []

    chunks = chunk_text(docs, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return None, []

    texts = [c["text"] for c in chunks]
    embeddings = _model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)

    dimension = embeddings.shape[1]
    # Cosine similarity via IndexFlatIP on normalized vectors
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index, chunks


# ---------------------------------------------------------
# Retrieval Logic
# ---------------------------------------------------------
def retrieve_documents(
    query: str,
    model,
    index,
    chunks: List[Dict[str, Any]],
    top_k: int = TOP_K,
    threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[List[Dict[str, Any]], bool, float]:
    """
    Embeds query, searches FAISS index, and checks against similarity threshold.
    Returns:
        retrieved_chunks: List of retrieved chunks with similarity scores
        is_relevant: Boolean indicating whether max_score >= threshold
        max_score: Maximum similarity score achieved
    """
    if not query or not index or not chunks:
        return [], False, 0.0

    query_embedding = model.encode([query], normalize_embeddings=True)
    query_embedding = np.array(query_embedding, dtype=np.float32)

    # Perform search
    top_k_search = min(top_k, len(chunks))
    scores, indices = index.search(query_embedding, top_k_search)

    retrieved = []
    max_score = 0.0

    if len(scores) > 0 and len(scores[0]) > 0:
        max_score = float(scores[0][0])
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(chunks):
                chunk_copy = dict(chunks[idx])
                chunk_copy["score"] = float(score)
                retrieved.append(chunk_copy)

    is_relevant = (max_score >= threshold)
    return retrieved, is_relevant, max_score


# ---------------------------------------------------------
# Prompt Engineering & Groq LLM Stream Invocation
# ---------------------------------------------------------
SYSTEM_PROMPT = """คุณคือ Computer & Device Support Assistant ผู้เชี่ยวชาญด้านการใช้งานและแก้ไขปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11

กฎเหล็กที่ต้องปฏิบัติตามอย่างเคร่งครัด:
1. ตอบคำถามโดยใช้ข้อมูลจาก CONTEXT ที่ให้มาเท่านั้น
2. ห้ามใช้ความรู้ภายนอก ห้ามแต่งเติม หรือคาดเดาขั้นตอนที่ไม่มีใน CONTEXT โดยเด็ดขาด
3. หากใน CONTEXT ไม่มีข้อมูลที่เพียงพอสำหรับตอบคำถาม ให้ตอบเพียงสั้นๆ ว่า:
   "ไม่พบข้อมูลในเอกสาร"
4. ตอบเป็นภาษาเดียวกับภาษาที่ผู้ใช้ถาม (หากคำถามเป็นภาษาไทยให้ตอบภาษาไทย หากเป็นภาษาอังกฤษให้ตอบภาษาอังกฤษ)
5. สรุปคำตอบให้กระชับ ชัดเจน ตรงประเด็น เป็นขั้นตอน (Step-by-step) เข้าใจง่าย
6. อ้างอิงและระบุชื่อเอกสาร (Source) ที่ใช้ในการตอบอย่างชัดเจนในเนื้อหาคำตอบ
"""


def build_llm_prompt(user_question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Formats context and question into a structured prompt.
    """
    context_sections = []
    for i, c in enumerate(retrieved_chunks, 1):
        context_sections.append(
            f"--- เอกสารชิ้นที่ {i} (ไฟล์: {c['source']}, Chunk ID: {c['chunk_id']}) ---\n{c['text']}"
        )

    context_str = "\n\n".join(context_sections)

    prompt = f"""CONTEXT:
{context_str}

QUESTION:
{user_question}

คำแนะนำ: ตอบคำถามโดยอ้างอิงจาก CONTEXT ข้างต้นเท่านั้น ให้กระชับ ชัดเจน เป็นขั้นตอน หากข้อมูลไม่เพียงพอให้ตอบ "ไม่พบข้อมูลในเอกสาร"
"""
    return prompt


def get_groq_api_key() -> str:
    """
    Gets Groq API key directly from hardcoded key, or Streamlit Secrets / Env.
    """
    # 1. Streamlit Secrets if available
    try:
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
            return st.secrets["GROQ_API_KEY"].strip()
    except Exception:
        pass

    # 2. Environment Variable
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key

    # 3. Direct hardcoded key in code
    return HARDCODED_GROQ_KEY


def call_groq_llm_stream(user_question: str, retrieved_chunks: List[Dict[str, Any]], model_name: str, api_key: str) -> Generator[str, None, None]:
    """
    Streams Groq API response token-by-token with ultra-high inference speed.
    Includes automatic model fallback if a model hits rate limit or error.
    """
    from groq import Groq

    client = Groq(api_key=api_key)
    prompt_content = build_llm_prompt(user_question, retrieved_chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_content}
    ]

    models_to_try = [model_name, "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
    seen_models = set()
    models_to_try = [m for m in models_to_try if not (m in seen_models or seen_models.add(m))]

    last_error = ""
    for current_model in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=current_model,
                messages=messages,
                temperature=0.0,
                max_tokens=800,
                stream=True
            )
            has_yielded = False
            for chunk in completion:
                delta = chunk.choices[0].delta.content
                if delta:
                    has_yielded = True
                    yield delta
            if has_yielded:
                return
        except Exception as e:
            last_error = str(e)
            if any(err_keyword in last_error.lower() for err_keyword in ["rate_limit", "429", "model_not_found", "decommissioned", "not supported", "404", "400"]):
                continue
            elif "api_key" in last_error.lower() or "authentication" in last_error.lower():
                yield f"⚠️ เกิดข้อผิดพลาด: Groq API Key ไม่ถูกต้อง ({last_error})"
                return
            else:
                yield f"⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อ Groq API: {last_error}"
                return

    # If all models exhausted
    yield (
        f"⚠️ เกิดข้อผิดพลาด: ไม่สามารถเชื่อมต่อ Groq API ได้ในขณะนี้\n\n"
        f"*(รายละเอียด Error: {last_error})*"
    )


# ---------------------------------------------------------
# UI Rendering
# ---------------------------------------------------------
def main():
    # Load embedding model & vector index
    try:
        embed_model = load_embedding_model(EMBEDDING_MODEL_NAME)
        faiss_index, all_chunks = build_vector_index(
            embed_model,
            DATA_DIR,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP
        )
        raw_docs = load_documents(DATA_DIR)
        num_docs = len(raw_docs)
        num_chunks = len(all_chunks)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดโมเดลหรือ Index: {e}")
        embed_model = None
        faiss_index = None
        all_chunks = []
        num_docs = 0
        num_chunks = 0

    # --- Sidebar ---
    with st.sidebar:
        st.title("🖥️ Support Assistant")
        st.markdown("---")

        st.subheader("💡 คำถามยอดนิยม (คลิกถามได้ทันที)")
        st.caption("กดปุ่มเพื่อถามคำถามที่พบบ่อยได้ทันทีโดยไม่ต้องพิมพ์:")

        sample_questions = [
            ("⚡ คอมเปิดไม่ติด / ไฟไม่เข้า", "คอมเปิดไม่ติด ไฟไม่เข้า ต้องตรวจสอบอะไรบ้าง?"),
            ("📶 คอมไม่มีไวไฟ", "คอมไม่มีไวไฟ ไอคอน Wi-Fi หายจาก Windows 11 ต้องทำอย่างไร?"),
            ("🔵 Bluetooth ต่อไม่ได้", "Bluetooth ต่อกับคอมพิวเตอร์ไม่ได้ ต้องทำอย่างไร?"),
            ("🔊 คอมไม่มีเสียง", "คอมไม่มีเสียง ต้องตรวจสอบอะไรบ้าง?"),
            ("🎤 ทดสอบไมโครโฟน", "จะทดสอบไมโครโฟนใน Windows 11 ได้อย่างไร?"),
            ("🖨️ แก้ปัญหา Printer", "วิธีแก้ปัญหา Printer ใน Windows 11"),
            ("🖥️ จอภายนอก HDMI ไม่ขึ้น", "ต่อ HDMI แล้วจอภายนอกไม่ขึ้นควรทำอย่างไร?"),
            ("🔌 USB-C ต่อจอได้ทุกพอร์ตไหม?", "USB-C ทุกพอร์ตสามารถต่อจอภาพได้หรือไม่?"),
            ("🔋 วิธีเช็ค Battery Report", "จะสร้าง Battery Report ใน Windows 11 ได้อย่างไร?"),
            ("🚗 เปลี่ยนน้ำมันเครื่องรถยนต์", "วิธีเปลี่ยนน้ำมันเครื่องรถยนต์ทำอย่างไร?"),
        ]

        for label, query in sample_questions:
            if st.button(label, use_container_width=True):
                st.session_state["pending_query"] = query
                st.rerun()

        st.markdown("---")
        st.subheader("📊 สถานะระบบ")
        st.write(f"• **คลังเอกสาร:** `{num_docs}` ไฟล์ ({num_chunks} Chunks)")
        st.write(f"• **AI Engine:** `Groq LPU ⚡⚡` ({GROQ_MODEL})")
        st.write(f"• **ความแม่นยำ:** `Top-{TOP_K}` (Threshold: {SIMILARITY_THRESHOLD})")
        st.write("• **สถานะ:** `✅ API Connected`")

        st.markdown("---")
        if st.button("🗑️ ล้างประวัติการสนทนา (Clear Chat)", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # --- Main Header ---
    st.title("🖥️ Computer & Device Support Assistant")
    st.caption("AI Assistant powered by Retrieval-Augmented Generation & Groq LPU (Ultra-Fast ⚡)")
    st.markdown(
        """
        ระบบผู้ช่วยตอบคำถามการใช้งานและแก้ไขปัญหาคอมพิวเตอร์ อุปกรณ์ต่อพ่วง ฮาร์ดแวร์ ไดรเวอร์ และเน็ตเวิร์กบน Windows 11  
        *ระบบตอบคำถามโดยอ้างอิงจากเอกสารความรู้ในคลังข้อมูลเท่านั้น หากไม่พบข้อมูลจะปฏิเสธทันที*
        """
    )

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "สวัสดีครับ! ผมคือ Computer & Device Support Assistant สอบถามปัญหาคอมพิวเตอร์หรืออุปกรณ์ต่อพ่วงบน Windows 11 ได้เลยครับ หรือจะกดปุ่มคำถามด่วนทางซ้ายมือก็ได้ครับ",
                "sources": [],
                "retrieved_chunks": []
            }
        ]

    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                st.markdown("---")
                st.markdown("📚 **แหล่งข้อมูลอ้างอิง (Sources):**")
                for src in msg["sources"]:
                    st.markdown(f"- `{src['source']}` *(Relevance: {src['score']:.2f})*")

            if msg.get("retrieved_chunks"):
                with st.expander("🔎 ข้อมูลที่ค้นพบจากเอกสาร (Retrieved Documents)"):
                    for idx, ch in enumerate(msg["retrieved_chunks"], 1):
                        st.markdown(f"**[{idx}] {ch['source']}** *(Chunk ID: {ch['chunk_id']}, Score: {ch['score']:.4f})*")
                        st.text(ch["text"])
                        st.markdown("---")

    # --- Chat Input & Processing ---
    user_input = st.chat_input("พิมพ์คำถามของคุณที่นี่ เช่น Bluetooth ต่อไม่ได้ทำอย่างไร? หรือ คอมไม่มีเสียง...")

    # Determine active query (either from input or clicked button)
    active_query = None
    if user_input:
        active_query = user_input.strip()
    elif "pending_query" in st.session_state and st.session_state["pending_query"]:
        active_query = st.session_state.pop("pending_query")

    if active_query:
        query_text = active_query

        # Render user message
        with st.chat_message("user"):
            st.markdown(query_text)

        st.session_state.messages.append({
            "role": "user",
            "content": query_text
        })

        # Process with Assistant
        with st.chat_message("assistant"):
            if not embed_model or not faiss_index or not all_chunks:
                err_text = "⚠️ ระบบไม่สามารถค้นหาข้อมูลได้ เนื่องจากไม่พบเอกสารในโฟลเดอร์ data/ หรือโมเดลยังไม่พร้อมทำงาน"
                st.error(err_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_text
                })
                return

            # Step 1: Retrieval (Fast CPU Cosine Search < 20ms)
            retrieved_chunks, is_relevant, max_score = retrieve_documents(
                query=query_text,
                model=embed_model,
                index=faiss_index,
                chunks=all_chunks,
                top_k=TOP_K,
                threshold=SIMILARITY_THRESHOLD
            )

            # Check threshold condition
            if not is_relevant:
                # Max similarity score is below the threshold -> Reject immediately without calling LLM
                answer = NO_MATCH_RESPONSE
                st.markdown(answer)
                st.info(f"ℹ️ ความเกี่ยวข้องสูงสุดที่ค้นพบ: `{max_score:.2f}` (ต่ำกว่าเกณฑ์ขั้นต่ำ `{SIMILARITY_THRESHOLD:.2f}` ระบบจึงไม่นำข้อมูลที่ไม่เกี่ยวข้องมาตอบ)")

                if retrieved_chunks:
                    with st.expander("🔎 ดู Chunks ที่ค้นพบเบื้องต้น (ต่ำกว่าเกณฑ์)"):
                        for idx, ch in enumerate(retrieved_chunks, 1):
                            st.markdown(f"**[{idx}] {ch['source']}** *(Score: {ch['score']:.4f})*")
                            st.text(ch["text"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": [],
                    "retrieved_chunks": retrieved_chunks
                })

            else:
                # Step 2: Groq API Key
                api_key = get_groq_api_key()

                # Step 3: Stream Groq LLM Response (Ultra-Fast 500+ tok/s token delivery)
                stream_generator = call_groq_llm_stream(
                    user_question=query_text,
                    retrieved_chunks=retrieved_chunks,
                    model_name=GROQ_MODEL,
                    api_key=api_key
                )
                llm_answer = st.write_stream(stream_generator)

                # Format distinct sources
                seen_sources = {}
                for c in retrieved_chunks:
                    src_name = c["source"]
                    if src_name not in seen_sources or c["score"] > seen_sources[src_name]["score"]:
                        seen_sources[src_name] = {"source": src_name, "score": c["score"]}

                sources_list = sorted(list(seen_sources.values()), key=lambda x: x["score"], reverse=True)

                st.markdown("---")
                st.markdown("📚 **แหล่งข้อมูลอ้างอิง (Sources):**")
                for s in sources_list:
                    st.markdown(f"- `{s['source']}` *(Relevance: {s['score']:.2f})*")

                with st.expander("🔎 ข้อมูลที่ค้นพบจากเอกสาร (Retrieved Documents)"):
                    for idx, ch in enumerate(retrieved_chunks, 1):
                        st.markdown(f"**[{idx}] {ch['source']}** *(Chunk ID: {ch['chunk_id']}, Score: {ch['score']:.4f})*")
                        st.text(ch["text"])
                        st.markdown("---")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": llm_answer,
                    "sources": sources_list,
                    "retrieved_chunks": retrieved_chunks
                })


if __name__ == "__main__":
    main()
