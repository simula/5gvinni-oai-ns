-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: 172.16.200.10:3306
-- Generation Time: Mar 22, 2021 at 10:31 AM
-- Server version: 5.7.33
-- PHP Version: 7.4.15

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `oai_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `AccessAndMobilitySubscriptionData`
--

CREATE TABLE `AccessAndMobilitySubscriptionData` (
  `ueid` varchar(15) NOT NULL,
  `servingPlmnid` varchar(15) NOT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `gpsis` json DEFAULT NULL,
  `internalGroupIds` json DEFAULT NULL,
  `sharedVnGroupDataIds` json DEFAULT NULL,
  `subscribedUeAmbr` json DEFAULT NULL,
  `nssai` json DEFAULT NULL,
  `ratRestrictions` json DEFAULT NULL,
  `forbiddenAreas` json DEFAULT NULL,
  `serviceAreaRestriction` json DEFAULT NULL,
  `coreNetworkTypeRestrictions` json DEFAULT NULL,
  `rfspIndex` int(10) DEFAULT NULL,
  `subsRegTimer` int(10) DEFAULT NULL,
  `ueUsageType` int(10) DEFAULT NULL,
  `mpsPriority` tinyint(1) DEFAULT NULL,
  `mcsPriority` tinyint(1) DEFAULT NULL,
  `activeTime` int(10) DEFAULT NULL,
  `sorInfo` json DEFAULT NULL,
  `sorInfoExpectInd` tinyint(1) DEFAULT NULL,
  `sorafRetrieval` tinyint(1) DEFAULT NULL,
  `sorUpdateIndicatorList` json DEFAULT NULL,
  `upuInfo` json DEFAULT NULL,
  `micoAllowed` tinyint(1) DEFAULT NULL,
  `sharedAmDataIds` json DEFAULT NULL,
  `odbPacketServices` json DEFAULT NULL,
  `serviceGapTime` int(10) DEFAULT NULL,
  `mdtUserConsent` json DEFAULT NULL,
  `mdtConfiguration` json DEFAULT NULL,
  `traceData` json DEFAULT NULL,
  `cagData` json DEFAULT NULL,
  `stnSr` varchar(50) DEFAULT NULL,
  `cMsisdn` varchar(50) DEFAULT NULL,
  `nbIoTUePriority` int(10) DEFAULT NULL,
  `nssaiInclusionAllowed` tinyint(1) DEFAULT NULL,
  `rgWirelineCharacteristics` varchar(50) DEFAULT NULL,
  `ecRestrictionDataWb` json DEFAULT NULL,
  `ecRestrictionDataNb` tinyint(1) DEFAULT NULL,
  `expectedUeBehaviourList` json DEFAULT NULL,
  `primaryRatRestrictions` json DEFAULT NULL,
  `secondaryRatRestrictions` json DEFAULT NULL,
  `edrxParametersList` json DEFAULT NULL,
  `ptwParametersList` json DEFAULT NULL,
  `iabOperationAllowed` tinyint(1) DEFAULT NULL,
  `wirelineForbiddenAreas` json DEFAULT NULL,
  `wirelineServiceAreaRestriction` json DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `AccessAndMobilitySubscriptionData` (`ueid`, `servingPlmnid`, `nssai`) VALUES
('242881234500125', '24288','{\"defaultSingleNssais\": [{\"sst\": 1, \"sd\": \"1\"}]}'),
('242881234500126', '24288','{\"defaultSingleNssais\": [{\"sst\": 1, \"sd\": \"1\"}]}'),
('242881234500127', '24288','{\"defaultSingleNssais\": [{\"sst\": 1, \"sd\": \"1\"}]}'),
('242881234500128', '24288','{\"defaultSingleNssais\": [{\"sst\": 1, \"sd\": \"1\"}]}'),
('242881234500129', '24288','{\"defaultSingleNssais\": [{\"sst\": 1, \"sd\": \"1\"}]}');
-- --------------------------------------------------------

--
-- Table structure for table `Amf3GppAccessRegistration`
--

CREATE TABLE `Amf3GppAccessRegistration` (
  `ueid` varchar(15) NOT NULL,
  `amfInstanceId` varchar(50) NOT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `purgeFlag` tinyint(1) DEFAULT NULL,
  `pei` varchar(50) DEFAULT NULL,
  `imsVoPs` json DEFAULT NULL,
  `deregCallbackUri` varchar(50) NOT NULL,
  `amfServiceNameDereg` json DEFAULT NULL,
  `pcscfRestorationCallbackUri` varchar(50) DEFAULT NULL,
  `amfServiceNamePcscfRest` json DEFAULT NULL,
  `initialRegistrationInd` tinyint(1) DEFAULT NULL,
  `guami` json NOT NULL,
  `backupAmfInfo` json DEFAULT NULL,
  `drFlag` tinyint(1) DEFAULT NULL,
  `ratType` json NOT NULL,
  `urrpIndicator` tinyint(1) DEFAULT NULL,
  `amfEeSubscriptionId` varchar(50) DEFAULT NULL,
  `epsInterworkingInfo` json DEFAULT NULL,
  `ueSrvccCapability` tinyint(1) DEFAULT NULL,
  `registrationTime` varchar(50) DEFAULT NULL,
  `vgmlcAddress` json DEFAULT NULL,
  `contextInfo` json DEFAULT NULL,
  `noEeSubscriptionInd` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `AuthenticationStatus`
--

CREATE TABLE `AuthenticationStatus` (
  `ueid` varchar(20) NOT NULL,
  `nfInstanceId` varchar(50) NOT NULL,
  `success` tinyint(1) NOT NULL,
  `timeStamp` varchar(50) NOT NULL,
  `authType` varchar(25) NOT NULL,
  `servingNetworkName` varchar(50) NOT NULL,
  `authRemovalInd` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `AuthenticationSubscription`
--

CREATE TABLE `AuthenticationSubscription` (
  `ueid` varchar(20) NOT NULL,
  `authenticationMethod` varchar(25) NOT NULL,
  `encPermanentKey` varchar(50) DEFAULT NULL,
  `protectionParameterId` varchar(50) DEFAULT NULL,
  `sequenceNumber` json DEFAULT NULL,
  `authenticationManagementField` varchar(50) DEFAULT NULL,
  `algorithmId` varchar(50) DEFAULT NULL,
  `encOpcKey` varchar(50) DEFAULT NULL,
  `encTopcKey` varchar(50) DEFAULT NULL,
  `vectorGenerationInHss` tinyint(1) DEFAULT NULL,
  `n5gcAuthMethod` varchar(15) DEFAULT NULL,
  `rgAuthenticationInd` tinyint(1) DEFAULT NULL,
  `supi` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `AuthenticationSubscription`
--

INSERT INTO `AuthenticationSubscription` (`ueid`, `authenticationMethod`, `encPermanentKey`, `protectionParameterId`, `sequenceNumber`, `authenticationManagementField`, `algorithmId`, `encOpcKey`, `encTopcKey`, `vectorGenerationInHss`, `n5gcAuthMethod`, `rgAuthenticationInd`, `supi`) VALUES
('242881234500031', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500031'),
('242881234500032', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500032'),
('242881234500033', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500033'),
('242881234500034', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500034'),
('242881234500035', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500035'),
('242881234500036', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500036'),
('242881234500037', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500037'),
('242881234500038', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500038'),
('242881234500039', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500039'),
('242881234500040', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500040'),
('242881234500041', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500041'),
('242881234500042', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500042'),
('242881234500043', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500043'),
('242881234500044', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500044'),
('242881234500045', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500045'),
('242881234500046', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500046'),
('242881234500047', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500047'),
('242881234500048', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500048'),
('242881234500049', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500049'),
('242881234500050', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500050'),
('242881234500051', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500051'),
('242881234500052', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500052'),
('242881234500053', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500053'),
('242881234500054', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500054'),
('242881234500055', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500055'),
('242881234500056', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500056'),
('242881234500057', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500057'),
('242881234500058', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500058'),
('242881234500059', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500059'),
('242881234500060', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500060'),
('242881234500061', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500061'),
('242881234500062', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500062'),
('242881234500063', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500063'),
('242881234500064', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500064'),
('242881234500065', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500065'),
('242881234500066', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500066'),
('242881234500067', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500067'),
('242881234500068', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500068'),
('242881234500069', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500069'),
('242881234500070', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500070'),
('242881234500071', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500071'),
('242881234500072', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500072'),
('242881234500073', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500073'),
('242881234500074', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500074'),
('242881234500075', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500075'),
('242881234500076', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500076'),
('242881234500077', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500077'),
('242881234500078', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500078'),
('242881234500079', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500079'),
('242881234500080', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500080'),
('242881234500081', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500081'),
('242881234500082', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500082'),
('242881234500083', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500083'),
('242881234500084', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500084'),
('242881234500085', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500085'),
('242881234500086', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500086'),
('242881234500087', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500087'),
('242881234500088', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500088'),
('242881234500089', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500089'),
('242881234500090', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500090'),
('242881234500091', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500091'),
('242881234500092', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500092'),
('242881234500093', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500093'),
('242881234500094', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500094'),
('242881234500095', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500095'),
('242881234500096', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500096'),
('242881234500097', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500097'),
('242881234500098', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500098'),
('242881234500099', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500099'),
('242881234500100', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500100'),
('242881234500101', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500101'),
('242881234500102', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500102'),
('242881234500103', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500103'),
('242881234500104', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500104'),
('242881234500105', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500105'),
('242881234500106', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500106'),
('242881234500107', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500107'),
('242881234500108', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500108'),
('242881234500109', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500109'),
('242881234500110', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500110'),
('242881234500111', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500111'),
('242881234500112', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500112'),
('242881234500113', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500113'),
('242881234500114', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500114'),
('242881234500115', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500115'),
('242881234500116', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500116'),
('242881234500117', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500117'),
('242881234500118', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500118'),
('242881234500119', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500119'),
('242881234500120', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500120'),
('242881234500121', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500121'),
('242881234500122', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500122'),
('242881234500123', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500123'),
('242881234500124', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500124'),
('242881234500125', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500125'),
('242881234500126', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500126'),
('242881234500127', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500127'),
('242881234500128', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500128'),
('242881234500129', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500129'),
('242881234500130', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500130'),
('242881234500131', '5G_AKA', '1006020F0A478BF6B699F15C062E42B3', '1006020F0A478BF6B699F15C062E42B3', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '242881234500131');

-- --------------------------------------------------------

--
-- Table structure for table `SdmSubscriptions`
--

CREATE TABLE `SdmSubscriptions` (
  `ueid` varchar(15) NOT NULL,
  `subsId` int(10) UNSIGNED NOT NULL,
  `nfInstanceId` varchar(50) NOT NULL,
  `implicitUnsubscribe` tinyint(1) DEFAULT NULL,
  `expires` varchar(50) DEFAULT NULL,
  `callbackReference` varchar(50) NOT NULL,
  `amfServiceName` json DEFAULT NULL,
  `monitoredResourceUris` json NOT NULL,
  `singleNssai` json DEFAULT NULL,
  `dnn` varchar(50) DEFAULT NULL,
  `subscriptionId` varchar(50) DEFAULT NULL,
  `plmnId` json DEFAULT NULL,
  `immediateReport` tinyint(1) DEFAULT NULL,
  `report` json DEFAULT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `contextInfo` json DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `SessionManagementSubscriptionData`
--

CREATE TABLE `SessionManagementSubscriptionData` (
  `ueid` varchar(15) NOT NULL,
  `servingPlmnid` varchar(15) NOT NULL,
  `singleNssai` json NOT NULL,
  `dnnConfigurations` json DEFAULT NULL,
  `internalGroupIds` json DEFAULT NULL,
  `sharedVnGroupDataIds` json DEFAULT NULL,
  `sharedDnnConfigurationsId` varchar(50) DEFAULT NULL,
  `odbPacketServices` json DEFAULT NULL,
  `traceData` json DEFAULT NULL,
  `sharedTraceDataId` varchar(50) DEFAULT NULL,
  `expectedUeBehavioursList` json DEFAULT NULL,
  `suggestedPacketNumDlList` json DEFAULT NULL,
  `3gppChargingCharacteristics` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `SessionManagementSubscriptionData`
--

INSERT INTO `SessionManagementSubscriptionData` (`ueid`, `servingPlmnid`, `singleNssai`, `dnnConfigurations`) VALUES 
('242881234500031', '24288', '{\"sst\": 222, \"sd\": \"123\"}','{\"default\":{\"pduSessionTypes\":{ \"defaultSessionType\": \"IPV4\"},\"sscModes\": {\"defaultSscMode\": \"SSC_MODE_1\"},\"5gQosProfile\": {\"5qi\": 6,\"arp\":{\"priorityLevel\": 1,\"preemptCap\": \"NOT_PREEMPT\",\"preemptVuln\":\"NOT_PREEMPTABLE\"},\"priorityLevel\":1},\"sessionAmbr\":{\"uplink\":\"100Mbps\", \"downlink\":\"100Mbps\"},\"staticIpAddress\":[{\"ipv4Addr\": \"12.1.1.4\"}]}}');
INSERT INTO `SessionManagementSubscriptionData` (`ueid`, `servingPlmnid`, `singleNssai`, `dnnConfigurations`) VALUES 
('242881234500032', '24288', '{\"sst\": 222, \"sd\": \"123\"}','{\"default\":{\"pduSessionTypes\":{ \"defaultSessionType\": \"IPV4\"},\"sscModes\": {\"defaultSscMode\": \"SSC_MODE_1\"},\"5gQosProfile\": {\"5qi\": 6,\"arp\":{\"priorityLevel\": 1,\"preemptCap\": \"NOT_PREEMPT\",\"preemptVuln\":\"NOT_PREEMPTABLE\"},\"priorityLevel\":1},\"sessionAmbr\":{\"uplink\":\"100Mbps\", \"downlink\":\"100Mbps\"}}}');
-- --------------------------------------------------------

--
-- Table structure for table `SmfRegistrations`
--

CREATE TABLE `SmfRegistrations` (
  `ueid` varchar(15) NOT NULL,
  `subpduSessionId` int(10) NOT NULL,
  `smfInstanceId` varchar(50) NOT NULL,
  `smfSetId` varchar(50) DEFAULT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `pduSessionId` int(10) NOT NULL,
  `singleNssai` json NOT NULL,
  `dnn` varchar(50) DEFAULT NULL,
  `emergencyServices` tinyint(1) DEFAULT NULL,
  `pcscfRestorationCallbackUri` varchar(50) DEFAULT NULL,
  `plmnId` json NOT NULL,
  `pgwFqdn` varchar(50) DEFAULT NULL,
  `epdgInd` tinyint(1) DEFAULT NULL,
  `deregCallbackUri` varchar(50) DEFAULT NULL,
  `registrationReason` json DEFAULT NULL,
  `registrationTime` varchar(50) DEFAULT NULL,
  `contextInfo` json DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `SmfSelectionSubscriptionData`
--

CREATE TABLE `SmfSelectionSubscriptionData` (
  `ueid` varchar(15) NOT NULL,
  `servingPlmnid` varchar(15) NOT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `subscribedSnssaiInfos` json DEFAULT NULL,
  `sharedSnssaiInfosId` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `AccessAndMobilitySubscriptionData`
--
ALTER TABLE `AccessAndMobilitySubscriptionData`
  ADD PRIMARY KEY (`ueid`,`servingPlmnid`) USING BTREE;

--
-- Indexes for table `Amf3GppAccessRegistration`
--
ALTER TABLE `Amf3GppAccessRegistration`
  ADD PRIMARY KEY (`ueid`);

--
-- Indexes for table `AuthenticationStatus`
--
ALTER TABLE `AuthenticationStatus`
  ADD PRIMARY KEY (`ueid`);

--
-- Indexes for table `AuthenticationSubscription`
--
ALTER TABLE `AuthenticationSubscription`
  ADD PRIMARY KEY (`ueid`);

--
-- Indexes for table `SdmSubscriptions`
--
ALTER TABLE `SdmSubscriptions`
  ADD PRIMARY KEY (`subsId`,`ueid`) USING BTREE;

--
-- Indexes for table `SessionManagementSubscriptionData`
--
ALTER TABLE `SessionManagementSubscriptionData`
  ADD PRIMARY KEY (`ueid`,`servingPlmnid`) USING BTREE;

--
-- Indexes for table `SmfRegistrations`
--
ALTER TABLE `SmfRegistrations`
  ADD PRIMARY KEY (`ueid`,`subpduSessionId`) USING BTREE;

--
-- Indexes for table `SmfSelectionSubscriptionData`
--
ALTER TABLE `SmfSelectionSubscriptionData`
  ADD PRIMARY KEY (`ueid`,`servingPlmnid`) USING BTREE;

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `SdmSubscriptions`
--
ALTER TABLE `SdmSubscriptions`
  MODIFY `subsId` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

