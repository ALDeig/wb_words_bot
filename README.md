# tgbot_template

## Alembic
`alembic init alembic`

in env.py import Base from models.models
add function in env.py

    def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()
        
change function run_migrations_online:

    async def run_migrations_online():
        """Run migrations in 'online' mode.

        In this scenario we need to create an Engine
        and associate a connection with the context.

        """
        url = config.get_main_option("sqlalchemy.url")
        connectable = AsyncEngine(
            create_engine(
                url,
                poolclass=pool.NullPool,
                future=True,
            )
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)


    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())

`alembic revision --message="Create tables" --autogenerate`

`alembic upgrade head`
