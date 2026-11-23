# Tamil Kids AI – Fully Automated YouTube Channel 🎬

An automated, maintainable, zero-budget Tamil 3D cartoon storytelling platform engineered to produce and publish one original kids story video every day to YouTube.

---

## 🌟 Highlights & Capabilities
- **Daily Automated Workflow**: Runs at 09:00 AM IST (Asia/Kolkata).
- **Tamil Storytelling Engine**: AI curriculum rotating through moral categories (friendship, kindness, honesty, sharing, courage, nature) avoiding duplicates.
- **Natural Tamil TTS**: Powered by neural Tamil voices (`ta-IN-PallaviNeural` & `ta-IN-ValluvarNeural`) with zero synthetic latency and automatic word-boundary `.srt` subtitle generation.
- **3D Animation Pipeline**: Procedural Blender 3D character animation and camera control with high-performance low-resource fallback.
- **Child-Friendly Thumbnails**: Auto-generates colorful 16:9 thumbnails with high-contrast Tamil typography.
- **YouTube COPPA Compliance**: Strictly enforces `selfDeclaredMadeForKids: true`.
- **Admin Dashboard**: Full React + Vite dashboard with live progress tracker, story approval, and safety kill-switches.

---

## 📁 Project Architecture

```
tamil-kids-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints (auth, health, dashboard, topics, stories, jobs)
│   │   ├── core/            # Config, JWT security, database connection
│   │   ├── models/          # SQLAlchemy models (User, Topic, Story, Script, Job, Video)
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # AI story generator, Tamil TTS, Blender, Video assembly, YouTube
│   │   └── scheduler/       # APScheduler daily runner (Asia/Kolkata)
│   ├── worker/              # Standalone GPU/CPU render worker CLI
│   ├── requirements.txt     # Python backend dependencies
│   ├── main.py              # FastAPI server entrypoint
│   └── .env                 # Local configuration
├── frontend/                # React + Vite admin dashboard
├── blender/
│   ├── scripts/             # Procedural 3D scene builder & animation script
│   ├── characters/          # 3D character templates
│   └── environments/        # 3D environment models
├── media/                   # Public domain music, SFX, and Tamil Unicode fonts
├── storage/                 # Generated videos, thumbnails, and temp chunks
├── .env.example
└── README.md
```

---

## 🚀 Quick Setup Instructions

### 1. Backend Setup (Windows PowerShell)

```powershell
cd C:\Users\navee\.gemini\antigravity\scratch\tamil-kids-ai\backend

# 1. Create Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the FastAPI Server
python main.py
```

*Server starts on `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.*
*Default Admin Login: Username `admin` | Password `adminpassword123`.*

---

### 2. Frontend Setup

```powershell
cd C:\Users\navee\.gemini\antigravity\scratch\tamil-kids-ai\frontend

# Install and start Vite dev server
npm install
npm run dev
```

*Open your browser at `http://localhost:5173` to access the Tamil Kids AI Admin Dashboard.*

---

### 3. YouTube API v3 Credentials Setup (₹0 Google Cloud Tier)

1. Open **Google Cloud Console** (`console.cloud.google.com`).
2. Create a project named `Tamil Kids Automation`.
3. Enable **YouTube Data API v3**.
4. Go to **APIs & Services > Credentials > Create Credentials > OAuth Client ID**.
5. Select **Desktop App** (or Web Application with redirect URI `http://localhost:8000/api/v1/youtube/oauth2callback`).
6. Download the JSON file and save it as:
   `backend/client_secrets.json`
7. In the YouTube OAuth screen, add your personal channel Google account as a Test User.

---

### 4. Running the Standalone Video Render Worker

To keep your API lightweight while utilizing local GPU or background CPU for 3D animation rendering:

```powershell
cd C:\Users\navee\.gemini\antigravity\scratch\tamil-kids-ai\backend
python worker/render_worker.py
```

---

## 🛡️ Content Safety & COPPA Compliance

1. **Child Protection**: All videos generated have the YouTube Data API attribute `status.selfDeclaredMadeForKids: true`.
2. **Uplifting Themes Only**: All stories are validated against negative tropes, frightening monsters, or unsafe behaviors.
3. **Safety Switch**: By default, `REQUIRE_MANUAL_APPROVAL=true` in `.env` so you can review any generated video and thumbnail in the dashboard before it uploads to YouTube.
