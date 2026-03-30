# CLEAVE SNP — Frontend

Computational platform for detecting disease-causing SNPs and designing CRISPR-based genetic corrections.

**EC552 — Computational Synthetic Biology — Boston University**

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Start development server
npm start
```

The app runs at `http://localhost:3000`. It uses mock data by default — no backend needed to get started.

## Connecting to the Backend

1. Start your FastAPI backend on `http://localhost:8000`
2. Open `src/data/config.js` and set `USE_MOCK = false`
3. If your backend runs on a different URL, create a `.env` file:

```
REACT_APP_API_URL=http://your-server:8000
```

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
