CREATE DATABASE IF NOT EXISTS weather_dw;

USE weather_dw;

-- ============================================
-- Weather Data Warehouse Schema
-- Database: MySQL
-- Star Schema: 1 Dimension + 1 Fact Table
-- ============================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS fct_weather;
DROP TABLE IF EXISTS dim_cities;


-- ============================================
-- DIMENSION TABLE: dim_cities
-- Describes WHERE the weather was recorded
-- ============================================

CREATE TABLE dim_cities (
    city_id      INT AUTO_INCREMENT PRIMARY KEY,
    city_name    VARCHAR(100) NOT NULL,
    country      VARCHAR(10) NOT NULL,
    latitude     DOUBLE,
    longitude    DOUBLE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY unique_city_country (city_name, country)
);


-- ============================================
-- FACT TABLE: fct_weather
-- Stores weather measurements
--
-- Grain:
-- One row = one weather reading
-- for one city at one point in time
-- ============================================

CREATE TABLE fct_weather (
    observation_id   INT AUTO_INCREMENT PRIMARY KEY,
    city_id          INT NOT NULL,

    observation_time TIMESTAMP NOT NULL,

    temperature      DOUBLE,
    feels_like       DOUBLE,
    humidity         INT,
    pressure         INT,
    weather          VARCHAR(100),
    wind_speed       DOUBLE,

    inserted_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_city
        FOREIGN KEY (city_id)
        REFERENCES dim_cities(city_id)
        ON DELETE CASCADE
);