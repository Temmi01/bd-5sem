"""split air_quality table

Revision ID: 0002_split_air_quality
Revises: 0001_create_weather
Create Date: 2026-05-16 
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_split_air_quality"
down_revision = "0001_create_weather"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "air_quality",
        sa.Column(
            "weather_id",
            sa.Integer(),
            sa.ForeignKey("weather.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("air_quality_carbon_monoxide", sa.Float()),
        sa.Column("air_quality_ozone", sa.Float()),
        sa.Column("air_quality_nitrogen_dioxide", sa.Float()),
        sa.Column("air_quality_sulphur_dioxide", sa.Float()),
        sa.Column("air_quality_pm25", sa.Float()),
        sa.Column("air_quality_pm10", sa.Float()),
        sa.Column("air_quality_us_epa_index", sa.Float()),
        sa.Column("air_quality_gb_defra_index", sa.Float()),
        sa.Column("go_outside", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.execute(
        """
        INSERT INTO air_quality (
            weather_id,
            air_quality_carbon_monoxide,
            air_quality_ozone,
            air_quality_nitrogen_dioxide,
            air_quality_sulphur_dioxide,
            air_quality_pm25,
            air_quality_pm10,
            air_quality_us_epa_index,
            air_quality_gb_defra_index,
            go_outside
        )
        SELECT
            id,
            air_quality_carbon_monoxide,
            air_quality_ozone,
            air_quality_nitrogen_dioxide,
            air_quality_sulphur_dioxide,
            air_quality_pm25,
            air_quality_pm10,
            air_quality_us_epa_index,
            air_quality_gb_defra_index,
            CASE
                WHEN air_quality_pm25 <= 35
                     AND air_quality_pm10 <= 50
                     AND air_quality_us_epa_index <= 2
                THEN TRUE
                ELSE FALSE
            END
        FROM weather
        """
    )

    op.drop_column("weather", "air_quality_carbon_monoxide")
    op.drop_column("weather", "air_quality_ozone")
    op.drop_column("weather", "air_quality_nitrogen_dioxide")
    op.drop_column("weather", "air_quality_sulphur_dioxide")
    op.drop_column("weather", "air_quality_pm25")
    op.drop_column("weather", "air_quality_pm10")
    op.drop_column("weather", "air_quality_us_epa_index")
    op.drop_column("weather", "air_quality_gb_defra_index")


def downgrade() -> None:
    op.add_column("weather", sa.Column("air_quality_carbon_monoxide", sa.Float()))
    op.add_column("weather", sa.Column("air_quality_ozone", sa.Float()))
    op.add_column("weather", sa.Column("air_quality_nitrogen_dioxide", sa.Float()))
    op.add_column("weather", sa.Column("air_quality_sulphur_dioxide", sa.Float()))
    op.add_column("weather", sa.Column("air_quality_pm25", sa.Float()))
    op.add_column("weather", sa.Column("air_quality_pm10", sa.Float()))
    op.add_column("weather", sa.Column("air_quality_us_epa_index", sa.Float()))
    op.add_column("weather", sa.Column("air_quality_gb_defra_index", sa.Float()))

    op.execute(
        """
        UPDATE weather
        SET
            air_quality_carbon_monoxide = (
                SELECT air_quality_carbon_monoxide
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            ),
            air_quality_ozone = (
                SELECT air_quality_ozone
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            ),
            air_quality_nitrogen_dioxide = (
                SELECT air_quality_nitrogen_dioxide
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            ),
            air_quality_sulphur_dioxide = (
                SELECT air_quality_sulphur_dioxide
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            ),
            air_quality_pm25 = (
                SELECT air_quality_pm25
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            ),
            air_quality_pm10 = (
                SELECT air_quality_pm10
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            ),
            air_quality_us_epa_index = (
                SELECT air_quality_us_epa_index
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            ),
            air_quality_gb_defra_index = (
                SELECT air_quality_gb_defra_index
                FROM air_quality
                WHERE air_quality.weather_id = weather.id
            )
        """
    )

    op.drop_table("air_quality")
