"""Initial migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Create files table
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('content_type', sa.String(255), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('s3_key', sa.String(1000), nullable=False),
        sa.Column('s3_bucket', sa.String(255), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_s3_key'), 'files', ['s3_key'], unique=True)
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    
    # Create file_permissions table
    op.create_table(
        'file_permissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('file_id', sa.Integer(), sa.ForeignKey('files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_level', sa.Enum('read', 'write', 'admin', name='permissionlevel'), nullable=False),
        sa.Column('can_download', sa.Boolean(), nullable=False, default=True),
        sa.Column('can_share', sa.Boolean(), nullable=False, default=False),
        sa.Column('granted_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_permissions_id'), 'file_permissions', ['id'], unique=False)
    
    # Create share_links table
    op.create_table(
        'share_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('file_id', sa.Integer(), sa.ForeignKey('files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_downloads', sa.Integer(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('requires_auth', sa.Boolean(), nullable=False, default=False),
        sa.Column('allowed_email', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_share_links_token'), 'share_links', ['token'], unique=True)
    op.create_index(op.f('ix_share_links_id'), 'share_links', ['id'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.Enum(
            'login_success', 'login_failed', 'logout', 'token_refresh', 'password_change',
            'user_create', 'user_update', 'user_delete', 'role_assign',
            'file_upload', 'file_download', 'file_delete', 'file_update',
            'share_create', 'share_access', 'share_revoke',
            'permission_grant', 'permission_revoke',
            name='auditaction'
        ), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='success'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('share_links')
    op.drop_table('file_permissions')
    op.drop_table('files')
    op.drop_table('users')
    op.drop_table('roles')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS auditaction')
    op.execute('DROP TYPE IF EXISTS permissionlevel')
