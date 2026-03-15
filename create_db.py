"""Create the saas_multitenant database if it doesn't exist."""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
# Parse password and user from the URL
# Format: postgresql+asyncpg://user:pass@host:port/dbname
parts = DATABASE_URL.replace("postgresql+asyncpg://", "").split("@")
user_pass = parts[0].split(":")
host_db = parts[1].split("/")
host_port = host_db[0].split(":")

user = user_pass[0]
password = ":".join(user_pass[1:])  # Handle passwords with colons
host = host_port[0]
port = int(host_port[1]) if len(host_port) > 1 else 5432
dbname = host_db[1]


async def create_db():
    # Connect to default 'postgres' database
    conn = await asyncpg.connect(user=user, password=password, host=host, port=port, database='postgres')
    try:
        exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = $1", dbname)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
            print(f"✅ Database '{dbname}' created!")
        else:
            print(f"✅ Database '{dbname}' already exists.")
    finally:
        await conn.close()

asyncio.run(create_db())
