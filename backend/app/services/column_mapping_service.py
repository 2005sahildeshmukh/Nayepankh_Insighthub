import re
from typing import Optional, Tuple
from app.core.standard_fields import get_all_standard_fields

# These are words that are too generic to confidently map automatically.
AMBIGUOUS_TERMS = {"name", "location", "status", "date", "amount", "score", "id"}

class ColumnMappingService:
    @staticmethod
    def normalize_column_name(name: str) -> str:
        # Lowercase, replace non-alphanumeric with underscore, strip
        clean = re.sub(r'[^a-zA-Z0-9]+', '_', str(name).lower()).strip('_')
        return clean

    @staticmethod
    def suggest_mapping(original_name: str) -> Tuple[str, Optional[str]]:
        """
        Returns (mapping_status, standard_field_name)
        mapping_status: "mapped" or "keep"
        standard_field_name: string or None
        """
        name_clean = str(original_name).lower().strip()
        normalized = ColumnMappingService.normalize_column_name(name_clean)
        
        all_fields = get_all_standard_fields()
        
        # 1. Exact match on standard field name
        for field in all_fields:
            if normalized == field["name"]:
                if normalized in AMBIGUOUS_TERMS:
                    return "keep", field["name"] # Suggest but don't map automatically
                return "mapped", field["name"]
                
        # 2. Check explicit aliases
        for field in all_fields:
            for alias in field["aliases"]:
                alias_clean = str(alias).lower().strip()
                if name_clean == alias_clean or normalized == ColumnMappingService.normalize_column_name(alias_clean):
                    if alias_clean in AMBIGUOUS_TERMS:
                        return "keep", field["name"]
                    return "mapped", field["name"]

        # 3. Fuzzy matching / Contains
        for field in all_fields:
            for alias in field["aliases"]:
                alias_clean = str(alias).lower().strip()
                if len(alias_clean) > 4 and alias_clean in name_clean:
                    return "keep", field["name"] # Low confidence, suggest keep

        return "keep", None

