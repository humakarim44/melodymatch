import pandas as pd
import os
import sys
from dotenv import load_dotenv
from urllib.parse import quote_plus
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, Integer
from sqlalchemy.dialects.postgresql import insert
import great_expectations as gx
from prefect import task, flow
from prefect.artifacts import create_markdown_artifact # <-- NEW IMPORT FOR UI OUTPUTS

load_dotenv()

@task(name="Ingest JSON Data", retries=2, retry_delay_seconds=30)
def ingest_simulated_users(user_dataset_path):
    print("Starting Ingestion: Loading User Interactions from JSON...")
    if not os.path.exists(user_dataset_path):
        raise FileNotFoundError(f"Error: Could not find dataset at {user_dataset_path}")
        
    user_df = pd.read_json(user_dataset_path)
    user_df = user_df.rename(columns={
        'artistName': 'artist', 
        'artist_name': 'artist',
        'master_metadata_album_artist_name': 'artist', 
        'trackName': 'track_name',
        'master_metadata_track_name': 'track_name',
        'spotify_track_uri': 'track_id'
    })
    
    user_df = user_df.dropna(subset=['track_id'])
    user_df['track_id'] = user_df['track_id'].astype(str).str.replace('spotify:track:', '')
    unique_tracks_df = user_df.drop_duplicates(subset=['track_id'])
    
    print(f"Successfully ingested {len(unique_tracks_df)} unique tracks.")
    return unique_tracks_df

@task(name="Enrich with Audio Features")
def enrich_user_tracks(unique_tracks_df, features_dataset_path):
    print("Loading Kaggle audio features dataset...")
    columns_to_keep = [
        'id', 'danceability', 'energy', 'key', 'loudness',
        'mode', 'speechiness', 'acousticness', 'instrumentalness',
        'liveness', 'valence', 'tempo'
    ]
    
    features_df = pd.read_csv(features_dataset_path, usecols=columns_to_keep)
    
    enriched_df = pd.merge(
        unique_tracks_df, features_df, 
        left_on='track_id', right_on='id', how='inner'          
    )
    enriched_df = enriched_df.drop(columns=['id'])
    print(f"Transformation complete! {len(enriched_df)} tracks successfully enriched.")
    return enriched_df

@task(name="Great Expectations Validation")
def validate_data_quality(df):
    print("Running Great Expectations Validation...")
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas("pandas_source")
    data_asset = data_source.add_dataframe_asset(name="pandas_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("batch_def")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    
    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="track_id"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="track_id"),
        gx.expectations.ExpectColumnValuesToBeBetween(column="tempo", min_value=0, max_value=300),
        gx.expectations.ExpectColumnValuesToBeBetween(column="energy", min_value=0.0, max_value=1.0),
        gx.expectations.ExpectColumnValuesToBeBetween(column="valence", min_value=0.0, max_value=1.0),
        gx.expectations.ExpectColumnValuesToBeInSet(column="mode", value_set=[0, 1])
    ]
    
    failed_checks = []
    for exp in expectations:
        result = batch.validate(exp)
        if not result.success:
            failed_checks.append(result)
            
    if failed_checks:
        raise ValueError("CRITICAL ERROR: Data Validation Failed!")
        
    print("Great Expectations: All data quality checks passed!")
    
    # --- NEW ARTIFACT CODE: Pushes this report to your UI! ---
    markdown_report = f"""### 🎵 MelodyMatch Data Quality Report
* **Total Tracks Validated:** {len(df)}
* **Status:** Passed ✅
* **Checks Performed:** Nulls, Uniqueness, Ranges (Tempo, Energy, Valence), Mode Binary
    """
    create_markdown_artifact(
        key="data-quality-report",
        markdown=markdown_report,
        description="Daily ETL Quality Check"
    )
    # ---------------------------------------------------------
    
    return df

@task(name="Load to PostgreSQL (UPSERT)")
def load_to_postgres(df, db_url):
    print("Connecting to local PostgreSQL...")
    engine = create_engine(db_url)
    metadata = MetaData()

    enriched_tracks = Table(
        'enriched_tracks', metadata,
        Column('track_id', String, primary_key=True),
        Column('track_name', String),
        Column('artist', String),
        Column('danceability', Float),
        Column('energy', Float),
        Column('key', Integer),
        Column('loudness', Float),
        Column('mode', Integer),
        Column('speechiness', Float),
        Column('acousticness', Float),
        Column('instrumentalness', Float),
        Column('liveness', Float),
        Column('valence', Float),
        Column('tempo', Float)
    )

    metadata.create_all(engine)
    
    expected_columns = [
        'track_id', 'track_name', 'artist', 'danceability',
        'energy', 'key', 'loudness', 'mode', 'speechiness', 'acousticness',
        'instrumentalness', 'liveness', 'valence', 'tempo'
    ]
    clean_df = df[[col for col in expected_columns if col in df.columns]]

    print("Executing Idempotent UPSERT into PostgreSQL...")
    with engine.begin() as conn:
        data_dicts = clean_df.to_dict(orient='records')
        stmt = insert(enriched_tracks).values(data_dicts)
        on_conflict_stmt = stmt.on_conflict_do_nothing(index_elements=['track_id'])
        conn.execute(on_conflict_stmt)

    print("PIPELINE COMPLETE: Data successfully secured in the database!")

@flow(name="MelodyMatch_ETL_Orchestrator", log_prints=True)
def run_etl_pipeline():
    USER_INTERACTIONS_DATA = "kaggle-user-dataset/clean_data.json" 
    TRACK_FEATURES_DATA = "kaggle-spotify12m/tracks_features.csv"
    
    raw_password = os.getenv("POSTGRES_PASSWORD")
    if not raw_password:
        raise ValueError("CRITICAL: POSTGRES_PASSWORD not found in .env file!")
        
    encoded_password = quote_plus(raw_password)
    
    # --- NEW FIX: Use DB_HOST from Docker, or default to localhost ---
    db_host = os.getenv("DB_HOST", "localhost")
    DB_URL = f"postgresql://postgres:{encoded_password}@{db_host}:5432/spotify_db"
    # -----------------------------------------------------------------
    
    raw_tracks_df = ingest_simulated_users(USER_INTERACTIONS_DATA)
    final_df = enrich_user_tracks(raw_tracks_df, TRACK_FEATURES_DATA)
    validated_df = validate_data_quality(final_df)
    load_to_postgres(validated_df, db_url=DB_URL)

if __name__ == "__main__":
    run_etl_pipeline()