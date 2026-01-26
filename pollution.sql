-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema pollution_db
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `pollution_db` ;

-- -----------------------------------------------------
-- Schema pollution_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `pollution_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
USE `pollution_db` ;

-- -----------------------------------------------------
-- Table `pollution_db`.`constituency`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `pollution_db`.`constituency` (
  `Constituency_ID` INT NOT NULL AUTO_INCREMENT,
  `Constituency_Name` VARCHAR(50) NOT NULL,
  `Mp_Name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`Constituency_ID`),
  UNIQUE INDEX `constituency_name_UNIQUE` (`Constituency_Name` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `pollution_db`.`station`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `pollution_db`.`station` (
  `Site_ID` INT NOT NULL,
  `Station_Name` VARCHAR(50) NOT NULL,
  `Latitude` REAL NOT NULL,
  `Longitude` REAL NOT NULL,
  `Constituency_ID` INT NOT NULL,
  PRIMARY KEY (`Site_ID`),
  INDEX `fk_station_constituency_idx` (`Constituency_ID` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `pollution_db`.`reading`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `pollution_db`.`reading` (
  `Reading_ID` INT NOT NULL,
  `Date_Time` BIGINT NOT NULL,
  `NOx` FLOAT NULL,
  `NO2` FLOAT NULL,
  `NO` FLOAT NULL,
  `PM10` FLOAT NULL,
  `PM2_5` FLOAT NULL,
  `O3` FLOAT NULL,
  `CO` FLOAT NULL,
  `SO2` FLOAT NULL,
  `VPM10` FLOAT NULL,
  `NVPM2_5` FLOAT NULL,
  `VPM2_5` FLOAT NULL,
  `NVPM10` FLOAT NULL,
  `Temperature` FLOAT NULL,
  `Pressure` FLOAT NULL,
  `RH` FLOAT NULL,
  `objectId` INT NULL,
  `Site_ID` INT NOT NULL,
  PRIMARY KEY (`Reading_ID`),
  INDEX `date_time_idx` (`Date_Time` ASC),
  INDEX `fk_reading_station_idx` (`Site_ID` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `pollution_db`.`data_schema`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `pollution_db`.`data_schema` (
  `Ident` VARCHAR(50) NOT NULL,
  `Reading` VARCHAR(50) NULL,
  `Description` VARCHAR(200) NULL,
  `Unit` VARCHAR(50) NULL,
  PRIMARY KEY (`Ident`))
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
