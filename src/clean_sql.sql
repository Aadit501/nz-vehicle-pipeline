-- Data Cleaning SQL
-- Creates cleaned_vehicles from raw_vehicles

DROP TABLE IF EXISTS cleaned_vehicles;

CREATE TABLE cleaned_vehicles AS
SELECT
    objectid,
    TRIM(UPPER(basic_colour))                                  AS basic_colour,
    TRIM(UPPER(body_type))                                     AS body_type,
    COALESCE(cc_rating, 0)                                     AS cc_rating,
    TRIM(UPPER(import_status))                                 AS import_status,
    TRIM(UPPER(make))                                          AS make,
    TRIM(UPPER(model))                                         AS model,

    -- Standardise fuel/motive power
    CASE
        WHEN UPPER(motive_power) LIKE '%ELECTRIC%' AND UPPER(motive_power) NOT LIKE '%HYBRID%'
             THEN 'ELECTRIC'
        WHEN UPPER(motive_power) LIKE '%HYBRID%'   THEN 'HYBRID'
        WHEN UPPER(motive_power) = 'DIESEL'        THEN 'DIESEL'
        WHEN UPPER(motive_power) = 'PETROL'        THEN 'PETROL'
        WHEN UPPER(motive_power) = 'LPG'           THEN 'LPG'
        ELSE COALESCE(UPPER(TRIM(motive_power)), 'UNKNOWN')
    END AS fuel_type,

    first_nz_registration_year                                 AS reg_year,
    first_nz_registration_month                                AS reg_month,
    vehicle_year,
    COALESCE(gross_vehicle_mass, 0)                            AS gross_vehicle_mass,
    COALESCE(number_of_seats, 0)                               AS number_of_seats,
    COALESCE(number_of_axles, 0)                               AS number_of_axles,
    TRIM(UPPER(vehicle_type))                                  AS vehicle_type,
    TRIM(UPPER(vehicle_usage))                                 AS vehicle_usage,
    TRIM(UPPER(nz_assembled))                                  AS nz_assembled,
    TRIM(UPPER(original_country))                              AS original_country,
    TRIM(UPPER(tla))                                           AS tla,
    postcode,
    TRIM(UPPER(transmission_type))                             AS transmission_type,
    COALESCE(power_rating, 0)                                  AS power_rating,
    COALESCE(vdam_weight, 0)                                   AS vdam_weight,
    COALESCE(fc_combined, 0)                                   AS fc_combined,
    COALESCE(fc_urban, 0)                                      AS fc_urban,
    COALESCE(fc_extra_urban, 0)                                AS fc_extra_urban,
    TRIM(UPPER(synthetic_greenhouse_gas))                      AS synthetic_greenhouse_gas,
    vin11,

    -- Quality flags
    CASE WHEN first_nz_registration_year < 1950 OR first_nz_registration_year > 2026 THEN 1 ELSE 0 END AS flag_invalid_reg_year,
    CASE WHEN vehicle_year < 1885 OR vehicle_year > 2026 THEN 1 ELSE 0 END AS flag_invalid_vehicle_year,
    CASE WHEN cc_rating > 20000 THEN 1 ELSE 0 END                   AS flag_suspect_cc,
    CASE WHEN gross_vehicle_mass > 100000 THEN 1 ELSE 0 END         AS flag_suspect_gvm,
    CASE WHEN fc_combined > 30 AND fc_combined != 0 THEN 1 ELSE 0 END AS flag_high_fuel_consumption

FROM raw_vehicles
WHERE
    first_nz_registration_year BETWEEN 1950 AND 2026
    AND body_type IS NOT NULL
    AND body_type != '';
