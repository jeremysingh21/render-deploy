from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Boolean, JSON
from app import db
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import String, Integer, DateTime, Float
import secrets
from sqlalchemy.ext.hybrid import hybrid_property
from typing import List


class Saved_Searches(db.Model):
    __tablename__ = 'saved_searches'
    __table_args__ = {'schema': 'favorites'}

    search_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('react_users.user_id'))
    search_name: Mapped[str] = mapped_column(String(100))
    search_criteria: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    
    @hybrid_property
    def serialized(self):
        return {
            'search_id': self.search_id,
            'user_id': self.user_id,
            'search_name': self.search_name,
            'search_criteria': self.search_criteria,
            'created_at': self.created_at,
        }
class Saved_Listings(db.Model):
    __tablename__ = 'saved_listings'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'hash_id', name='uq_user_listing'),
        {'schema': 'favorites'}
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('react_users.user_id'))
    hash_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    
    @hybrid_property
    def serialized(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hash_id': self.hash_id,
            'created_at': self.created_at
        }
  
class Permissions:
    API_ACCESS = 0x01
    # ... other permissions ...

class React_Roles(db.Model):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    permissions: Mapped[int] = mapped_column(Integer, nullable=False)
    default_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    @hybrid_property
    def serialized(self):
        return {
            'id': self.id,
            'name': self.name,
            'permissions': self.permissions,
            'default_role': self.default_role
        }
    def has_permission(self, permission):
        return self.permissions & permission == permission
    def has_api_access(self):
        return self.permissions & Permissions.API_ACCESS == Permissions.API_ACCESS

class User_React(db.Model):
    __tablename__ = 'react_users'

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(256), nullable=True)
    last_name: Mapped[str] = mapped_column(String(256), nullable=True)
    company_name: Mapped[str] = mapped_column(String(256), nullable=True)
    email_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id'), nullable=False)
    role: Mapped[React_Roles] = relationship("React_Roles", backref="users")
    phone: Mapped[str] = mapped_column(String(15), nullable=True)
    user_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    
    subscriptions: Mapped[List["UserSubscription"]] = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    one_time_purchases: Mapped[List["OneTimePurchase"]] = relationship("OneTimePurchase", back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[List["ApiKey"]] = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, username: str, email: str, password: str, email_confirmed: bool = False, first_name: str = None, last_name: str = None, company_name: str = None, 
                 phone: str = None,
                 user_status: bool = True):
        self.username = username
        self.email = email
        self.email_confirmed = email_confirmed
        self.first_name = first_name
        self.last_name = last_name
        self.company_name = company_name
        self.phone = self.clean_phone(phone)
        self.user_status = user_status
        self.set_password(password)
        self.set_default_role()

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    def set_default_role(self):
        default_role = React_Roles.query.filter_by(default_role=True).first()
        if default_role:
            self.role_id = default_role.id
        else:
            # If no default role is set, assign the "Free" role (id=3)
            self.role_id = 3

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def clean_phone(self, phone: str) -> str:
        """Clean and format the phone number."""
        if phone:
            # Example of basic formatting: remove non-numeric characters
            return ''.join(filter(str.isdigit, phone))[:15]  # Limit to 15 digits
        return None


class ApiKey(db.Model):
    __tablename__ = 'apikeys'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer,ForeignKey('react_users.user_id', ondelete='CASCADE'),nullable=False)    
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    last_used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User_React] = relationship("User_React", back_populates="api_keys")

    @classmethod
    def generate_key(cls):
        return secrets.token_urlsafe(48)

    @staticmethod
    def validate_api_key(api_key):
        return ApiKey.query.filter_by(key=api_key).first() is not None

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    __table_args__ = {'schema': 'stripe'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer,ForeignKey('react_users.user_id', ondelete='CASCADE'),nullable=False)    
    stripe_subscription_id: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    user: Mapped[User_React] = relationship('User_React', back_populates='subscriptions')

class OneTimePurchase(db.Model):

    __tablename__ = 'one_time_purchases'
    __table_args__ = {'schema': 'stripe'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('react_users.user_id'), nullable=False)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(100), nullable=True)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    search_query: Mapped[dict] = mapped_column(JSON, nullable=True)
    s3_url: Mapped[dict] = mapped_column(JSON, nullable=True)  # Changed to JSON type
    file_types: Mapped[list] = mapped_column(JSON, nullable=True)  # New column to store selected file types
    user: Mapped[User_React] = relationship('User_React', back_populates='one_time_purchases')

    @hybrid_property
    def serialized(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'status': self.status,
            'search_query': self.search_query,
            's3_url': self.s3_url,
            'file_types': self.file_types
        }

class Listings(db.Model):
    __bind_key__ = 'listings'  # Add this line to specify the database binding
    __tablename__ = 'listings'
    __table_args__ = {'schema': 'listings'}

    link: Mapped[str] = mapped_column(String)
    company_name: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float)
    long: Mapped[float] = mapped_column(Float)
    hash_id: Mapped[str] = mapped_column(String(255), primary_key=True)
# In your models.py, add index=True to these columns
    geog_state: Mapped[str] = mapped_column(String(256), index=True)
    geog_city: Mapped[str] = mapped_column(String, index=True)
    geog_county: Mapped[str] = mapped_column(String, index=True)
    geog_zip: Mapped[str] = mapped_column(String(40), index=True)
    date_updated: Mapped[datetime] = mapped_column(DateTime)
    ac_0_1: Mapped[bool]
    ac_1_5: Mapped[bool]
    ac_5_10: Mapped[bool]
    ac_10_25: Mapped[bool]
    ac_25_50: Mapped[bool]
    ac_50_100: Mapped[bool]
    ac_100_plus: Mapped[bool]
    ac_raw_values: Mapped[str]
    sf_0_1: Mapped[bool]
    sf_1_5: Mapped[bool]
    sf_5_10: Mapped[bool]
    sf_10_25: Mapped[bool]
    sf_25_50: Mapped[bool]
    sf_50_100: Mapped[bool]
    sf_100_plus: Mapped[bool]
    sf_raw_values: Mapped[str]
    sf_range_pairs: Mapped[str]
    ac_range_pairs: Mapped[str]
    property_type: Mapped[str]
    transaction_sale: Mapped[bool]
    transaction_lease: Mapped[bool]
    brochure_link: Mapped[str]
    broker: Mapped[str]
    google_streetview_link: Mapped[str]
    phone: Mapped[str]
    email: Mapped[str]
    date_created: Mapped[datetime] = mapped_column(DateTime)
    days_on_cnvsd: Mapped[int]
    min_sf_available: Mapped[int]
    max_sf_available: Mapped[int]
    min_ac_available: Mapped[float]
    max_ac_available: Mapped[float]

    def __init__(self, link: str, company_name: str, address: str, lat: float, long: float, hash_id: str, 
                 geog_city: str, geog_county: str, geog_state: str, geog_zip: str, date_updated: datetime, 
                 ac_0_1: bool, ac_1_5: bool, ac_5_10: bool, ac_10_25: bool, ac_25_50: bool, ac_50_100: bool, 
                 ac_100_plus: bool, ac_raw_values: str, sf_0_1: bool, sf_1_5: bool, sf_5_10: bool, 
                 sf_10_25: bool, sf_25_50: bool, sf_50_100: bool, sf_100_plus: bool, sf_raw_values: str, 
                 sf_range_pairs: str, ac_range_pairs: str, property_type: str, transaction_sale: bool, 
                 transaction_lease: bool, brochure_link: str, broker: str, google_streetview_link: str, phone: str, 
                 email: str, date_created: datetime, days_on_cnvsd: int, min_sf_available: int, max_sf_available: int, 
                 min_ac_available: float, max_ac_available: float):
        self.link = link
        self.company_name = company_name
        self.address = address
        self.lat = lat
        self.long = long
        self.hash_id = hash_id
        self.geog_city = geog_city
        self.geog_county = geog_county
        self.geog_state = geog_state
        self.geog_zip = geog_zip
        self.date_updated = date_updated
        self.ac_0_1 = ac_0_1
        self.ac_1_5 = ac_1_5
        self.ac_5_10 = ac_5_10
        self.ac_10_25 = ac_10_25
        self.ac_25_50 = ac_25_50
        self.ac_50_100 = ac_50_100
        self.ac_100_plus = ac_100_plus
        self.ac_raw_values = ac_raw_values
        self.sf_0_1 = sf_0_1
        self.sf_1_5 = sf_1_5
        self.sf_5_10 = sf_5_10
        self.sf_10_25 = sf_10_25
        self.sf_25_50 = sf_25_50
        self.sf_50_100 = sf_50_100
        self.sf_100_plus = sf_100_plus
        self.sf_raw_values = sf_raw_values
        self.sf_range_pairs = sf_range_pairs
        self.ac_range_pairs = ac_range_pairs
        self.property_type = property_type
        self.transaction_sale = transaction_sale
        self.transaction_lease = transaction_lease
        self.brochure_link = brochure_link
        self.broker = broker
        self.google_streetview_link = google_streetview_link
        self.phone = phone
        self.email = email
        self.date_created = date_created
        self.days_on_cnvsd = days_on_cnvsd
        self.min_sf_available = min_sf_available
        self.max_sf_available = max_sf_available
        self.min_ac_available = min_ac_available
        self.max_ac_available = max_ac_available

    def __repr__(self) -> str:
        return f'<Listing {self.link}>'

    def clean_transaction_type(self):
        if self.transaction_sale and self.transaction_lease:
            return 'Sale or Lease'
        elif self.transaction_sale:
            return 'Sale'
        elif self.transaction_lease:
            return 'Lease'
        else:
            return None
        
    def clean_property_type(self):
        if self.property_type:
            self.property_type = self.property_type.strip("[]").strip("'\" ").replace("'","").title()
        return self.property_type
    
    def clean_broker(self):
        if self.broker:
            self.broker = self.broker.strip("[]").strip("'\" ").replace("'","").title()
        return self.broker
    
    def clean_email(self):
        if self.email:
            self.email = self.email.strip("[]").strip("'\" ").replace("'","").title()
        return self.email
    
    def clean_phone(self):
        if self.phone:
            self.phone = self.phone.strip("[]").strip("'\" ").replace("'","").title()
        return self.phone
    
    @hybrid_property
    def serialized(self):
        return {
            'Link': self.link,
            'Company Name': self.company_name,
            'Address': self.address,
            'Latitude': self.lat,
            'Longitude': self.long,
            'Hash ID': self.hash_id,
            'City': self.geog_city,
            'County': self.geog_county,
            'State': self.geog_state,
            'ZIP Code': self.geog_zip,
            'Last Updated': self.date_updated.isoformat() if self.date_updated else None,
            'Property Type': self.clean_property_type(),
            'Transaction Type': self.clean_transaction_type(),
            'Brochure Link': self.brochure_link,
            'Broker': self.clean_broker(),
            'Street View': self.google_streetview_link,
            'Phone': self.clean_phone(),
            'Email': self.clean_email(),
            'Date Created': self.date_created.isoformat() if self.date_created else None,
            'Days on Market': self.days_on_cnvsd,
            'Min Sq Ft Available': self.min_sf_available,
            'Max Sq Ft Available': self.max_sf_available,
            'Min Acres Available': self.min_ac_available,
            'Max Acres Available': self.max_ac_available
        }