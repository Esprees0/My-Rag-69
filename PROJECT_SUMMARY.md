# สรุปงานแบบพร้อมทำ

หัวข้อ: **Computer & Device Support Assistant — ระบบ RAG สำหรับตอบคำถามและแก้ไขปัญหาคอมพิวเตอร์และอุปกรณ์ต่อพ่วงบน Windows 11**

## ต้องทำอะไร
1. เตรียมเอกสารความรู้ 12 ไฟล์ใน `data/`
2. โหลดและ Cleaning ข้อความ
3. แบ่งข้อความเป็น Chunk
4. ทำ Sentence Embedding
5. สร้าง FAISS Vector Index
6. รับคำถามและค้น Top-k Chunks
7. ส่ง Context + Question เข้า LLM ด้วย Prompt ที่บังคับให้ตอบจากเอกสารเท่านั้น
8. ถ้าไม่มีข้อมูล ให้ตอบ `ไม่พบข้อมูลในเอกสาร`
9. สร้าง Streamlit Chat UI พร้อม Chat history และ Source
10. ทำ `test_questions.csv` และทดสอบอย่างน้อย 10 ข้อ
11. ใส่โค้ดทั้งหมดขึ้น GitHub
12. เก็บ `GROQ_API_KEY` ใน Streamlit Secrets เท่านั้น
13. Deploy ผ่าน Streamlit Community Cloud
14. Capture หน้าจอและทำ PDF ส่งอาจารย์

## ไฟล์ที่เตรียมให้แล้ว
- `data/` เอกสารความรู้ 12 ไฟล์
- `test_questions.csv` คำถามทดสอบ 12 ข้อ โดยมีคำถามที่ไม่มีข้อมูล 2 ข้อ
- `README.md` แนวคิด Domain, แหล่งข้อมูล, แนวทาง RAG และตัวอย่าง Prompt

## แนะนำโครงสร้าง GitHub
```text
computer-device-rag/
├── app.py
├── requirements.txt
├── README.md
├── test_questions.csv
├── .gitignore
└── data/
    ├── 01_windows11_basic.txt
    ├── 02_wifi_troubleshooting.txt
    ├── 03_bluetooth.txt
    ├── 04_audio.txt
    ├── 05_microphone_headset.txt
    ├── 06_printer.txt
    ├── 07_external_monitor.txt
    ├── 08_usb_usbc.txt
    ├── 09_device_manager_driver.txt
    └── 10_storage_disk.txt
```
