# CLEAVE SNP

Computational platform for detecting disease-causing SNPs and designing CRISPR-based genetic corrections.

**EC552 — Computational Synthetic Biology — Boston University**

## Prerequisites

- **Node.js** 18+ (for the React frontend)
- **Python** 3.10+ (for the FastAPI backend)
- **BLAST+** from NCBI — [download here](https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/)

---

## Running the Backend

The backend is a FastAPI server that wraps the BLAST analysis pipeline.

```bash
# 1. Install Python dependencies (from the project root)
pip install -r requirements.txt

# 2. Start the API server
uvicorn BLAST.server.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Keep this terminal open while using the app.

> **Important:** Run the `uvicorn` command from the **project root** (`EC552-Project/`), not from inside the `BLAST/` folder. The relative imports require it to be run as a package.

### First-Time Backend Setup

After starting the server, open the app and go to **Settings** to complete one-time configuration:

1. **Configure BLAST bin path** — Paste the full path to your BLAST+ `bin` folder (e.g. `C:\Program Files\NCBI\blast-2.17.0+\bin`) and click **Save Configuration**.
2. **Build the reference database** — Load a FASTA file or paste FASTA text in the "Initialize / Update Database" card, then click **Build (overwrite)**. The sample database is at `BLAST/sample_fasta_test/gene.fa`.

These steps only need to be done once. The server remembers the BLAST bin path in `BLAST/server_config.json`.

---

## Running the Frontend

```bash
# 1. Install dependencies
npm install

# 2. Start development server
npm start
```

The app runs at `http://localhost:3000`.

### Mock vs. Live Data

By default the app uses mock data so the UI can be explored without the backend running. To switch to the live API:

1. Open `src/data/config.js` and set `USE_MOCK = false`
2. Make sure the backend is running on `http://localhost:8000`

If your backend runs on a different URL, create a `.env` file in the project root:

```
REACT_APP_API_URL=http://your-server:8000
```

---

## Running Both Together (Recommended)

Open two terminals side by side:

```bash
# Terminal 1 — Backend
uvicorn BLAST.server.main:app --reload --port 8000

# Terminal 2 — Frontend
npm start
```

Then open `http://localhost:3000` in your browser.

## Project Structure

```
src/
├── components/
│   ├── shared/           # Reusable UI components (Btn, Card, PathBadge, Layout)
│   │   ├── Btn.js
│   │   ├── Card.js
│   │   ├── PathBadge.js
│   │   ├── Layout.js     # PageShell, PageHeader, Spinner
│   │   └── index.js      # Barrel export
│   └── Navbar.js
├── pages/
│   ├── HomePage.js           # Landing page with feature cards
│   ├── DatabasePage.js       # Browse/add DNA sequences
│   ├── AnalysisPage.js       # Sequence input (paste / upload)
│   ├── InstructionsPage.js   # Usage guide + FAQ
│   ├── SettingsPage.js       # BLAST bin config + database management
│   ├── AnalyzingPage.js      # Loading screen (fires API call)
│   ├── SNPResultsPage.js     # Detected SNPs table
│   ├── CRISPRDesignPage.js   # gRNA candidates table + refinement
│   ├── BindingViewPage.js    # Interactive SVG genome viewer
│   ├── EditResultsPage.js    # Final summary + export
│   └── index.js              # Barrel export
├── context/
│   └── AppContext.js         # Global state (React Context + useNavigate)
├── services/
│   └── api.js                # Axios client for FastAPI backend
├── utils/
│   └── sequence.js           # FASTA parser, sequence validator
├── data/
│   ├── config.js             # USE_MOCK toggle, app constants
│   └── mockData.js           # Mock sequences, SNPs, gRNAs, binding data
├── styles/
│   ├── index.css             # Global CSS, reset, animations
│   └── theme.js              # Theme constants for inline styles
├── App.js                    # React Router setup
└── index.js                  # ReactDOM entry point
```

## Route Map

| Path | Page | Description |
|------|------|-------------|
| `/` | HomePage | Landing with feature cards |
| `/database` | DatabasePage | Browse/add sequences |
| `/analysis` | AnalysisPage | Sequence input form |
| `/instructions` | InstructionsPage | Guide + FAQ |
| `/settings` | SettingsPage | BLAST bin config + database management |
| `/analyzing` | AnalyzingPage | Loading (auto-redirects) |
| `/results/snps` | SNPResultsPage | Detected SNPs table |
| `/results/crispr` | CRISPRDesignPage | gRNA design + scoring |
| `/results/binding` | BindingViewPage | Genome viewer |
| `/results/edit` | EditResultsPage | Summary + export |

## Building for Production

```bash
npm run build
```

Output goes to `build/`. Deploy this folder to any static hosting (Netlify, Vercel, GitHub Pages, or serve alongside your FastAPI backend).

## Team

- Luke Hovagimian
- Alexander Leong
- Minh Nguyen
- Heewon Park
