from fastapi import APIRouter
from app.core.standard_fields import STANDARD_FIELD_GROUPS

router = APIRouter(prefix="/standard-fields", tags=["Standard Fields"])

@router.get("")
def get_standard_fields():
    return STANDARD_FIELD_GROUPS
