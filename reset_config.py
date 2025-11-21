"""Script para resetear las configuraciones de la base de datos."""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import crud
from services.config_manager import ConfigManager

# Load environment
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sales_bot.db")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def reset_all_configs():
    """Resetear todas las configuraciones a valores vacíos."""
    config_manager = ConfigManager()

    async with AsyncSessionLocal() as db:
        # Obtener todas las configuraciones actuales
        configs = await crud.get_all_configs(db)
        print(f"\nConfiguraciones actuales encontradas: {len(configs)}")

        # Mostrar configuraciones que tienen valores
        for key, value in configs.items():
            if value:
                print(f"  - {key}: {str(value)[:80]}...")

        # Resetear todas las configuraciones al DEFAULT_CONFIG (valores vacíos)
        print(f"\nReseteando todas las configuraciones a valores vacios...")

        for key in config_manager.DEFAULT_CONFIG.keys():
            await crud.set_config(db, key, config_manager.DEFAULT_CONFIG[key])
            print(f"  OK {key} -> (vacio)")

        print(f"\nTodas las configuraciones han sido reseteadas.")
        print(f"\nIMPORTANTE: Ahora debes ir a la pestana 'Configuracion' y configurar el bot antes de usarlo.")


if __name__ == "__main__":
    print("="*60)
    print("RESET DE CONFIGURACIONES")
    print("="*60)
    print("\nEste script limpiará TODAS las configuraciones actuales")
    print("y las reemplazará con valores vacíos.\n")

    confirm = input("¿Estás seguro de que quieres continuar? (si/no): ")

    if confirm.lower() in ["si", "sí", "s", "yes", "y"]:
        asyncio.run(reset_all_configs())
    else:
        print("\n❌ Operación cancelada.")
