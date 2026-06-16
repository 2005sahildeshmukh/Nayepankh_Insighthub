from typing import Dict, Any
from app.models.dataset import DatasetColumn

class AnalyticsRoleService:
    @staticmethod
    def get_column_roles(session, dataset_id: str) -> Dict[str, Dict[str, Any]]:
        cols = session.query(DatasetColumn).filter_by(dataset_id=dataset_id).all()
        roles = {}
        
        for c in cols:
            if c.mapping_status == "exclude":
                continue
                
            name = c.normalized_name
            inferred = c.inferred_type
            std_field = c.standard_field
            
            role = inferred
            is_identifier_like = False
            
            # Explicit overrides
            if std_field in ["id", "volunteer_id", "external_id", "phone", "postal_code"]:
                role = "identifier"
                is_identifier_like = True
            
            name_lower = name.lower()
            id_keywords = ["id", "identifier", "code", "ref", "reference", "phone", "postal", "zip", "number"]
            if any(k in name_lower for k in id_keywords):
                is_identifier_like = True
                if inferred in ["integer", "float", "text"]:
                    role = "identifier"
                    
            if inferred == "boolean":
                # Booleans are categorical dimensions, not measures, even if 0/1
                role = "boolean"
                
            roles[name] = {
                "inferred_type": inferred,
                "role": role,
                "is_identifier_like": is_identifier_like,
                "standard_field": std_field
            }
            
        return roles
