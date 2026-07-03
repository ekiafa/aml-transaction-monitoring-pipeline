from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "eftychia",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="aml_pipeline",
    description="End-to-end AML transaction monitoring pipeline",
    default_args=default_args,
    schedule=None,  # manual trigger for now
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["aml", "dbt", "databricks"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt/aml_lakehouse && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt/aml_lakehouse && dbt test",
    )

    dbt_run >> dbt_test