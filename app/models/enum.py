# app/models/enum.py
from enum import Enum
from sqlalchemy import Enum as SAEnum

# ✅ 1. Python Enum 정의
# (서비스에서 사용하는 OAuth 제공자 목록 — 현재는 google만)
class Provider(str, Enum):
    GOOGLE = "google"

# ✅ 2. SQLAlchemy용 Enum 타입 객체 정의
# name="provider_enum" → DB에 생성될 PostgreSQL ENUM 이름
# native_enum=True → PostgreSQL의 ENUM 타입으로 실제 생성
# create_type=True → Alembic이 ENUM 타입을 새로 생성하게 허용
ProviderSAEnum = SAEnum(
    Provider,
    name="provider_enum",
    native_enum=True,
    create_type=True
)

class InputType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"

InputTypeSAEnum = SAEnum(
    InputType,
    name="input_type_enum",
    native_enum=True,
    create_type=True
)
