from __future__ import annotations

import argparse
import enum
import os
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    create_engine,
    func,
    inspect,
    text,
)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH_DEFAULT = BASE_DIR / "GlobalWeatherRepository.csv"

load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

Base = declarative_base()

class WindDirection(str, enum.Enum):
    N = "N"
    NNE = "NNE"
    NE = "NE"
    ENE = "ENE"
    E = "E"
    ESE = "ESE"
    SE = "SE"
    SSE = "SSE"
    S = "S"
    SSW = "SSW"
    SW = "SW"
    WSW = "WSW"
    W = "W"
    WNW = "WNW"
    NW = "NW"
    NNW = "NNW"
    VAR = "VAR"
    CALM = "CALM"
    UNKNOWN = "UNKNOWN"

WIND_DIRECTION_VALUES = {member.value for member in WindDirection}
WIND_DIRECTION_TYPE = Enum(
    *sorted(WIND_DIRECTION_VALUES),
    name="wind_direction_enum",
    native_enum=False,
)

class Weather(Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True)
    country = Column(String(255))
    location_name = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    last_updated_date = Column(Date)
    wind_degree = Column(Integer)
    wind_kph = Column(Float)
    wind_direction = Column(WIND_DIRECTION_TYPE)
    sunrise = Column(Time)
    temperature_celsius = Column(Float)
    pressure_mb = Column(Float)
    precip_mm = Column(Float)
    humidity = Column(Float)

    air_quality = relationship("AirQuality", back_populates="weather", uselist=False)

class AirQuality(Base):
    __tablename__ = "air_quality"

    weather_id = Column(Integer, ForeignKey("weather.id", ondelete="CASCADE"), primary_key=True)
    air_quality_carbon_monoxide = Column(Float)
    air_quality_ozone = Column(Float)
    air_quality_nitrogen_dioxide = Column(Float)
    air_quality_sulphur_dioxide = Column(Float)
    air_quality_pm25 = Column(Float)
    air_quality_pm10 = Column(Float)
    air_quality_us_epa_index = Column(Float)
    air_quality_gb_defra_index = Column(Float)
    go_outside = Column(Boolean, nullable=False, default=False)

    weather = relationship("Weather", back_populates="air_quality")

@dataclass(frozen=True)
class DbTarget:
    name: str
    url: str
    alembic_ini: str

def _build_postgres_url() -> str:
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise RuntimeError("DB_PASSWORD is not set in .env")

    db = os.getenv("POSTGRES_DB", "lab3BDsem2")
    user = os.getenv("POSTGRES_USER", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{db}"

def _build_mysql_url() -> str:
    password = os.getenv("MYSQL_PASSWORD")
    if not password:
        raise RuntimeError("MYSQL_PASSWORD is not set in .env")

    driver = os.getenv("MYSQL_DRIVER", "pymysql")
    if driver == "pymysql":
        try:
            password.encode("latin1")
        except UnicodeEncodeError as exc:
            raise RuntimeError(
                "MYSQL_PASSWORD contains non-latin1 characters. "
                "PyMySQL cannot authenticate with such password. "
                "Use an ASCII/latin1 MySQL password or set MYSQL_DRIVER to another driver."
            ) from exc

    db = os.getenv("MYSQL_DB", "lab3BDsem2")
    user = os.getenv("MYSQL_USER", "root")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    return f"mysql+{driver}://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{db}"

def resolve_targets(target_name: str) -> list[DbTarget]:
    names = ["postgres", "mysql"] if target_name == "both" else [target_name]
    targets: list[DbTarget] = []

    for name in names:
        try:
            if name == "postgres":
                targets.append(
                    DbTarget(name="postgres", url=_build_postgres_url(), alembic_ini="alembic_postgres.ini")
                )
            elif name == "mysql":
                targets.append(DbTarget(name="mysql", url=_build_mysql_url(), alembic_ini="alembic_mysql.ini"))
            else:
                raise RuntimeError(f"Unknown target: {name}")
        except Exception as exc:
            if target_name == "both":
                continue
            raise

    if not targets:
        raise RuntimeError("No available database targets.")
    return targets

def _ensure_database_exists(target: DbTarget) -> None:
    url = make_url(target.url)
    db_name = url.database
    if not db_name:
        raise RuntimeError(f"Database name is missing for target '{target.name}'.")

    if target.name == "postgres":
        admin_url = url.set(database="postgres")
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        try:
            with engine.connect() as conn:
                exists = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname=:db_name"),
                    {"db_name": db_name},
                ).scalar()
                if not exists:
                    conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        finally:
            engine.dispose()
        return

    if target.name == "mysql":
        admin_url = url.set(database="mysql")
        engine = create_engine(admin_url)
        try:
            with engine.begin() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
        finally:
            engine.dispose()
        return

    raise RuntimeError(f"Unsupported database target '{target.name}'.")

def _normalize_wind_direction(value: object) -> str:
    if value is None:
        return WindDirection.UNKNOWN.value
    normalized = str(value).strip().upper()
    if normalized in WIND_DIRECTION_VALUES:
        return normalized
    return WindDirection.UNKNOWN.value

def _parse_sunrise(series: pd.Series) -> pd.Series:
    parsed_primary = pd.to_datetime(series, format="%I:%M %p", errors="coerce")
    missing_mask = parsed_primary.isna()
    if missing_mask.any():
        parsed_24h = pd.to_datetime(series[missing_mask], format="%H:%M", errors="coerce")
        parsed_primary.loc[missing_mask] = parsed_24h
    return parsed_primary.dt.time

def prepare_frames(csv_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(csv_path)

    rename_map = {
        "air_quality_Carbon_Monoxide": "air_quality_carbon_monoxide",
        "air_quality_Ozone": "air_quality_ozone",
        "air_quality_Nitrogen_dioxide": "air_quality_nitrogen_dioxide",
        "air_quality_Sulphur_dioxide": "air_quality_sulphur_dioxide",
        "air_quality_PM2.5": "air_quality_pm25",
        "air_quality_PM10": "air_quality_pm10",
        "air_quality_us-epa-index": "air_quality_us_epa_index",
        "air_quality_gb-defra-index": "air_quality_gb_defra_index",
    }
    df = df.rename(columns=rename_map)

    df["id"] = range(1, len(df) + 1)
    df["last_updated_date"] = pd.to_datetime(df["last_updated"], errors="coerce").dt.date
    df["wind_degree"] = pd.to_numeric(df["wind_degree"], errors="coerce").fillna(0).round().astype(int)
    df["wind_kph"] = pd.to_numeric(df["wind_kph"], errors="coerce").fillna(0.0)
    df["wind_direction"] = df["wind_direction"].apply(_normalize_wind_direction)
    df["sunrise"] = _parse_sunrise(df["sunrise"]).apply(
        lambda value: value if isinstance(value, time) else time(0, 0)
    )

    numeric_cols = [
        "latitude",
        "longitude",
        "temperature_celsius",
        "pressure_mb",
        "precip_mm",
        "humidity",
        "air_quality_carbon_monoxide",
        "air_quality_ozone",
        "air_quality_nitrogen_dioxide",
        "air_quality_sulphur_dioxide",
        "air_quality_pm25",
        "air_quality_pm10",
        "air_quality_us_epa_index",
        "air_quality_gb_defra_index",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["country"] = df["country"].fillna("UNKNOWN").astype(str)
    df["location_name"] = df["location_name"].fillna("UNKNOWN").astype(str)
    df["last_updated_date"] = df["last_updated_date"].apply(
        lambda value: value if isinstance(value, date) else date(1970, 1, 1)
    )

    weather_cols = [
        "id",
        "country",
        "location_name",
        "latitude",
        "longitude",
        "last_updated_date",
        "wind_degree",
        "wind_kph",
        "wind_direction",
        "sunrise",
        "temperature_celsius",
        "pressure_mb",
        "precip_mm",
        "humidity",
    ]

    air_cols = [
        "air_quality_carbon_monoxide",
        "air_quality_ozone",
        "air_quality_nitrogen_dioxide",
        "air_quality_sulphur_dioxide",
        "air_quality_pm25",
        "air_quality_pm10",
        "air_quality_us_epa_index",
        "air_quality_gb_defra_index",
    ]

    weather_df = df[weather_cols].copy()
    air_quality_df = df[["id"] + air_cols].copy().rename(columns={"id": "weather_id"})
    air_quality_df["go_outside"] = (
        (air_quality_df["air_quality_pm25"] <= 35)
        & (air_quality_df["air_quality_pm10"] <= 50)
        & (air_quality_df["air_quality_us_epa_index"] <= 2)
    )
    return weather_df, air_quality_df

def run_migrations(target: DbTarget) -> None:
    _ensure_database_exists(target)
    config = AlembicConfig(str(BASE_DIR / target.alembic_ini))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", target.url.replace("%", "%%"))
    alembic_command.upgrade(config, "head")

def _ensure_tables_exist(engine) -> None:
    inspector = inspect(engine)
    required = {"weather", "air_quality"}
    existing = set(inspector.get_table_names())
    missing = required - existing
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise RuntimeError(f"Missing tables: {missing_str}. Run migrations first.")

def load_data(target: DbTarget, weather_df: pd.DataFrame, air_quality_df: pd.DataFrame) -> None:
    engine = create_engine(target.url)
    try:
        _ensure_tables_exist(engine)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM air_quality"))
            conn.execute(text("DELETE FROM weather"))

        weather_df.to_sql("weather", con=engine, if_exists="append", index=False, method="multi", chunksize=2000)
        air_quality_df.to_sql(
            "air_quality", con=engine, if_exists="append", index=False, method="multi", chunksize=2000
        )
    finally:
        engine.dispose()

class WeatherRepository:
    def __init__(self, session):
        self.session = session

    def get_by_country_date(
        self,
        country: str,
        day_value: date,
        city: str | None = None,
        go_outside: bool | None = None,
    ):
        query = (
            self.session.query(Weather, AirQuality)
            .join(AirQuality, Weather.id == AirQuality.weather_id)
            .filter(
                func.lower(Weather.country) == country.lower(),
                Weather.last_updated_date == day_value,
            )
        )
        if city:
            query = query.filter(func.lower(Weather.location_name) == city.lower())
        if go_outside is not None:
            query = query.filter(AirQuality.go_outside == go_outside)
        return query.all()

    def get_by_country_city(self, country: str, city: str):
        return (
            self.session.query(Weather, AirQuality)
            .join(AirQuality, Weather.id == AirQuality.weather_id)
            .filter(
                func.lower(Weather.country) == country.lower(),
                func.lower(Weather.location_name) == city.lower(),
            )
            .all()
        )

class WeatherService:
    def __init__(self, repository: WeatherRepository):
        self.repository = repository

    def report_by_country_date(
        self,
        country: str,
        day_value: date,
        city: str | None = None,
        go_outside: bool | None = None,
    ) -> list[dict]:
        rows = self.repository.get_by_country_date(country, day_value, city=city, go_outside=go_outside)
        return self._rows_to_dict(rows)

    def report_by_country_city(self, country: str, city: str) -> list[dict]:
        rows = self.repository.get_by_country_city(country, city)
        return self._rows_to_dict(rows)

    @staticmethod
    def _rows_to_dict(rows) -> list[dict]:
        result = []
        for weather, air in rows:
            result.append(
                {
                    "country": weather.country,
                    "location_name": weather.location_name,
                    "date": weather.last_updated_date.isoformat() if weather.last_updated_date else None,
                    "sunrise": weather.sunrise.isoformat() if weather.sunrise else None,
                    "wind_degree": weather.wind_degree,
                    "wind_kph": weather.wind_kph,
                    "wind_direction": weather.wind_direction,
                    "temperature_celsius": weather.temperature_celsius,
                    "pressure_mb": weather.pressure_mb,
                    "precip_mm": weather.precip_mm,
                    "humidity": weather.humidity,
                    "air_quality_pm25": air.air_quality_pm25,
                    "air_quality_pm10": air.air_quality_pm10,
                    "air_quality_us_epa_index": air.air_quality_us_epa_index,
                    "go_outside": air.go_outside,
                }
            )
        return result

def _target_to_engine(target: DbTarget):
    return create_engine(target.url)

def _with_service(target: DbTarget) -> tuple[object, WeatherService]:
    engine = _target_to_engine(target)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    repository = WeatherRepository(session)
    service = WeatherService(repository)
    return session, service

def query_by_date(
    target: DbTarget,
    country: str,
    date_text: str,
    city: str | None = None,
    go_outside: bool | None = None,
) -> list[dict]:
    day_value = datetime.strptime(date_text, "%Y-%m-%d").date()
    session, service = _with_service(target)
    try:
        return service.report_by_country_date(country, day_value, city=city, go_outside=go_outside)
    finally:
        session.close()

def query_by_city(target: DbTarget, country: str, city: str) -> list[dict]:
    session, service = _with_service(target)
    try:
        return service.report_by_country_city(country, city)
    finally:
        session.close()

def run_console(target: DbTarget) -> None:
    while True:
        choice = input("1=country+date, 2=country+city, q=quit: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            break
        if choice == "1":
            country = input("Country: ").strip()
            day_text = input("Date (YYYY-MM-DD): ").strip()
            city = input("City (optional): ").strip()
            go_outside_text = input("go_outside yes/no (optional): ").strip().lower()
            go_outside = None
            if go_outside_text in {"yes", "y", "true", "1"}:
                go_outside = True
            elif go_outside_text in {"no", "n", "false", "0"}:
                go_outside = False
            try:
                rows = query_by_date(
                    target,
                    country,
                    day_text,
                    city=city or None,
                    go_outside=go_outside,
                )
                if not rows:
                    print("No results.")
                for row in rows:
                    print(row)
            except Exception as exc:  
                print(f"Error: {exc}")
        elif choice == "2":
            country = input("Country: ").strip()
            city = input("City: ").strip()
            try:
                rows = query_by_city(target, country, city)
                if not rows:
                    print("No results.")
                for row in rows:
                    print(row)
            except Exception as exc:  
                print(f"Error: {exc}")
        else:
            print("Unknown option. Use 1, 2, or q.")

def _run_for_targets(
    targets: list[DbTarget],
    action_name: str,
    action,
    *,
    raise_on_failure: bool = True,
) -> tuple[list[DbTarget], list[str]]:
    successes: list[DbTarget] = []
    failures: list[str] = []
    for target in targets:
        try:
            action(target)
            successes.append(target)
        except Exception as exc:
            failures.append(f"{target.name}: {exc}")

    if failures and raise_on_failure:
        details = "\n".join(failures)
        raise RuntimeError(f"{action_name} finished with errors:\n{details}")
    return successes, failures

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lab 3 weather migration application")
    subparsers = parser.add_subparsers(dest="command", required=True)

    migrate_parser = subparsers.add_parser("migrate", help="Run Alembic migrations")
    migrate_parser.add_argument("--target", choices=["postgres", "mysql", "both"], default="both")

    setup_parser = subparsers.add_parser(
        "setup", help="Run migrations and load CSV data into selected databases"
    )
    setup_parser.add_argument("--target", choices=["postgres", "mysql", "both"], default="both")
    setup_parser.add_argument("--csv", default=str(CSV_PATH_DEFAULT))

    date_parser = subparsers.add_parser("query-date", help="Query by country and date")
    date_parser.add_argument("--target", choices=["postgres", "mysql"], default="postgres")
    date_parser.add_argument("--country", required=True)
    date_parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    date_parser.add_argument("--city")
    date_parser.add_argument("--go-outside", choices=["yes", "no"])

    city_parser = subparsers.add_parser("query-city", help="Query by country and city")
    city_parser.add_argument("--target", choices=["postgres", "mysql"], default="postgres")
    city_parser.add_argument("--country", required=True)
    city_parser.add_argument("--city", required=True)

    console_parser = subparsers.add_parser("console", help="Interactive console")
    console_parser.add_argument("--target", choices=["postgres", "mysql"], default="postgres")

    return parser.parse_args()

def main() -> None:
    args = _parse_args()

    if args.command == "migrate":
        targets = resolve_targets(args.target)
        _run_for_targets(targets, "migrate", run_migrations)
        return

    if args.command == "setup":
        targets = resolve_targets(args.target)
        weather_df, air_quality_df = prepare_frames(Path(args.csv))
        migrated_targets, migrate_failures = _run_for_targets(
            targets, "migrate", run_migrations, raise_on_failure=False
        )
        loaded_targets, load_failures = _run_for_targets(
            migrated_targets,
            "load",
            lambda target: load_data(target, weather_df, air_quality_df),
            raise_on_failure=False,
        )

        all_failures = migrate_failures + load_failures
        if all_failures:
            details = "\n".join(all_failures)
            raise RuntimeError(f"setup finished with errors:\n{details}")
        return

    if args.command == "query-date":
        target = resolve_targets(args.target)[0]
        go_outside = None
        if args.go_outside == "yes":
            go_outside = True
        elif args.go_outside == "no":
            go_outside = False
        rows = query_by_date(target, args.country, args.date, city=args.city, go_outside=go_outside)
        if not rows:
            print("No results.")
        for row in rows:
            print(row)
        return

    if args.command == "query-city":
        target = resolve_targets(args.target)[0]
        rows = query_by_city(target, args.country, args.city)
        if not rows:
            print("No results.")
        for row in rows:
            print(row)
        return

    if args.command == "console":
        target = resolve_targets(args.target)[0]
        run_console(target)
        return

    raise RuntimeError(f"Unsupported command: {args.command}")

if __name__ == "__main__":
    main()