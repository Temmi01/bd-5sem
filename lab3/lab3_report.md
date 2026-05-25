# Лабораторна 3: Міграція даних (погодна БД)

## Що реалізовано

1. ORM-модель і шарова архітектура у `lab3_app.py`:
   - ORM-сутності `Weather` та `AirQuality`
   - шар репозиторію: `WeatherRepository`
   - шар сервісу: `WeatherService`
   - консольні точки входу для запитів

2. Завантаження CSV `GlobalWeatherRepository.csv` з нормалізацією даних:
   - `country` (текст)
   - `wind_degree` (ціле число)
   - `wind_kph` (дробове число)
   - `wind_direction` (enum-подібний домен)
   - `last_updated_date` (дата)
   - `sunrise` (час)

3. Рефакторинг міграцією (винесення категорії якості повітря):
   - базові погодні поля збережено в `weather`
   - категорію якості повітря винесено в `air_quality`
   - дані перенесено через SQL `INSERT ... SELECT`
   - при переході між етапами дані не втрачаються

4. Булеве поле рішення:
   - `air_quality.go_outside` (boolean, `NOT NULL`, `default false`)
   - формула заповнення:
     - `pm25 <= 35`
     - `pm10 <= 50`
     - `us_epa_index <= 2`

5. Скрипти міграції між БД:
   - PostgreSQL-конфіг: `alembic_postgres.ini`
   - MySQL-конфіг: `alembic_mysql.ini`
   - спільні міграції в `alembic/versions`

## Етапи міграцій

1. `0001_create_weather.py` - створює початкову таблицю `weather` одразу з обов'язковими типами:
   - `wind_degree` (Integer)
   - `wind_kph` (Float)
   - `wind_direction` (Enum domain)
   - `sunrise` (Time)
2. `0002_split_air_quality.py` - створює `air_quality`, переносить дані, видаляє винесені колонки з `weather`.

## Як запускати

Із директорії `лаб3`:

```bash
python lab3.py migrate --target both
python lab3.py setup --target both
python lab3.py query-date --target postgres --country Afghanistan --date 2024-05-16
python lab3.py console --target postgres
```
