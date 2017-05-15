					DROP SCHEMA IF EXISTS naa; 
                    CREATE SCHEMA naa; 
                    
                    DROP TABLE IF EXISTS naa.naa_2012; 
                    CREATE TABLE naa.naa_2012 (fips char(5), 
                    ozone_8hr_2008 char(50),
                    co_1971 char(50), 
                    no2_1971 char(50),
                    pm10_1987 char(50),
                    pm25_1997_2006_2012 char(50), 
                    so2_1971_2010 char(50)
                    );

                    LOAD DATA LOCAL INFILE "C:/Users/aeberle/ws/src/BiofuelAirEmissions/F-PEAM code base/development/input_data/naa_data/NAA data.csv"
                    INTO TABLE naa.naa_2012
                    COLUMNS TERMINATED BY ','
                    OPTIONALLY ENCLOSED BY '"'
                    ESCAPED BY '"'
                    LINES TERMINATED BY '\n'
                    IGNORE 1 LINES
                    (@fips, ozone_8hr_2008, co_1971, no2_1971, pm10_1987, pm25_1997_2006_2012, so2_1971_2010)
                    SET
                    fips = LPAD(@fips,5,'0');