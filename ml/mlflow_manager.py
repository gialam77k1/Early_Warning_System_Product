import mlflow
import mlflow.sklearn
import os
import json
from datetime import datetime

class MLflowManager:
    """Quản lý việc log experiments lên MLflow"""
    
    def __init__(self, experiment_name="Early_Warning_System"):
        # Tự động nhận diện host MLflow
        # Nếu ở trong Docker, host là 'mlflow', nếu ở ngoài là '127.0.0.1'
        host = "mlflow" if os.environ.get("RUNNING_IN_DOCKER") == "true" else "127.0.0.1"
        mlflow.set_tracking_uri(f"http://{host}:5050")
        
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)
        
    def start_run(self, run_name=None):
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return mlflow.start_run(run_name=run_name)
    
    def log_params(self, params):
        mlflow.log_params(params)
        
    def log_metrics(self, metrics):
        mlflow.log_metrics(metrics)
        
    def log_model(self, model, artifact_path="model"):
        mlflow.sklearn.log_model(model, artifact_path)
        
    def log_artifact(self, local_path):
        mlflow.log_artifact(local_path)

    def end_run(self):
        mlflow.end_run()
