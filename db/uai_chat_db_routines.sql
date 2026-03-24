-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: uai_chat_db
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Temporary view structure for view `session_overview`
--

DROP TABLE IF EXISTS `session_overview`;
/*!50001 DROP VIEW IF EXISTS `session_overview`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `session_overview` AS SELECT 
 1 AS `session_id`,
 1 AS `user_id`,
 1 AS `username`,
 1 AS `session_name`,
 1 AS `message_count`,
 1 AS `session_start`,
 1 AS `session_end`,
 1 AS `session_duration_minutes`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `user_chat_summary`
--

DROP TABLE IF EXISTS `user_chat_summary`;
/*!50001 DROP VIEW IF EXISTS `user_chat_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `user_chat_summary` AS SELECT 
 1 AS `user_id`,
 1 AS `username`,
 1 AS `total_sessions`,
 1 AS `total_messages`,
 1 AS `total_tokens`,
 1 AS `last_chat_activity`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `session_overview`
--

/*!50001 DROP VIEW IF EXISTS `session_overview`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `session_overview` AS select `us`.`session_id` AS `session_id`,`us`.`user_id` AS `user_id`,`u`.`username` AS `username`,`us`.`session_name` AS `session_name`,count(`cm`.`id`) AS `message_count`,min(`cm`.`created_at`) AS `session_start`,max(`cm`.`created_at`) AS `session_end`,timestampdiff(MINUTE,min(`cm`.`created_at`),max(`cm`.`created_at`)) AS `session_duration_minutes` from ((`user_sessions` `us` left join `users` `u` on((`us`.`user_id` = `u`.`id`))) left join `chat_messages` `cm` on((`us`.`session_id` = `cm`.`session_id`))) group by `us`.`session_id`,`us`.`user_id`,`u`.`username`,`us`.`session_name` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `user_chat_summary`
--

/*!50001 DROP VIEW IF EXISTS `user_chat_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `user_chat_summary` AS select `u`.`id` AS `user_id`,`u`.`username` AS `username`,count(distinct `us`.`session_id`) AS `total_sessions`,count(`cm`.`id`) AS `total_messages`,sum(`cm`.`tokens`) AS `total_tokens`,max(`cm`.`created_at`) AS `last_chat_activity` from ((`users` `u` left join `user_sessions` `us` on((`u`.`id` = `us`.`user_id`))) left join `chat_messages` `cm` on(((`us`.`session_id` = `cm`.`session_id`) and (`cm`.`user_id` = `u`.`id`)))) group by `u`.`id`,`u`.`username` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-24 12:38:28
