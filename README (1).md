# 🎵 MelodyMatch

> A content-based Spotify song recommender that finds new tracks matching the *vibe* of a song you already love.

MelodyMatch takes a song you like, analyses its audio characteristics (energy, danceability, valence, tempo, and more), and surfaces the most similar tracks using a K-Nearest-Neighbours model. It ships as a full, containerised data application — a production-style ETL pipeline feeds a PostgreSQL database, and a Streamlit web app serves live recommendations on top of it.

---

## ✨ Features

- **Content-based recommendations** using K-Nearest-Neighbours with cosine similarity over 11 audio features.
- **Automatic vibe clustering** — every track is grouped into a mood (e.g. *Mellow / Chill*, *Party / Upbeat*) via K-Means.
- **Production-style ETL pipeline** orchestrated with [Prefect](https://www.prefect.io/), with retries, logging, and run artifacts.
- **Data quality gate** — [Great Expectations](https://greatexpectations.io/) validates the data (null checks, uniqueness, value ranges) *before* anything is written to the database.
- **Idempotent loads** — uses a PostgreSQL `UPSERT` (`ON CONFLICT DO NOTHING`), so re-running the pipeline never creates duplicates.
- **Fully Dockerised** — one command spins up the database, runs the pipeline, and launches the web app.
- **Polished UI** — a Spotify-themed Streamlit interface with embedded track players and a vibe-match score.

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Frontend | Streamlit |
| ML / Recommendations | scikit-learn (KNN, K-Means, MinMaxScaler) |
| Data pipeline | Prefect (orchestration), Great Expectations (validation), Pandas |
| Database | PostgreSQL 15 |
| Infrastructure | Docker, Docker Compose |
| Logging | Loguru |

---

## 🏗️ How It Works

```
 Kaggle datasets
       │
       ▼
┌──────────────────────────────────────────────┐
│  ETL Pipeline (Prefect)  — etl_pipeline.py     │
│                                                │
│  1. Ingest    user listening history (JSON)    │
│  2. Enrich    join with audio features (CSV)   │
│  3. Validate  Great Expectations quality gate  │
│  4. Load      idempotent UPSERT into Postgres  │
└──────────────────────────────────────────────┘
       │
       ▼
  PostgreSQL  ──►  Streamlit App (app.py)
                   • MinMax scale features
                   • K-Means → vibe clusters
                   • KNN → similar tracks
```

The ETL stage builds a clean, enriched table of tracks. The app then loads that table, scales the features, clusters tracks into moods, and trains a KNN model so it can return the closest matches to any song you pick.

---

## 📁 Project Structure

```
.
├── app.py                # Streamlit web app (recommendation UI)
├── etl_pipeline.py       # Prefect-orchestrated ETL pipeline
├── main.ipynb            # Notebook version of the ETL (exploration / dev)
├── Dockerfile            # Container image for the app + pipeline
├── docker-compose.yml    # Wires up Postgres + ETL + frontend
├── requirements.txt      # Python dependencies
├── website-logo1.png     # App logo
├── .env.example          # Template for environment variables
└── README.md
```

---

## 📦 Datasets

The raw data is **not** included in this repo (the audio-features file is too large for git). Download these and place them in the paths below:

| File | Source | Expected path |
|---|---|---|
| Audio features (~1.2M tracks) | [Kaggle: Spotify 1.2M+ Songs](https://www.kaggle.com/datasets/rodolfofigueroa/spotify-12m-songs) | `kaggle-spotify12m/tracks_features.csv` |
| User listening history (JSON) | Your Spotify "Extended Streaming History" export, or any similar Kaggle dataset | `kaggle-user-dataset/clean_data.json` |

> The pipeline joins your listening history against the audio-features dataset, so only tracks present in both end up in the final table.

---

## 🚀 Getting Started

### Option A — Run with Docker (recommended)

This is the easiest path: it starts PostgreSQL, runs the ETL pipeline, and launches the app automatically.

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/melodymatch.git
   cd melodymatch
   ```

2. **Add your environment file**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and set your own `POSTGRES_PASSWORD`.

3. **Add the datasets** in the paths shown in the [Datasets](#-datasets) section.

4. **Launch everything**
   ```bash
   docker compose up --build
   ```

5. Open the app at **http://localhost:8501**

### Option B — Run locally (without Docker)

1. Create and activate a virtual environment, then install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Make sure PostgreSQL is running locally and a database named `spotify_db` exists.
3. Create your `.env` (copy from `.env.example`) and set `POSTGRES_PASSWORD`.
4. Run the pipeline to populate the database:
   ```bash
   python etl_pipeline.py
   ```
5. Launch the app:
   ```bash
   streamlit run app.py
   ```

---

## 🎧 Usage

1. Search for a song you love in the search bar.
2. Choose how many recommendations you want (1–10).
3. Hit **Discover New Music** — MelodyMatch returns the closest-matching tracks, each with a vibe label, a similarity score, and an embedded player so you can listen right away.

---

## 🔭 Possible Improvements

- Add user accounts and save generated playlists.
- Replace content-based KNN with a hybrid (collaborative + content) model.
- Schedule the ETL pipeline to refresh data automatically.
- Push recommendations back into a real Spotify playlist via the Spotify Web API.

---

## 📄 License

Released under the MIT License — feel free to use and adapt.
