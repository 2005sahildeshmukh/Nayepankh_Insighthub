import os
import joblib
from typing import Any
from pathlib import Path
from app.core.config import settings

# Derive model storage artifacts directory from settings.data_root_dir
STORAGE_DIR = str(settings.data_root_dir / "artifacts" / "models")
os.makedirs(STORAGE_DIR, exist_ok=True)



class MLArtifactService:
    @staticmethod
    def get_artifact_path(experiment_id: str) -> str:
        """
        Returns the absolute path to an experiment's joblib artifact safely.
        """
        # Secure the path by strictly using the ID
        filename = f"{experiment_id}.joblib"
        path = os.path.abspath(os.path.join(STORAGE_DIR, filename))
        
        # Prevent path traversal
        if not path.startswith(os.path.abspath(STORAGE_DIR)):
            raise ValueError("Invalid artifact path traversal attempt.")
        
        return path

    @staticmethod
    def save_pipeline(experiment_id: str, pipeline: Any) -> str:
        """
        Saves a trained sklearn pipeline to the local storage.
        """
        path = MLArtifactService.get_artifact_path(experiment_id)
        
        # Write to temporary file first, then atomically rename
        temp_path = path + ".tmp"
        try:
            joblib.dump(pipeline, temp_path)
            if os.path.exists(path):
                os.remove(path)
            os.rename(temp_path, path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
        return path

    @staticmethod
    def load_pipeline(experiment_id: str) -> Any:
        """
        Loads a trained sklearn pipeline from local storage.
        """
        path = MLArtifactService.get_artifact_path(experiment_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Artifact for experiment {experiment_id} not found.")
        
        return joblib.load(path)

    @staticmethod
    def delete_artifact(experiment_id: str) -> bool:
        """
        Deletes the joblib artifact if it exists.
        """
        path = MLArtifactService.get_artifact_path(experiment_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
