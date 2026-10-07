# เอกสารสรุปโครงงาน (Project Summary)

---

## 1. ชื่อโครงงาน (Project Title)
**Computer & Device Support Assistant**  
*(ระบบ RAG ตอบคำถามและแก้ไขปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11 ด้วย Google Gemini)*

---

## 2. แนวคิดของโครงงาน (Core Concept)
การพัฒนา AI Chatbot แบบ **Retrieval-Augmented Generation (RAG)** ที่เชื่อมโยง Large Language Model (LLM) เข้ากับคลังความรู้เฉพาะทาง (Domain-Specific Knowledge Base) เพื่อให้ AI ตอบคำถามจากข้อเท็จจริงในเอกสารที่กำหนดไว้เท่านั้น ป้องกันการกุเรื่องหรือตอบข้อความที่ไม่เป็นจริง (Hallucination) และแสดงแหล่งอ้างอิงทุกครั้งที่ตอบคำถาม

---

## 3. ปัญหาที่ต้องการแก้ไข (Problem Statement)
- ผู้ใช้งานทั่วไปเมื่อพบปัญหาเกี่ยวกับคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11 (เช่น Wi-Fi หลุด, เสียงไม่ออก, Bluetooth ไม่เชื่อมต่อ, จอภายนอกไม่ติด) มักค้นหาผ่านอินเทอร์เน็ตแล้วพบข้อมูลกระจัดกระจาย ไม่ตรงรุ่น หรือมีขั้นตอนที่ไม่ถูกต้อง
- หากใช้โมเดล LLM ทั่วไปตอบคำถาม โมเดลมักจะตอบด้วยความรู้กว้างๆ ที่อาจคลาดเคลื่อน หรือแนะนำวิธีที่อาจส่งผลกระทบต่อระบบคอมพิวเตอร์
- จำเป็นต้องมีระบบผู้ช่วยที่ตอบเฉพาะวิธีแก้ไขปัญหาที่เป็นมาตรฐานตามคู่มือของระบบปฏิบัติการ โดยมีแหล่งอ้างอิงชัดเจน และปฏิเสธอย่างถูกต้องหากคำถามอยู่นอกเหนือขอบเขต

---

## 4. วัตถุประสงค์ (Objectives)
1. พัฒนาระบบค้นคืนข้อมูลและสร้างคำตอบ (RAG Pipeline) สำหรับคำถามด้านคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11
2. นำเทคนิค Text Cleaning, Chunking, Multilingual Embedding และ FAISS Vector Search มาประยุกต์ใช้ร่วมกันอย่างมีประสิทธิภาพ
3. ออกแบบและทดสอบ Prompt Engineering ร่วมกับ Google Gemini LLM API เพื่อจำกัดขอบเขตคำตอบให้อยู่ใน Context เท่านั้น
4. พัฒนา Web Application Chatbot ด้วย Streamlit ที่พร้อมสำหรับการ Deploy ใช้งานจริงบน Streamlit Community Cloud
5. สร้างระบบกรองคำถามด้วย Similarity Threshold เพื่อปฏิเสธคำถามที่ไม่มีในเอกสารโดยตอบว่า *"ไม่พบข้อมูลในเอกสาร"*

---

## 5. ขอบเขตและโดเมนของระบบ (Domain)
เน้นการแก้ไขปัญหาทางเทคนิคระดับผู้ใช้งานทั่วไป (Level 1 Support) บนระบบปฏิบัติการ **Windows 11**:
- ปัญหาเครือข่าย: Wi-Fi, Router, Network Adapter
- อุปกรณ์ไร้สาย: Bluetooth, หูฟังไร้สาย, Pairing Mode
- ระบบเสียง: Output Device, Audio Troubleshooter, Microphone Input
- อุปกรณ์แสดงผล: HDMI, DisplayPort, Multiple Monitors, Windows + P
- การเชื่อมต่อภายนอก: พอร์ต USB, USB-C (Data/Display/Power Delivery)
- ไดรเวอร์และฮาร์ดแวร์: Device Manager, Driver Update/Rollback, Error Codes
- พื้นที่จัดเก็บข้อมูล: จัดการไดรฟ์ C, Temporary Files, Storage Sense
- พลังงาน: สถานะแบตเตอรี่, การสร้าง Battery Report (`powercfg /batteryreport`)

---

## 6. คลังความรู้ (Knowledge Base)
เอกสารในโฟลเดอร์ `data/` ประกอบด้วย 12 ไฟล์ในรูปแบบ UTF-8 Plain Text ซึ่งเรียบเรียงและอ้างอิงจาก **Microsoft Support**:
1. `01_windows11_basic.txt`: การตรวจสอบสเปกเครื่องและการใช้งาน Windows Update
2. `02_wifi_troubleshooting.txt`: การวิเคราะห์และแก้ปัญหา Wi-Fi เชื่อมต่อไม่ได้หรือไม่มีอินเทอร์เน็ต
3. `03_bluetooth.txt`: การแก้ปัญหา Bluetooth หาย, ไม่พบอุปกรณ์, และหูฟังไม่มีเสียง
4. `04_audio.txt`: การตั้งค่าและแก้ปัญหาลำโพง/เสียงไม่มีเสียงใน Windows 11
5. `05_microphone_headset.txt`: การตั้งค่าไมโครโฟน สิทธิ์การเข้าถึง และการทดสอบไมค์
6. `06_printer.txt`: ขั้นตอนการติดตั้งและแก้ปัญหาเครื่องพิมพ์
7. `07_external_monitor.txt`: การต่อจอภายนอก ตรวจสอบสาย และโหมดแสดงผล
8. `08_usb_usbc.txt`: ข้อจำกัดและมาตรฐานของพอร์ต USB / Type-C
9. `09_device_manager_driver.txt`: การตรวจสอบ Hardware Status และรหัสข้อผิดพลาดของ Driver
10. `10_storage_disk.txt`: การล้างไฟล์ขยะและเพิ่มพื้นที่ไดรฟ์ C
11. `11_mouse_keyboard.txt`: การแยกปัญหาฮาร์ดแวร์เมาส์และคีย์บอร์ด
12. `12_battery_power.txt`: การถนอมแบตเตอรี่และการวิเคราะห์ประวัติแบตเตอรี่

---

## 7. สถาปัตยกรรม RAG Pipeline (RAG Pipeline Architecture)
ระบบแบ่งออกเป็น 2 กระบวนการหลัก:

### 1) Offline/Initialization Stage (การเตรียมดัชนีเวกเตอร์)
1. **Document Loading**: สแกนและอ่านไฟล์ `.txt` ทั้งหมดใน `data/` ด้วย UTF-8 encoding
2. **Text Cleaning**: ตัดช่องว่างซ้ำซ้อน, จัดระเบียบ Newlines, คงตัวอักษรไทย-อังกฤษครบถ้วน
3. **Chunking**: ตัดข้อความออกเป็นส่วนย่อยขนาด 650 ตัวอักษร มี Overlap 120 ตัวอักษร
4. **Sentence Embedding**: แปลงข้อความแต่ละ Chunk เป็น Dense Vector ขนาด 384 มิติ
5. **FAISS Indexing**: สร้างดัชนีเวกเตอร์แบบ Cosine Similarity ผ่าน `IndexFlatIP` แล้วเก็บ Cache ไว้ในหน่วยความจำ

### 2) Online/Inference Stage (การตอบคำถามผู้ใช้)
1. **User Query**: รับคำถามจาก Chat Interface
2. **Query Embedding**: แปลงคำถามของผู้ใช้เป็น Vector ด้วยโมเดลเดียวกัน
3. **FAISS Search**: ค้นหา Top-4 Chunks ที่มี Cosine Similarity สูงสุด
4. **Threshold Evaluation**: ตรวจสอบว่าความคล้ายคลึงสูงสุด $\ge 0.35$ หรือไม่
   - หากต่ำกว่า $\rightarrow$ ส่งคืนคำตอบ *"ไม่พบข้อมูลในเอกสาร"* ทันที (ไม่เรียก LLM)
   - หากผ่านเกณฑ์ $\rightarrow$ ประกอบร่าง Prompt พร้อม Context
5. **LLM Generation**: ส่ง Context และคำถามไปยัง Google Gemini API (`gemini-1.5-flash`)
6. **Response & Citation**: แสดงคำตอบบน Streamlit พร้อมระบุชื่อไฟล์อ้างอิงและคะแนนความเกี่ยวข้อง

---

## 8. การแบ่งท่อนข้อความ (Chunking Strategy)
- **พารามิเตอร์**:
  - `chunk_size = 650` ตัวอักษร
  - `chunk_overlap = 120` ตัวอักษร
- **แนวคิดการออกแบบ**: 
  - ขนาด 650 ตัวอักษร มีความยาวประมาณ 1-2 ย่อหน้า ซึ่งเพียงพอสำหรับเก็บใจความของขั้นตอนแก้ปัญหา 1 ขั้นตอนโดยไม่ตกหล่น
  - Overlap 120 ตัวอักษร ป้องกันไม่ให้ประโยคหรือขั้นตอนสำคัญถูกตัดขาดตอนรอยต่อ
  - มีการตัดคำโดยตรวจหาเครื่องหมายขึ้นบรรทัดใหม่ (`\n`) หรือช่องว่าง (` `) ก่อนตัด เพื่อไม่ให้คำขาดช่วงกลางคำ
  - มีการผูก Metadata: `source` (ชื่อไฟล์) และ `chunk_id` ไว้กับทุก Chunk

---

## 9. โมเดล Embedding (Embedding Model)
- **โมเดลที่เลือกใช้**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **เหตุผลในการเลือก**:
  - รองรับมากกว่า 50 ภาษา รวมทั้งภาษาไทยและภาษาอังกฤษอย่างมีประสิทธิภาพ
  - มิติเวกเตอร์ขนาด 384 มิติ ทำให้ค้นหาได้อย่างรวดเร็วและใช้หน่วยความจำน้อย
  - โมเดลมีขนาดไฟล์เพียง ~470 MB เหมาะอย่างยิ่งสำหรับสภาพแวดล้อมที่มี RAM จำกัด เช่น Streamlit Community Cloud (จำกัด ~1 GB RAM)
  - โหลดเพียงครั้งเดียวและถูก Cache ด้วย `@st.cache_resource`

---

## 10. การค้นคืนข้อมูลด้วย FAISS (FAISS Vector Retrieval)
- **Library**: `faiss-cpu`
- **Index Type**: `faiss.IndexFlatIP` (Inner Product)
- **การคำนวณ Cosine Similarity**:
  $$\text{Cosine Similarity} = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\|_2 \|\mathbf{B}\|_2}$$
  เนื่องจากเวกเตอร์ของ Chunk และ Query ได้รับการ Normalize ($L_2\text{-norm} = 1$) ก่อนบันทึกลงใน FAISS ผลลัพธ์ของ Inner Product จึงเท่ากับ Cosine Similarity โดยตรง
- **Top-K**: ค่าเริ่มต้นกำหนดไว้ที่ 4 Chunks

---

## 11. การออกแบบ Prompt (Prompt Engineering)
ออกแบบ System Prompt ในลักษณะ **Constraint-Based Guardrail**:
- กำหนดบทบาทชัดเจน: ผู้เชี่ยวชาญด้านคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11
- กฎเกณฑ์ที่เคร่งครัด:
  1. บังคับตอบจาก `CONTEXT` เท่านั้น ห้ามนำความรู้ภายนอกมาตอบ
  2. ห้ามแต่งเติมหรือสร้างขั้นตอนที่ไม่มีในเอกสาร
  3. หาก Context ไม่มีข้อมูลเพียงพอ ต้องตอบว่า *"ไม่พบข้อมูลในเอกสาร"* เท่านั้น
  4. ตอบภาษาเดียวกับคำถามของผู้ใช้
  5. อ้างอิงชื่อไฟล์แหล่งข้อมูลในคำตอบ

---

## 12. โมเดลภาษาและการตั้งค่า LLM (LLM & Google Gemini API)
- **Provider**: Google Gemini API (`google-generativeai`)
- **โมเดลหลัก (Default)**: `gemini-1.5-flash` (สามารถสลับเป็น `gemini-1.5-pro`, `gemini-2.0-flash` ได้)
- **Temperature**: กำหนดเป็น `0.0` เพื่อลดความผันแปรและเน้นความถูกต้องตามข้อเท็จจริง (Deterministic & Factual)
- **ความปลอดภัยของ API Key**: 
  - อ่านผ่าน `st.secrets["GEMINI_API_KEY"]` เป็นลำดับแรก
  - ป้องกันการหลุดของคีย์ขึ้น Git โดยการระบุ `.streamlit/secrets.toml` ใน `.gitignore`

---

## 13. การออกแบบหน้าจอ Chatbot (Chatbot UI)
พัฒนาด้วย **Streamlit**:
- **Main Chat Window**: ใช้ `st.chat_message()` และ `st.chat_input()` แสดงผลลื่นไหลเหมือนแอปพลิเคชันแชตสมัยใหม่
- **Chat History**: รักษาประวัติการถาม-ตอบตลอด Session ด้วย `st.session_state.messages`
- **Source Citation Display**: แสดงส่วนสรุปแหล่งข้อมูลอ้างอิงและ Relevance Score ใต้คำตอบ
- **Retrieved Chunks Expander**: กล่องพับเก็บ `st.expander("🔎 ข้อมูลที่ค้นพบจากเอกสาร")` ให้ผู้ใช้ตรวจสอบข้อความดิบที่ระบบค้นคืนได้จริง
- **Sidebar Control**:
  - แสดงสถิติจำนวนเอกสารและจำนวน Chunks ทั้งหมด
  - สไลเดอร์ปรับค่า Top-K (1 - 8) และ Similarity Threshold (0.10 - 0.80)
  - กล่องเลือกเปลี่ยนโมเดล Gemini
  - ปุ่มล้างประวัติการสนทนา (Clear Chat)

---

## 14. การแสดงแหล่งข้อมูลอ้างอิง (Source Citation)
เพื่อสร้างความโปร่งใส (Explainability):
- ทุกคำตอบที่ผ่านการตอบจาก Context จะมีรายการไฟล์อ้างอิง เช่น:
  ```text
  📚 แหล่งข้อมูลอ้างอิง (Sources):
  - 03_bluetooth.txt (Relevance: 0.78)
  ```
- ช่วยให้ผู้ใช้สามารถตรวจสอบความถูกต้องกับเอกสารต้นฉบับได้ทันที

---

## 15. การจัดการคำถามที่ไม่มีในเอกสาร (Unknown Question Handling)
ระบบป้องกันการตอบคำถามนอกขอบเขตด้วยกลไก 2 ชั้น (Two-Tier Guardrails):
1. **Tier 1 (Vector Retrieval Threshold)**: หากคะแนนความเกี่ยวข้องสูงสุดจากการค้นหา FAISS ต่ำกว่า `0.35` ระบบจะตอบ *"ไม่พบข้อมูลในเอกสาร"* ทันที และ**ไม่ส่งต่อไปยัง LLM**
2. **Tier 2 (Strict Prompt Constraint)**: หากคำถามมีคีย์เวิร์ดที่ผ่านเกณฑ์ Threshold แต่เนื้อหาใน Chunks ไม่ครอบคลุมคำตอบ ตัว Prompt จะบังคับให้ LLM ตอบว่า *"ไม่พบข้อมูลในเอกสาร"*

---

## 16. การนำขึ้นระบบและการ Deploy (Deployment)
- **แพลตฟอร์ม**: Streamlit Community Cloud
- **ไฟล์สำคัญสำหรับ Deploy**:
  - `app.py`: ตัวแอปพลิเคชันหลัก
  - `requirements.txt`: ระบุ Library ที่จำเป็น (`streamlit`, `sentence-transformers`, `faiss-cpu`, `google-generativeai`, `numpy`)
  - `.gitignore`: ป้องกันการอัปโหลดไฟล์ลับ
  - `data/`: คลังเอกสารความรู้
- **การจัดการ Secret บน Cloud**: กำหนด `GEMINI_API_KEY` ในเมนู Settings > Secrets ของ Streamlit Cloud Dashboard

---

## 17. ผลการทดสอบ (Test Cases Evaluation)
จากการทดสอบชุดคำถาม 17 ข้อใน `test_questions.csv`:
- **คำถามตรงหัวข้อ (12 ข้อ)**: ค้นคืน Chunks ตรงกับเอกสารเป้าหมาย เช่น Wi-Fi, Bluetooth, ไมโครโฟน, จอภาพ, แบตเตอรี่ ได้ความแม่นยำสูง (Relevance Score > 0.65)
- **คำถามภาษาอังกฤษ (2 ข้อ)**: โมเดล Multilingual Sentence Transformer สามารถจับคู่คำถามภาษาอังกฤษกับเอกสารภาษาไทยได้อย่างถูกต้อง
- **คำถามนอกขอบเขต (3 ข้อ)**: เช่น การเปลี่ยนน้ำมันเครื่อง, การติดตั้ง Ubuntu Server, การทำขนมเค้ก ระบบมี Relevance Score ต่ำกว่า 0.35 ส่งผลให้ปฏิเสธคำถามทันทีด้วยข้อความ *"ไม่พบข้อมูลในเอกสาร"*
