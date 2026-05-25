"""create weather table

Revision ID: 0001_create_weather
Revises:
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_weather"
down_revision = None
branch_labels = None
depends_on = None

WIND_DIRECTION_ENUM = sa.Enum(
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
    "VAR",
    "CALM",
    "UNKNOWN",
    name="wind_direction_enum",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "weather",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country", sa.String(length=255)),
        sa.Column("location_name", sa.String(length=255)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("last_updated_date", sa.Date()),
        sa.Column("wind_degree", sa.Integer()),
        sa.Column("wind_kph", sa.Float()),
        sa.Column("wind_direction", WIND_DIRECTION_ENUM),
        sa.Column("sunrise", sa.Time()),
        sa.Column("temperature_celsius", sa.Float()),
        sa.Column("pressure_mb", sa.Float()),
        sa.Column("precip_mm", sa.Float()),
        sa.Column("humidity", sa.Float()),
        sa.Column("air_quality_carbon_monoxide", sa.Float()),
        sa.Column("air_quality_ozone", sa.Float()),
        sa.Column("air_quality_nitrogen_dioxide", sa.Float()),
        sa.Column("air_quality_sulphur_dioxide", sa.Float()),
        sa.Column("air_quality_pm25", sa.Float()),
        sa.Column("air_quality_pm10", sa.Float()),
        sa.Column("air_quality_us_epa_index", sa.Float()),
        sa.Column("air_quality_gb_defra_index", sa.Float()),
    )


def downgrade() -> None:
    op.drop_table("weather")
