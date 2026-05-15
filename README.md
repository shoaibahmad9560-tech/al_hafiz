# WhatsApp AI Automation — Enhancement Layer

> **⚠️ CRITICAL**: This system **extends** the existing WhatsApp Messenger (NestJS).
> It does NOT replace it. All existing functionality continues to work unchanged.

---

## What This Is

A Python/Flask middleware layer that adds AI-powered automation on top of your
existing NestJS-based WhatsApp Messenger system. Think of it as a second brain
that sits alongside the existing system and handles conversations intelligently.

```
Twilio WhatsApp
      │
      ├──→ Existing NestJS (port 3005)   ← handles receipts, DB writes
      │         ↑ forwarded by AI layer
      │
      └──→ AI Enhancement Layer (port 5000)   ← NEW: AI, rules, agents, broadcast
                ├── Rule Engine (keyword → instant Urdu reply)
                ├── AI Engine (OpenAI GPT → context-aware Urdu reply)
                ├── Session Store (Redis, temp — no DB writes)
                ├── Agent Escalation (human takeover)
                └── Broadcast (promotional messages)
```

---

## Safety Guarantees

| What we DON'T do | What we DO |
|---|---|
| ❌ Modify existing DB | ✅ Read-only calls to existing API |
| ❌ Change existing code | ✅ Parallel webhook subscription |
| ❌ Replace existing replies | ✅ Add AI replies alongside |
| ❌ Break existing flows | ✅ Forward to existing system first |
| ❌ Overwrite chat records | ✅ Parallel Redis session (TTL 24h) |

---

## Quick Start

### 1. Install dependencies
```bash
cd whatsapp_ai_layer
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — fill in your OpenAI API key and confirm Twilio credentials
nano .env
```

Key settings to fill in:
- `OPENAI_API_KEY` — your OpenAI API key (get from platform.openai.com)
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` — same as existing system
- `NESTJS_BASE_URL` — URL of your existing NestJS API (default: `http://localhost:3005/api`)

### 3. Run
```bash
python app.py
# Server starts on http://localhost:5000
```

For production:
```bash
gunicorn app:create_app() --bind 0.0.0.0:5000 --workers 2
```

---

## Twilio Webhook Setup (Two Options)

### Option A — Dual Webhook (Recommended)
Set TWO webhooks in Twilio console — both receive all messages:
1. Existing: `https://yourserver.com/api/webhooks/whatsapp` (NestJS)
2. New AI: `https://yourserver.com:5000/api/whatsapp/webhook` (this layer)

Both run independently. Media receipts → handled by NestJS. Text → handled by AI layer.

### Option B — Single Webhook (Proxy Mode)
Set ONLY the AI layer as the webhook:
`https://yourserver.com:5000/api/whatsapp/webhook`

The AI layer automatically forwards to NestJS internally. This is simpler but adds one network hop.

---

## API Reference

### Webhook (incoming messages)
```
POST /api/whatsapp/webhook          ← Twilio sends here
GET  /api/whatsapp/webhook          ← Twilio verification challenge
GET  /api/whatsapp/sessions/{phone} ← View a chat session
POST /api/whatsapp/sessions/{phone}/resolve  ← Mark resolved
POST /api/whatsapp/sessions/{phone}/assign   ← Assign to agent
```

### Agent Dashboard
```
GET  /api/agents/chats               ← All active chats
GET  /api/agents/chats/escalated     ← Only escalated chats
POST /api/agents/chats/{phone}/reply ← Send manual agent reply
POST /api/agents/chats/{phone}/resolve
GET  /api/agents/chats/{phone}/history
```

### Broadcast
```
POST /api/broadcast/send             ← Send to multiple numbers
GET  /api/broadcast/templates        ← List templates
GET  /api/broadcast/templates/{name} ← Preview a template
```

### Integration / Sync
```
GET /api/integration/sync            ← Check existing system health
GET /api/integration/receipts/{phone}
GET /api/integration/students/{phone}
```

### Status
```
GET /api/status/health               ← Quick health check
GET /api/status/diagnostics          ← Full component status
```

---

## Message Flow

```
1. Message arrives from WhatsApp user
2. AI layer receives it (webhook)
3. Forward to existing NestJS system (non-blocking)
   └── If media (receipt image) → NestJS handles, AI layer steps back
4. Check if session is already ESCALATED → human agent handling, skip AI
5. Rule Engine: check keyword matches
   └── Match found → instant Urdu reply, done
6. Escalation check: too many turns? AI recommends escalation?
   └── Yes → send escalation notice, assign to agent queue
7. AI (OpenAI GPT): generate context-aware Urdu reply
   └── Context enriched with student/receipt data from existing system
8. Send reply via Twilio
9. Save session to Redis (TTL 24h, separate DB from existing system)
```

---

## Customizing Rules (Urdu Keyword Replies)

Add/edit in `.env`:
```env
REPLY_PRICE=💰 ہماری ماہانہ فیس 5000 روپے ہے۔ داخلہ فیس 2000 روپے ہے۔
REPLY_LOCATION=📍 ہمارا پتہ: گلشن اقبال، کراچی۔ نزد X مارکیٹ
REPLY_TIMING=🕐 اوقات: پیر تا ہفتہ، صبح 8 سے شام 4 بجے
```

Or add rules dynamically via the admin panel.

---

## Broadcast Example

```bash
curl -X POST http://localhost:5000/api/broadcast/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["+923001234567", "+923009876543"],
    "template": "fee_reminder",
    "variables": {
      "name": "احمد",
      "amount": "5,000",
      "due_date": "31 مئی",
      "month": "مئی"
    }
  }'
```

---

## Folder Structure

```
whatsapp_ai_layer/
├── app.py                    ← Flask app factory
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py           ← All config from env vars
├── routes/
│   ├── webhook.py            ← Incoming message handler
│   ├── integration.py 🔥     ← Sync with existing NestJS system
│   ├── broadcast.py          ← Promotional message sending
│   ├── agent.py              ← Human agent management
│   └── status.py             ← Health checks
├── services/
│   ├── factory.py            ← Service singleton initialization
│   ├── orchestrator.py       ← Core message decision engine
│   ├── rule_engine.py        ← Keyword → Urdu reply matching
│   ├── ai_service.py         ← OpenAI GPT integration
│   ├── whatsapp_service.py   ← Twilio send wrapper
│   ├── integration_service.py 🔥 ← NestJS API proxy (read-only)
│   └── session_store.py      ← Redis/in-memory chat state
├── models/
│   └── chat.py               ← ChatSession, ChatState, MessageRole
└── utils/
    ├── helpers.py             ← Phone normalization, retries
    └── templates.py           ← Urdu broadcast message templates
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `development` | `development` or `production` |
| `AI_LAYER_PORT` | `5000` | Port for this Flask server |
| `NESTJS_BASE_URL` | `http://localhost:3005/api` | Existing system URL |
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | GPT model (mini is cheaper) |
| `TWILIO_ACCOUNT_SID` | — | Same as existing .env |
| `TWILIO_AUTH_TOKEN` | — | Same as existing .env |
| `TWILIO_WHATSAPP_FROM` | — | Same as existing .env |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `REDIS_DB` | `1` | Redis DB (1 = separate from existing system's 0) |
| `ESCALATION_THRESHOLD_TURNS` | `3` | Turns before auto-escalating |
| `BROADCAST_BATCH_SIZE` | `10` | Numbers per broadcast batch |

---

## Future Scope (Modular Extensions)

- `services/accounting_service.py` — fee balance queries
- `services/inventory_service.py` — stock/product replies
- `services/order_service.py` — order status tracking
- `routes/analytics.py` — chat metrics dashboard
- Admin panel React frontend (connect to `/api/agents/*` endpoints)
