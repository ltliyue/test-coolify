from __future__ import annotations
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_platform_db
from app.core.deps import get_current_user
from app.core.permissions import require_permission
from app.models.agency import Agency
from app.models.client import Client
from app.models.user import User
from app.schemas.tenant import AgencyCreate, AgencyResponse, ClientCreate, ClientResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


@router.post("/agencies", response_model=AgencyResponse, status_code=status.HTTP_201_CREATED)
async def create_agency(
    payload: AgencyCreate,
    db: AsyncSession = Depends(get_platform_db),
    _: User = Depends(require_permission("platform.agency.create")),
) -> AgencyResponse:
    base_slug = _slugify(payload.name)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(select(Agency).where(Agency.slug == slug))
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    agency = Agency(
        name=payload.name,
        slug=slug,
        plan=payload.plan,
        monthly_token_budget=payload.monthly_token_budget,
    )
    db.add(agency)
    await db.commit()
    await db.refresh(agency)
    return AgencyResponse.model_validate(agency)


@router.get("/agencies", response_model=list[AgencyResponse])
async def list_agencies(
    db: AsyncSession = Depends(get_platform_db),
    current_user: User = Depends(get_current_user),
) -> list[AgencyResponse]:
    result = await db.execute(
        select(Agency).where(Agency.id == current_user.agency_id)
    )
    agencies = result.scalars().all()
    return [AgencyResponse.model_validate(a) for a in agencies]


@router.get("/agencies/{agency_id}", response_model=AgencyResponse)
async def get_agency(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_platform_db),
    current_user: User = Depends(get_current_user),
) -> AgencyResponse:
    if current_user.agency_id != agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    return AgencyResponse.model_validate(agency)


@router.post(
    "/agencies/{agency_id}/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    agency_id: uuid.UUID,
    payload: ClientCreate,
    db: AsyncSession = Depends(get_platform_db),
    current_user: User = Depends(require_permission("clients.create")),
) -> ClientResponse:
    if current_user.agency_id != agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    base_slug = _slugify(payload.name)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(
            select(Client).where(Client.slug == slug, Client.agency_id == agency_id)
        )
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    client = Client(
        agency_id=agency_id,
        name=payload.name,
        slug=slug,
        verticals=payload.verticals,
        brand_config=payload.brand_config,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return ClientResponse.model_validate(client)


@router.get("/agencies/{agency_id}/clients", response_model=list[ClientResponse])
async def list_clients(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_platform_db),
    current_user: User = Depends(get_current_user),
) -> list[ClientResponse]:
    if current_user.agency_id != agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    result = await db.execute(
        select(Client).where(Client.agency_id == agency_id)
    )
    clients = result.scalars().all()
    return [ClientResponse.model_validate(c) for c in clients]
