from __future__ import annotations
import enum


class IntegrationPlatform(str, enum.Enum):
    GA4 = "ga4"
    META_ADS = "meta_ads"
    HUBSPOT = "hubspot"
    TIKTOK_ADS = "tiktok_ads"
    DV360 = "dv360"
    STACKADAPT = "stackadapt"
    LEADRX = "leadrx"
    LIVERAMP = "liveramp"
    QUORUM = "quorum"
    CANVA = "canva"
    ADOBE_FIREFLY = "adobe_firefly"
    ICON_APP = "icon_app"


class AuthType(str, enum.Enum):
    OAUTH = "oauth"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"


class IntegrationStatus(str, enum.Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    EXPIRED = "expired"
    ERROR = "error"


class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CredentialType(str, enum.Enum):
    OAUTH = "oauth"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"


class CredentialStatus(str, enum.Enum):
    VALID = "valid"
    EXPIRED = "expired"
    ERROR = "error"
    REVOKED = "revoked"


class ConsentPurpose(str, enum.Enum):
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    CROSS_DEVICE = "cross_device"
    DATA_SHARING = "data_sharing"
    AI_PROCESSING = "ai_processing"


class DSARType(str, enum.Enum):
    ACCESS = "access"
    DELETE = "delete"
    EXPORT = "export"
    RECTIFY = "rectify"
    RESTRICT = "restrict"
    PORTABILITY = "portability"


class DSARStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    APPEALED = "appealed"


class Regulation(str, enum.Enum):
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
