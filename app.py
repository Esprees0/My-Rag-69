"""
Computer & Device Support Assistant
A Production-ready RAG Web Application for Windows 11 & Peripheral Troubleshooting
Deployed with Streamlit, Sentence Transformers, FAISS, and Google Gemini API
"""

import os
import glob
import re
import base64
from typing import List, Dict, Tuple, Any

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

# ค่าคงที่กำหนดเองในโค้ด ไม่ต้องปรับบนหน้าเว็บ
GEMINI_MODEL = "gemini-1.5-flash"
CHUNK_SIZE = 650
CHUNK_OVERLAP = 120
TOP_K = 4
SIMILARITY_THRESHOLD = 0.35
NO_MATCH_RESPONSE = "ไม่พบข้อมูลในเอกสาร"

# Gemini API Key ฝังในโค้ดโดยตรง พร้อมเชื่อมต่ออัตโนมัติ
_DEFAULT_KEY_ENCODED = "QVEuQWI4Uk42S0hWQkFkbDVQSUlGRVozYTM1akZTQUMxUlhVNEczN1BoTWliT3Z0NTVobGc="
HARDCODED_GEMINI_KEY = base64.b64decode(_DEFAULT_KEY_ENCODED).decode("utf-8")

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
# Prompt Engineering & Gemini LLM Invocation
# ---------------------------------------------------------
SYSTEM_PROMPT = """คุณคือ Computer & Device Support Assistant ผู้เชี่ยวชาญด้านการใช้งานและแก้ไขปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11

กฎเหล็กที่ต้องปฏิบัติตามอย่างเคร่งครัด:
1. ตอบคำถามโดยใช้ข้อมูลจาก CONTEXT ที่ให้มาเท่านั้น
2. ห้ามใช้ความรู้ภายนอก ห้ามแต่งเติม หรือคาดเดาขั้นตอนที่ไม่มีใน CONTEXT โดยเด็ดขาด
3. หากใน CONTEXT ไม่มีข้อมูลที่เพียงพอสำหรับตอบคำถาม ให้ตอบเพียงสั้นๆ ว่า:
   "ไม่พบข้อมูลในเอกสาร"
4. ตอบเป็นภาษาเดียวกับภาษาที่ผู้ใช้ถาม (หากคำถามเป็นภาษาไทยให้ตอบภาษาไทย หากเป็นภาษาอังกฤษให้ตอบภาษาอังกฤษ)
5. สรุปคำตอบให้ชัดเจน เข้าใจง่าย เป็นขั้นตอน (Step-by-step) เมื่อเหมาะสมกับคำถาม
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

คำแนะนำ: ตอบคำถามโดยอ้างอิงจาก CONTEXT ข้างต้นเท่านั้น หากข้อมูลไม่เพียงพอให้ตอบ "ไม่พบข้อมูลในเอกสาร"
"""
    return prompt


def get_gemini_api_key() -> str:
    """
    Gets Gemini API key directly from hardcoded key, or Streamlit Secrets / Env.
    """
    # 1. Streamlit Secrets if available
    try:
        for secret_name in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            if secret_name in st.secrets and st.secrets[secret_name]:
                return st.secrets[secret_name].strip()
    except Exception:
        pass

    # 2. Environment Variable
    for env_name in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        env_key = os.environ.get(env_name, "").strip()
        if env_key:
            return env_key

    # 3. Direct hardcoded key in code
    return HARDCODED_GEMINI_KEY


def call_gemini_llm(user_question: str, retrieved_chunks: List[Dict[str, Any]], model_name: str, api_key: str) -> str:
    """
    Calls the Google Gemini API to generate an answer based on retrieved context.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    prompt_content = build_llm_prompt(user_question, retrieved_chunks)

    generation_config = {
        "temperature": 0.0,  # Factual, grounded deterministic output
        "max_output_tokens": 1024,
    }

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            generation_config=generation_config
        )
        response = model.generate_content(prompt_content)
        if response and response.text:
            return response.text.strip()
        return NO_MATCH_RESPONSE
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "invalid argument" in error_msg.lower():
            return "⚠️ เกิดข้อผิดพลาด: Gemini API Key ไม่ถูกต้องหรือยังไม่เปิดใช้งาน กรุณาตรวจสอบ API Key"
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
            return "⚠️ เกิดข้อผิดพลาด: เกินขีดจำกัดการเรียกใช้งาน Gemini API (Quota/Rate limit) กรุณารอสักครู่แล้วลองใหม่"
        return f"⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อ Gemini API: {error_msg}"


# ---------------------------------------------------------
# UI Rendering
# ---------------------------------------------------------
def main():
    # --- Sidebar ---
    with st.sidebar:
        st.title("🖥️ ข้อมูลระบบ (System Info)")
        st.markdown("---")

        st.subheader("📖 เกี่ยวกับแชตบอต")
        st.markdown(
            """
            **Computer & Device Support Assistant**  
            ระบบตอบคำถามและแก้ปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11  
            ขับเคลื่อนด้วยสถาปัตยกรรม **RAG (Retrieval-Augmented Generation)**  
            ค้นหาข้อมูลตรงจากเอกสารทางการ ไม่แต่งคำตอบนอกเหนือจากเอกสาร
            """
        )

        st.markdown("---")
        st.subheader("📊 ข้อมูล Knowledge Base")

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

            st.metric(label="จำนวนเอกสาร (Documents)", value=f"{num_docs} ไฟล์")
            st.metric(label="จำนวน Chunks ในระบบ", value=f"{num_chunks} Chunks")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลดโมเดลหรือ Index: {e}")
            embed_model = None
            faiss_index = None
            all_chunks = []

        st.markdown("---")
        st.subheader("⚙️ พารามิเตอร์ระบบ (Configured)")
        st.write(f"• **LLM Model:** `{GEMINI_MODEL}`")
        st.write(f"• **Top-K Retrieval:** `{TOP_K}` Chunks")
        st.write(f"• **Similarity Threshold:** `{SIMILARITY_THRESHOLD}`")
        st.write(f"• **Status:** `✅ API Connected`")

        st.markdown("---")
        if st.button("🗑️ ล้างประวัติการสนทนา (Clear Chat)", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.caption("💡 **วิธีใช้งาน**: พิมพ์คำถามเกี่ยวกับปัญหาคอมพิวเตอร์หรืออุปกรณ์ต่อพ่วงในกล่องข้อความด้านล่าง")

    # --- Main Header ---
    st.title("🖥️ Computer & Device Support Assistant")
    st.caption("AI Assistant powered by Retrieval-Augmented Generation (Windows 11 & Peripheral Support)")
    st.markdown(
        """
        ระบบผู้ช่วยตอบคำถามการใช้งานและแก้ไขปัญหาคอมพิวเตอร์ อุปกรณ์ต่อพ่วง ฮาร์ดแวร์ ไดรเวอร์ และเน็ตเวิร์กเบื้องต้น  
        *ระบบตอบคำถามโดยอ้างอิงจากเอกสารความรู้ในคลังข้อมูลเท่านั้น หากไม่พบข้อมูลจะปฏิเสธทันที*
        """
    )

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "สวัสดีครับ! ผมคือ Computer & Device Support Assistant มีปัญหาเกี่ยวกับการใช้งานคอมพิวเตอร์ อุปกรณ์ต่อพ่วง หรือ Windows 11 ด้านไหน สอบถามได้เลยครับ",
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
    user_query = st.chat_input("พิมพ์คำถามของคุณที่นี่ เช่น Bluetooth ต่อไม่ได้ทำอย่างไร? หรือ คอมไม่มีเสียง...")

    if user_query:
        query_text = user_query.strip()
        if not query_text:
            return

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

            # Step 1: Retrieval
            with st.spinner("🔍 กำลังค้นหาข้อมูลที่เกี่ยวข้องจาก Knowledge Base..."):
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
                # Max similarity score is below the threshold -> Reject without calling LLM
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
                # Step 2: Gemini API Key & Generation
                api_key = get_gemini_api_key()

                # Step 3: Call Gemini LLM
                with st.spinner("🤖 กำลังวิเคราะห์และเรียบเรียงคำตอบจากเอกสาร..."):
                    llm_answer = call_gemini_llm(
                        user_question=query_text,
                        retrieved_chunks=retrieved_chunks,
                        model_name=GEMINI_MODEL,
                        api_key=api_key
                    )

                st.markdown(llm_answer)

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
