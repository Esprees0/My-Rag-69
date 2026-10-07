# 🖥️ Computer & Device Support Assistant

AI Assistant powered by Retrieval-Augmented Generation (RAG) สำหรับตอบคำถามและแก้ไขปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วงเบื้องต้นบน Windows 11 ขับเคลื่อนด้วย Google Gemini API พร้อมรองรับการ Deploy บน Streamlit Community Cloud

---

## 📌 1. Project Description (คำอธิบายโครงการ)

**Computer & Device Support Assistant** คือ Web Application Chatbot ที่พัฒนาด้วยสถาปัตยกรรม **Retrieval-Augmented Generation (RAG)** มีวัตถุประสงค์เพื่อช่วยผู้ใช้งานแก้ปัญหาคอมพิวเตอร์ ฮาร์ดแวร์ ไดรเวอร์ และอุปกรณ์ต่อพ่วงต่าง ๆ บนระบบปฏิบัติการ Windows 11 ได้อย่างถูกต้อง รวดเร็ว และเชื่อถือได้

ระบบทำงานโดยยึดหลัก **Grounded Generation**:
- ค้นหาข้อมูลจากเอกสารทางการในคลังความรู้ (`data/`) เท่านั้น
- **ห้าม LLM แต่งเติมคำตอบหรือใช้ความรู้ทั่วไปนอกเหนือจากเอกสาร**
- เมื่อระบบค้นหาแล้วไม่พบข้อมูลที่เกี่ยวข้องเพียงพอ จะปฏิเสธคำถามทันทีด้วยข้อความ:  
  **"ไม่พบข้อมูลในเอกสาร"**
- แสดงแหล่งที่มาของเอกสาร (Source citation) และคะแนนความเกี่ยวข้อง (Relevance score) ทุกครั้ง

---

## ✨ 2. Key Features (คุณสมบัติเด่น)

1. **Dynamic Document Loading**: โหลดเอกสาร `.txt` ทุกไฟล์ในโฟลเดอร์ `data/` รองรับ UTF-8 สามารถเพิ่มเอกสารใหม่ได้ทันทีโดยไม่ต้องแก้ไขซอร์สโค้ด
2. **Text Cleaning & Preprocessing**: ทำความสะอาดข้อความ ปรับแก้ Whitespace และบรรทัดว่างซ้ำซ้อน โดยคงเนื้อหาทั้งภาษาไทยและภาษาอังกฤษครบถ้วน
3. **Smart Chunking**: แบ่งท่อนข้อความแบบ Sliding Window พร้อม Context Overlap เพื่อรักษาความต่อเนื่องของบริบท และเก็บ Metadata ราย Chunk
4. **Multilingual Sentence Embedding**: ใช้โมเดล `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` รองรับการประมวลผลภาษาไทยและอังกฤษ มีขนาดกะทัดรัด ประหยัด RAM เหมาะกับ Cloud ทรัพยากรจำกัด
5. **FAISS Vector Search**: จัดทำดัชนีเวกเตอร์แบบ `IndexFlatIP` พร้อม Normalized Vectors เพื่อคำนวณ Cosine Similarity ได้อย่างแม่นยำและรวดเร็ว
6. **Strict Retrieval Threshold**: กรองคำถามด้วย Similarity Threshold หากคะแนนความเกี่ยวข้องต่ำกว่าเกณฑ์ จะไม่ส่งไปยัง LLM ช่วยประหยัด Token และป้องกันการหลอนคำตอบ (Hallucination)
7. **Prompt Engineering & Google Gemini LLM**: ออกแบบ System Prompt เข้มงวด เรียกใช้งาน LLM ผ่าน Google Gemini API (เช่น `gemini-1.5-flash`)
8. **Interactive Streamlit UI**: หน้าจอแชตสวยงาม มีระบบเก็บประวัติการสนทนา (Chat History), แสดงแหล่งข้อมูลอ้างอิง, แสดง Chunks ที่ค้นพบใน Expander และแผงควบคุมใน Sidebar

---

## 🏗️ 3. RAG Pipeline Architecture

```text
       [ เอกสารใน data/*.txt ]
                 │
                 ▼
       [ Document Loading ] (UTF-8, Metadata extraction)
                 │
                 ▼
       [ Text Cleaning ] (Normalize spaces & newlines)
                 │
                 ▼
       [ Chunking ] (chunk_size: 650 chars, overlap: 120 chars)
                 │
                 ▼
       [ Sentence Embedding ] (paraphrase-multilingual-MiniLM-L12-v2)
                 │
                 ▼
       [ FAISS Vector Index ] (IndexFlatIP / Cosine Similarity)
                 │
   ────────────────────────────────────────────────────────
                 │
       [ คำถามจากผู้ใช้ (User Query) ]
                 │
                 ▼
       [ Query Embedding ]
                 │
                 ▼
       [ Vector Search (Top-K = 4) ]
                 │
                 ▼
         { ตรวจสอบ Threshold } ── (Score < 0.35) ──► "ไม่พบข้อมูลในเอกสาร"
                 │                                        (ไม่เรียก LLM)
            (Score >= 0.35)
                 │
                 ▼
       [ Context Injection & Strict System Prompt ]
                 │
                 ▼
       [ Google Gemini API ] (gemini-1.5-flash)
                 │
                 ▼
   [ คำตอบที่ถูกต้อง + แหล่งอ้างอิง (Sources) ]
```

---

## 🎯 4. Domain & Knowledge Sources

### ทำไมจึงเลือก Computer & Device Support?
ปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วง เช่น หูฟังไม่ได้ยินเสียง, Wi-Fi หลุด, Bluetooth หาไม่เจอ, จอภายนอกไม่ติด, หรือ USB-C ไม่ชาร์จ เป็นปัญหาที่ผู้ใช้ทั่วไปพบเจอทุกวัน การค้นหาผ่าน Search Engine ทั่วไปมักเจอบทความยาวหรือขั้นตอนที่ซับซ้อนเกินไป การใช้ RAG ช่วยให้ผู้ใช้ได้รับคำตอบเป็นขั้นตอนที่สั้น ตรงจุด และเชื่อถือได้

### แหล่งข้อมูลเอกสาร (Knowledge Base)
เอกสารในโฟลเดอร์ `data/` ประกอบด้วย 12 หัวข้อหลัก เรียบเรียงจากเอกสารสนับสนุนทางเทคนิคของ **Microsoft Support** และคู่มือผู้ผลิต:
1. `01_windows11_basic.txt`: การตรวจสอบระบบและ Windows Update
2. `02_wifi_troubleshooting.txt`: การแก้ปัญหาเครือข่ายและ Wi-Fi
3. `03_bluetooth.txt`: การเชื่อมต่อและแก้ปัญหา Bluetooth
4. `04_audio.txt`: ปัญหาเสียง ลำโพง และการตั้งค่า Output Device
5. `05_microphone_headset.txt`: ปัญหาไมโครโฟนและชุดหูฟัง
6. `06_printer.txt`: การติดตั้งและแก้ปัญหาเครื่องพิมพ์
7. `07_external_monitor.txt`: การต่อจอภายนอกผ่าน HDMI / DisplayPort
8. `08_usb_usbc.txt`: ฟังก์ชันและการแก้ปัญหาพอร์ต USB และ USB-C
9. `09_device_manager_driver.txt`: การใช้งาน Device Manager และแก้ไข Driver
10. `10_storage_disk.txt`: การจัดการพื้นที่ฮาร์ดดิสก์และไดรฟ์ C
11. `11_mouse_keyboard.txt`: ปัญหาเมาส์และคีย์บอร์ด
12. `12_battery_power.txt`: การจัดการพลังงานและสร้าง Battery Report

---

## 📝 5. Prompt Engineering

ระบบใช้ System Prompt ที่กำหนดกฎเหล็กอย่างเข้มงวด:

```text
คุณคือ Computer & Device Support Assistant ผู้เชี่ยวชาญด้านการใช้งานและแก้ไขปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11

กฎเหล็กที่ต้องปฏิบัติตามอย่างเคร่งครัด:
1. ตอบคำถามโดยใช้ข้อมูลจาก CONTEXT ที่ให้มาเท่านั้น
2. ห้ามใช้ความรู้ภายนอก ห้ามแต่งเติม หรือคาดเดาขั้นตอนที่ไม่มีใน CONTEXT โดยเด็ดขาด
3. หากใน CONTEXT ไม่มีข้อมูลที่เพียงพอสำหรับตอบคำถาม ให้ตอบเพียงสั้นๆ ว่า:
   "ไม่พบข้อมูลในเอกสาร"
4. ตอบเป็นภาษาเดียวกับภาษาที่ผู้ใช้ถาม (หากคำถามเป็นภาษาไทยให้ตอบภาษาไทย หากเป็นภาษาอังกฤษให้ตอบภาษาอังกฤษ)
5. สรุปคำตอบให้ชัดเจน เข้าใจง่าย เป็นขั้นตอน (Step-by-step) เมื่อเหมาะสมกับคำถาม
6. อ้างอิงและระบุชื่อเอกสาร (Source) ที่ใช้ในการตอบอย่างชัดเจนในเนื้อหาคำตอบ
```

---

## ☁️ 6. Streamlit Community Cloud Deployment Guide (วิธี Deploy จริง)

เนื่องจากระบบถูกออกแบบมาให้ Deploy บน Streamlit Community Cloud ได้โดยตรงโดยไม่ต้องติดตั้ง Python ลงในเครื่อง local:

1. **นำโฟลเดอร์โปรเจกต์ขึ้น GitHub:**
   - เข้า [github.com](https://github.com/) แล้วสร้าง Repository ใหม่ (เช่น `My-Rag-69`)
   - อัปโหลดไฟล์: `app.py`, `requirements.txt`, `test_questions.csv`, `README.md`, `PROJECT_SUMMARY.md`, `.gitignore` และโฟลเดอร์ `data/`
   > ⚠️ ไฟล์ `.streamlit/secrets.toml` จะไม่ถูกอัปโหลดขึ้น GitHub เพื่อความปลอดภัยของ API Key
2. **เข้าสู่ Streamlit Community Cloud:**
   - ไปที่ [share.streamlit.io](https://share.streamlit.io/) แล้วล็อกอินด้วย GitHub
3. **สร้างแอปพลิเคชัน (New App):**
   - **Repository:** เลือก Repository ของคุณ
   - **Branch:** `main` (หรือ master)
   - **Main file path:** `app.py`
4. **ตั้งค่า Gemini API Key ใน Secrets:**
   - คลิกที่ **"Advanced settings..."**
   - ในช่อง **Secrets** ให้ระบุ:
     ```toml
     GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
     ```
   - กดปุ่ม **Save**
5. **กดปุ่ม "Deploy!":**
   - Streamlit Cloud จะทำการติดตั้ง dependencies ทั้งหมดและรันระบบให้พร้อมใช้งานออนไลน์ทันที
