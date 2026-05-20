from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.db import get_engine
from app.services.data_loader import load_csv_folder_to_database


def main() -> None:
    settings = get_settings()
    engine = get_engine()
    loaded = load_csv_folder_to_database(engine, Path(settings.sample_data_dir))
    print("Database initialized successfully.")
    for table, count in loaded.items():
        print(f"  {table}: {count} rows")


if __name__ == "__main__":
    main()
