"""fix user composite key for multi-tenant phone numbers

Revision ID: fix_user_composite_key
Revises: fca1930d8a4d
Create Date: 2025-11-15 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fix_user_composite_key'
down_revision: Union[str, None] = 'fca1930d8a4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add id column to users table (will become primary key)
    op.add_column('users', sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    
    # Step 2: Drop the old foreign key constraint from user_messages to users.phone_no (if exists)
    try:
        op.drop_constraint('user_messages_phone_no_fkey', 'user_messages', type_='foreignkey')
    except Exception:
        pass  # Constraint might not exist
    
    # Step 3: Drop old unique index on phone_no in users table
    op.drop_index('ix_users_phone_no', 'users')
    
    # Step 4: Drop phone_no as primary key from users
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # Step 5: Make id the new primary key of users
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # Step 6: Create composite unique constraint on (phone_no, tenant_id)
    # This allows same phone_no for different tenants, but unique within a tenant
    op.create_unique_constraint('uq_user_phone_tenant', 'users', ['phone_no', 'tenant_id'])
    
    # Step 7: Re-create index on phone_no (non-unique now)
    op.create_index('ix_users_phone_no', 'users', ['phone_no'])
    
    # Step 8: Create composite index on user_messages for fast queries by (tenant_id, phone_no)
    op.create_index('ix_user_messages_tenant_phone', 'user_messages', ['tenant_id', 'phone_no'])


def downgrade() -> None:
    # Reverse the changes
    op.drop_index('ix_user_messages_tenant_phone', 'user_messages')
    op.drop_index('ix_users_phone_no', 'users')
    
    op.drop_constraint('uq_user_phone_tenant', 'users', type_='unique')
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # Restore phone_no as primary key
    op.create_primary_key('users_pkey', 'users', ['phone_no'])
    
    # Restore unique index on phone_no
    op.create_index('ix_users_phone_no', 'users', ['phone_no'], unique=True)
    
    # Restore foreign key from user_messages to users.phone_no (if it existed)
    try:
        op.create_foreign_key('user_messages_phone_no_fkey', 'user_messages', 'users', ['phone_no'], ['phone_no'])
    except Exception:
        pass
    
    # Drop id column from users
    op.drop_column('users', 'id')
