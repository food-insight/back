"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# Alembic에서 사용하는 리비전 식별자
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    """
    스키마 업그레이드 함수:
    이 함수는 마이그레이션 적용 시 실행됩니다.
    """
    ${upgrades if upgrades else "pass"}


def downgrade():
    """
    스키마 다운그레이드 함수:
    이 함수는 마이그레이션 롤백 시 실행됩니다.
    """
    ${downgrades if downgrades else "pass"}