from datetime import date, timedelta
from typing import List

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.contacts import ContactModel


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, first_name: str, last_name: str, email: str, skip: int, limit: int, user: User) -> List[Contact]:
        stmt = select(Contact).filter_by(user=user).where(Contact.first_name.contains(first_name)).where(
            Contact.last_name.contains(last_name)).where(
            Contact.email.contains(email)).offset(skip).limit(limit)
        contacts = await self.db.execute(stmt)
        return list(contacts.scalars().all())

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(self, contact_id: int, body: ContactModel, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def is_contact_exists(self, email: str, phone: str) -> bool:
        stmt = select(Contact).where(or_(Contact.email == email, Contact.phone_number == phone))
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def get_upcoming_birthdays(self, days: int = 7) -> List[Contact]:
        today = date.today()
        upcoming_date = today + timedelta(days=days)
        stmt = select(Contact).where(
            Contact.birth_date.is_not(None),
            Contact.birth_date >= today,
            Contact.birth_date <= upcoming_date
        ).order_by(Contact.birth_date.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
