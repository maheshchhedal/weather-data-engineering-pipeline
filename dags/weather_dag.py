from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/opt/airflow/src/extract")
sys.path.insert(0, "/opt/airflow/src/transform")
sys.path.insert(0, "/opt/airflow/src/load")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="weather_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["weather"],
) as dag:

    def run_extract():
        import pandas as pd
        from datetime import datetime
        from extract import fetch_weather, RAW_DATA_DIR

        data = fetch_weather()
        df = pd.DataFrame(data)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = RAW_DATA_DIR / f"weather_data_{ts}.csv"
        df.to_csv(path, index=False)
        print(f"Saved {len(df)} rows to {path}")

    def run_transform():
        from datetime import datetime
        from transform import transform_data, get_latest_raw_file, PROCESSED_DATA_DIR

        latest = get_latest_raw_file()
        df = transform_data(latest)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = PROCESSED_DATA_DIR / f"weather_processed_{ts}.csv"
        df.to_csv(path, index=False)
        print(f"Saved processed data to {path}")

    def run_load():
        from load import load_data, get_latest_processed_file

        latest = get_latest_processed_file()
        load_data(latest)
        print("Load completed successfully")

    extract_task = PythonOperator(task_id="extract", python_callable=run_extract)
    transform_task = PythonOperator(task_id="transform", python_callable=run_transform)
    load_task = PythonOperator(task_id="load", python_callable=run_load)

    extract_task >> transform_task >> load_task