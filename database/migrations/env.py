from __future__ import with_statement
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Alembic 설정 객체 - .ini 파일 내의 값에 접근하는 데 사용됩니다.
config = context.config

# Python 로깅을 위한 설정 파일 해석.
# 이 라인은 기본적으로 로거를 설정합니다.
fileConfig(config.config_file_name)

# 모델의 MetaData 객체를 여기에 추가하세요
# 'autogenerate' 지원을 위해
try:
    from app import app, db
    with app.app_context():
        # 모델 import
        import models.user
        import models.meal
        import models.food
        import models.allergy
        import models.recommendation
        import models.chatbot
        import models.ragdata

        target_metadata = db.metadata
except Exception:
    target_metadata = None

# 설정에서 다른 값들도 가져올 수 있습니다.
# 필요에 따라 env.py에서 정의된 값:
# my_important_option = config.get_main_option("my_important_option")
# ... 등등


def run_migrations_offline():
    """'오프라인' 모드에서 마이그레이션 실행.

    이 모드는 Engine 대신 URL만으로 context를 설정합니다.
    물론 Engine도 사용 가능합니다. Engine 생성을 건너뛰므로
    DBAPI가 필요하지 않습니다.

    여기서 context.execute()를 호출하면 주어진 문자열이
    스크립트 출력에 표시됩니다.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """'온라인' 모드에서 마이그레이션 실행.

    이 시나리오에서는 Engine을 생성하고
    context와 연결해야 합니다.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()