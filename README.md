# ஆணைகள் Repository
தமிழ்நாடு பொது நூலகத் துறை அமைச்சுப் பணியாளர்கள் சங்கம் — Government Orders Archive

## Stack
- Flask (Python)
- Neon PostgreSQL (stores compressed PDF/JPG as BYTEA — no external file storage needed)
- Render.com (hosting)

## Local Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your real DATABASE_URL
python app.py          # runs on http://localhost:5000, creates tables on first run
```

## Git
```bash
git init
git add .
git commit -m "Initial commit: orders repository"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Neon Setup
1. neon.tech-ல் account create பண்ணி புதிய Project உருவாக்கவும்.
2. Dashboard-ல் கிடைக்கும் **Connection string**-ஐ காபி பண்ணவும் (sslmode=require உடன்).
3. இதை Render-ல் `DATABASE_URL` environment variable-ஆக வைக்கவும்.

## Render Deployment
1. Render Dashboard → New → Web Service → இந்த GitHub repo-ஐ connect பண்ணவும்.
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `gunicorn app:app`
4. **Environment Variables:**
   - `DATABASE_URL` → Neon connection string
   - `ADMIN_PASSWORD` → Dlodgl@789 (அல்லது வேறு password)
   - `SECRET_KEY` → ஏதேனும் random string
   - `COMPRESSION_QUALITY` → 70
5. Deploy ஆனதும், முதல் முறை app run ஆகும்போது tables தானாகவே உருவாகும் (`init_db()` runs on `python app.py`, ஆனால் gunicorn-ல் manual ஆக ஒரு தடவை run பண்ணணும் — கீழே பாருங்க).

### முதல் தடவை Tables உருவாக்க (Render Shell-ல்)
Render dashboard-ல் உங்கள் service-க்குள் "Shell" tab திறந்து:
```bash
python -c "from db import init_db; init_db()"
```

## கட்டமைப்பு (Structure)
- 3 முதன்மை வகைகள் (அரசு / இயக்குநர் / நீதிமன்றம்) → ஒவ்வொன்றுக்கும் துணை வகைகள்
- ஒவ்வொரு ஆணைக்கும் ஆவணப் பார்வை முறை (பொதுவானவை/மைய/கிளை/ஊரப்புறம்/அலுவலகம்)
- Admin (`/admin`) — password login → முதன்மை/துணை வகைகளை சேர்க்க/நீக்க, ஆணைகளை பதிவேற்ற/நீக்க முடியும்
- Users — `/` நேரடியா பார்வையிட முடியும், password தேவையில்லை

## Compression
- Images → JPEG quality 70%, max dimension 2000px
- PDFs → ஒவ்வொரு பக்கமும் 150 DPI-ல் rasterize பண்ணி JPEG quality 70%-ல் மறுகட்டமைக்கப்படும் (scanned ஆணைகளுக்கு சிறந்த அளவு குறைப்பு)
- `COMPRESSION_QUALITY` env var மூலம் தேவைப்பட்டால் மாற்றலாம்
