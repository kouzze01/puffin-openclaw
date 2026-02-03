# 🤖 AI-Powered Trade Analysis with n8n

> **Integrate Smart Analysis using n8n Webhooks & OpenRouter**

## 🎯 Concept

ระบบนี้จะทำการส่งข้อมูลการเทรดที่ปิดแล้ว (Closed Trades) ไปยัง n8n เพื่อให้ AI (ผ่าน OpenRouter) ช่วยวิเคราะห์พฤติกรรมการเทรด จุดเข้า/ออก และให้คำแนะนำ จากนั้นบันทึกผลการวิเคราะห์กลับลง Database เพื่อแสดงผลใน Dashboard

**Flow:**
`VPS (Bot)` ➔ `Webhook` ➔ `n8n (AI Agent)` ➔ `Supabase Results` ➔ `Streamlit Dashboard`

---

## 🗄️ Database Changes (SQL)

เพิ่ม Column สำหรับเก็บผลการวิเคราะห์ในตาราง `trade_log` และ `paper_trade_log`

### 1. SQL Script
รันคำสั่งนี้ใน Supabase SQL Editor:

```sql
-- เพิ่ม Column ai_analysis ใน paper_trade_log
ALTER TABLE paper_trade_log 
ADD COLUMN IF NOT EXISTS ai_analysis TEXT,
ADD COLUMN IF NOT EXISTS ai_score INTEGER;

-- เพิ่ม Column ai_analysis ใน trade_log (สำหรับ Live)
ALTER TABLE trade_log 
ADD COLUMN IF NOT EXISTS ai_analysis TEXT,
ADD COLUMN IF NOT EXISTS ai_score INTEGER;

-- (Optional) สร้างตารางแยกถ้าต้องการเก็บรายละเอียดเพิ่มเติม
-- แต่เบื้องต้นเก็บใน Table เดิมสะดวกกว่า
```

---

## ⚡ n8n Workflow Design

### Workflow Overview
1. **Webhook (POST)**: รับ JSON data จาก VPS
2. **AI Agent (OpenRouter)**: วิเคราะห์ Trade Data
3. **Supabase Node (Update)**: บันทึกผลกลับลง DB

### JSON Data Payload (ส่งจาก VPS)
```json
{
  "trade_id": 123,
  "pair": "BTCUSDT",
  "zone_name": "Module 90k-92k",
  "mode": "PAPER",
  "entry_price": 91200,
  "exit_price": 91400,
  "quantity": 0.001,
  "pnl_usdt": 0.2,
  "duration_minutes": 45,
  "market_regime": "SIDEWAY",
  "rsi_entry": 35,
  "rsi_exit": 65
}
```

### 🧩 Workflow Steps

#### 1. Webhook Node
- **Method:** `POST`
- **Path:** `/analyze-trade`
- **Authentication:** Header Auth (แนะนำให้ใส่ Secret Key)

#### 2. LLM Chain / AI Agent Node
เชื่อมต่อกับ **OpenRouter** (เลือก Model เช่น `google/gemini-2.0-flash-exp` หรือ `anthropic/claude-3-5-sonnet`)

**System Prompt:**
```text
You are an expert crypto trading analyst for a Grid Trading Bot system.
Your job is to analyze a completed trade and provide brief, actionable feedback.

Input Data:
- Entry: {{json.entry_price}} | Exit: {{json.exit_price}}
- PnL: {{json.pnl_usdt}} USDT
- Duration: {{json.duration_minutes}} mins
- RSI Entry: {{json.rsi_entry}} | Market Regime: {{json.market_regime}}

Task:
1. Rate this trade from 1-10 (Score).
2. Provide a 1-sentence analysis of the Entry (Good/Bad/Risky).
3. Provide a 1-sentence observation on the Exit.
4. Keep it concise.

Output Format (JSON):
{
  "score": 8,
  "analysis": "Good entry at RSI 35 during sideway market. Quick profit secured effectively."
}
```

#### 3. Output Parser (JSON)
แปลงผลลัพธ์จาก AI ให้เป็น JSON Object เพื่อเตรียมลง DB

#### 4. Supabase Update Node
- **Operation:** Update
- **Table:** `paper_trade_log` (หรือ `trade_log` เช็คจาก input `mode`)
- **Match By:** `id` = `{{json.trade_id}}`
- **Update Fields:**
  - `ai_analysis`: `{{json.analysis}}`
  - `ai_score`: `{{json.score}}`

---

## 💻 Python Implementation (VPS Side)

เพิ่มฟังก์ชันใน `trade_and_log.py` เพื่อยิง Webhook หลังปิด Trade

### Function
```python
import requests
import json

N8N_WEBHOOK_URL = "YOUR_N8N_WEBHOOK_URL"
N8N_SECRET = "YOUR_SECRET_KEY"

def send_trade_to_analysis(trade_data):
    """
    Sends closed trade data to n8n for AI analysis.
    This should be non-blocking (fire and forget).
    """
    try:
        payload = {
            "trade_id": trade_data['id'],
            "mode": TRADING_MODE,
            "pair": SYMBOL,
            "entry_price": float(trade_data['entry_price']),
            "exit_price": float(trade_data['exit_price']),
            "quantity": float(trade_data['quantity']),
            "pnl_usdt": float(trade_data['pnl_usdt']),
            "rsi_entry": 0, # ถ้ามีเก็บไว้
            # ... field อื่นๆ
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-auth-secret": N8N_SECRET
        }
        
        # Requests.post (use simple timeout to avoid hanging)
        requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=2)
        print(f"🤖 Sent Trade {trade_data['id']} to AI Analysis")
        
    except Exception as e:
        print(f"⚠️ Failed to send trade to AI: {e}")
```

### Integration Point
เรียกฟังก์ชันนี้ใน `execute_sell` หลังจาก `supabase_client.update().execute()` สำเร็จ

---

## ✅ Next Steps for User
1. สร้าง **n8n Workflow** ตามโครงสร้างด้านบน
2. สร้าง Column ใน **Supabase** ตาม SQL ที่ให้
3. นำ URL Webhook มาใส่ใน `.env`
4. ผมจะแก้โค้ด Python ให้รองรับฟังก์ชันนี้
