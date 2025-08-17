

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pgsodium" WITH SCHEMA "pgsodium";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA "public";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."get_connection_status"() RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN true;
END;
$$;


ALTER FUNCTION "public"."get_connection_status"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_user_id_based_on_slack_id"("input_slack_id" "text") RETURNS "uuid"
    LANGUAGE "plpgsql"
    AS $$DECLARE
    result TEXT;
BEGIN
    SELECT cp.id INTO result
    FROM creator_profiles cp
    WHERE cp.slack_id = input_slack_id
    LIMIT 1;

    RETURN result;
END;$$;


ALTER FUNCTION "public"."get_user_id_based_on_slack_id"("input_slack_id" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_users_with_conversations_today"() RETURNS TABLE("user_id" "uuid")
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT c.user_id
    FROM conversations c
    WHERE DATE(c.created_at) = CURRENT_DATE
    AND c.user_id IS NOT NULL  -- Add null check
    AND NOT EXISTS (
        SELECT 1 FROM longterm_memory l
        WHERE l.user_id = c.user_id
        AND l.summary_date = CURRENT_DATE
    );
END;
$$;


ALTER FUNCTION "public"."get_users_with_conversations_today"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."search_all_content"("p_query" "text", "p_user_id" "uuid") RETURNS TABLE("id" "uuid", "user_id" "uuid", "source_type" "text", "original_row" "jsonb", "relevance_score" real)
    LANGUAGE "plpgsql"
    AS $$BEGIN
  RETURN QUERY
  -- Memory
  SELECT 
      m.id,
      m.user_id,
      'memory'::text as source_type,
      to_jsonb(m.*) as original_row,
      1::real
  FROM memory m
  WHERE m.user_id = p_user_id 
  GROUP BY m.id

  UNION ALL
  -- Longterm Memory
  SELECT 
      l.id,
      l.user_id,
      'longterm_memory'::text as source_type,
      to_jsonb(l.*) as original_row,
      1::real
  FROM longterm_memory l
  WHERE l.user_id = p_user_id
  GROUP BY l.id

  UNION ALL
  -- Transcripts
  SELECT 
      t.id,
      p_user_id,
      'transcripts'::text as source_type,
      to_jsonb(t.*) as original_row,
      1::real
  FROM transcripts t
  WHERE t.team_id = (
            SELECT team_id FROM teams_creators tc
            WHERE tc.creator_profile_id = p_user_id
            LIMIT 1
            )
  GROUP BY t.id

  UNION ALL
  -- Project Overview
  SELECT 
      p.id,
      p.user_id,
      'project_overview'::text as source_type,
      to_jsonb(p.*) as original_row,
      1::real
  FROM project_overview p
  WHERE p.user_id = p_user_id
  GROUP BY p.id

  UNION ALL
  -- Project Updates
  SELECT 
      pu.id,
      pu.user_id,
      'project_update'::text as source_type,
      to_jsonb(pu.*) as original_row,
      1.
  FROM project_updates pu
  WHERE pu.user_id = p_user_id
  GROUP BY pu.id

  LIMIT 50;
END;$$;


ALTER FUNCTION "public"."search_all_content"("p_query" "text", "p_user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."search_transcripts"("p_query" "text", "p_user_id" "uuid") RETURNS TABLE("id" "uuid", "user_id" "uuid", "meeting_id" "text", "transcript_text" "text", "meeting_date" timestamp with time zone, "duration_minutes" integer, "participants" "jsonb", "metadata" "jsonb", "created_at" timestamp with time zone, "relevance_tags" character varying[], "speakers" "jsonb", "key_points" "text"[], "action_items" "text"[])
    LANGUAGE "plpgsql"
    AS $$BEGIN
    RETURN QUERY
    SELECT t.*
    FROM transcripts t
    WHERE t.team_id = (
            SELECT team_id FROM teams_creators tc
            WHERE tc.creator_profile_id = p_user_id
            )
    AND (
        similarity(t.summary, p_query) > 0.3
        OR t.summary ILIKE '%' || p_query || '%'
    )
    ORDER BY similarity(t.summary, p_query) DESC;
END;$$;


ALTER FUNCTION "public"."search_transcripts"("p_query" "text", "p_user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."set_current_user_id"("user_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::text, false);
END;
$$;


ALTER FUNCTION "public"."set_current_user_id"("user_id" "uuid") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."applications" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" "text" NOT NULL,
    "first_name" "text" NOT NULL,
    "last_name" "text" NOT NULL,
    "project_type" "text" NOT NULL,
    "status" "text" DEFAULT 'pending'::"text",
    "responses" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "approved_at" timestamp with time zone,
    "creator_profile_id" "uuid",
    CONSTRAINT "applications_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'approved'::"text", 'rejected'::"text"])))
);


ALTER TABLE "public"."applications" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "message_text" "text",
    "role" "text",
    "context" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    CONSTRAINT "conversations_role_check" CHECK (("role" = ANY (ARRAY['user'::"text", 'assistant'::"text"])))
);


ALTER TABLE "public"."conversations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."creator_profiles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "slack_id" "text",
    "slack_email" "text",
    "zoom_email" "text",
    "first_name" "text",
    "preferences" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "last_interaction_date" timestamp with time zone,
    "interaction_count" integer DEFAULT 0,
    "last_name" "text"
);


ALTER TABLE "public"."creator_profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."interaction_metrics" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "meeting_id" "text",
    "interaction_type" "text",
    "metrics" "jsonb" DEFAULT '{"completion_rate": 0.0, "response_time_ms": 0, "context_relevance": 0.0}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "interaction_metrics_interaction_type_check" CHECK (("interaction_type" = ANY (ARRAY['conversation'::"text", 'meeting'::"text", 'project_update'::"text"])))
);


ALTER TABLE "public"."interaction_metrics" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."longterm_memory" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "summary_date" "date",
    "content" "text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "relevance_score" double precision,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."longterm_memory" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."meeting_recordings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "meeting_id" "text",
    "user_id" "uuid",
    "team_id" bigint,
    "video_url" "text",
    "duration_seconds" integer,
    "file_size_bytes" bigint,
    "metadata" "jsonb" DEFAULT '{"format": "mp4", "status": "available", "recording_type": "full"}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."meeting_recordings" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."meetings" (
    "zoom_meeting_id" bigint NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "team_id" bigint,
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL
);


ALTER TABLE "public"."meetings" OWNER TO "postgres";


ALTER TABLE "public"."meetings" ALTER COLUMN "zoom_meeting_id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "public"."meetings_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



CREATE TABLE IF NOT EXISTS "public"."memory" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "memory_type" "text",
    "content" "text",
    "relevance_score" double precision,
    "summary_date" "date" DEFAULT CURRENT_DATE,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "memory_memory_type_check" CHECK (("memory_type" = ANY (ARRAY['buffer_summary'::"text", 'daily_summary'::"text", 'message'::"text"])))
);


ALTER TABLE "public"."memory" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."project_overview" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "project_name" "text",
    "project_type" "text",
    "description" "text",
    "current_phase" "text",
    "goals" "jsonb"[] DEFAULT '{}'::"jsonb"[],
    "challenges" "jsonb"[] DEFAULT '{}'::"jsonb"[],
    "success_metrics" "jsonb" DEFAULT '{}'::"jsonb",
    "creation_date" timestamp with time zone DEFAULT "now"(),
    "last_updated" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."project_overview" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."project_updates" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "project_id" "uuid",
    "user_id" "uuid",
    "update_date" "date" DEFAULT CURRENT_DATE,
    "progress_summary" "text",
    "milestones_hit" "text"[],
    "blockers" "text"[],
    "next_steps" "text"[],
    "mood_rating" integer,
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "project_updates_mood_rating_check" CHECK ((("mood_rating" >= 1) AND ("mood_rating" <= 5)))
);


ALTER TABLE "public"."project_updates" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."slack_installations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "slack_workspace_id" "text" NOT NULL,
    "slack_workspace_name" "text" NOT NULL,
    "bot_user_id" "text" NOT NULL,
    "bot_token" "text" NOT NULL,
    "installing_slack_user_id" "text" NOT NULL,
    "installing_user_email" "text",
    "user_id" "uuid",
    "installed_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "token_expiration" timestamp with time zone,
    "token_refreshed_at" timestamp with time zone,
    "refresh_token" "text"
);


ALTER TABLE "public"."slack_installations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."teams" (
    "id" bigint NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "team_name" "text"
);


ALTER TABLE "public"."teams" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."teams_creators" (
    "team_id" bigint NOT NULL,
    "creator_profile_id" "uuid" NOT NULL
);


ALTER TABLE "public"."teams_creators" OWNER TO "postgres";


ALTER TABLE "public"."teams_creators" ALTER COLUMN "team_id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "public"."teams_creators_team_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



ALTER TABLE "public"."teams" ALTER COLUMN "id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "public"."teams_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



CREATE TABLE IF NOT EXISTS "public"."transcript_raw" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "meeting_id" character varying NOT NULL,
    "meeting_date" timestamp with time zone,
    "content" "text" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "team_id" bigint
);


ALTER TABLE "public"."transcript_raw" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."transcripts" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "meeting_id" "text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "summary" "text",
    "team_id" bigint
);


ALTER TABLE "public"."transcripts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_feedback" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "meeting_id" "text",
    "rating" integer,
    "feedback_text" "text",
    "feedback_type" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "user_feedback_feedback_type_check" CHECK (("feedback_type" = ANY (ARRAY['general'::"text", 'meeting'::"text", 'summary'::"text", 'project'::"text"]))),
    CONSTRAINT "user_feedback_rating_check" CHECK ((("rating" >= 1) AND ("rating" <= 10)))
);


ALTER TABLE "public"."user_feedback" OWNER TO "postgres";




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "service_role";




















































































































































































GRANT ALL ON FUNCTION "public"."get_connection_status"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_connection_status"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_connection_status"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_user_id_based_on_slack_id"("input_slack_id" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_user_id_based_on_slack_id"("input_slack_id" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_user_id_based_on_slack_id"("input_slack_id" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_users_with_conversations_today"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_users_with_conversations_today"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_users_with_conversations_today"() TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."search_all_content"("p_query" "text", "p_user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."search_all_content"("p_query" "text", "p_user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."search_all_content"("p_query" "text", "p_user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."search_transcripts"("p_query" "text", "p_user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."search_transcripts"("p_query" "text", "p_user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."search_transcripts"("p_query" "text", "p_user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."set_current_user_id"("user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."set_current_user_id"("user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."set_current_user_id"("user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "postgres";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "anon";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "authenticated";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "service_role";



GRANT ALL ON FUNCTION "public"."show_limit"() TO "postgres";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "anon";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "service_role";



GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "postgres";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "anon";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "service_role";


















GRANT ALL ON TABLE "public"."applications" TO "anon";
GRANT ALL ON TABLE "public"."applications" TO "authenticated";
GRANT ALL ON TABLE "public"."applications" TO "service_role";



GRANT ALL ON TABLE "public"."conversations" TO "anon";
GRANT ALL ON TABLE "public"."conversations" TO "authenticated";
GRANT ALL ON TABLE "public"."conversations" TO "service_role";



GRANT ALL ON TABLE "public"."creator_profiles" TO "anon";
GRANT ALL ON TABLE "public"."creator_profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."creator_profiles" TO "service_role";



GRANT ALL ON TABLE "public"."interaction_metrics" TO "anon";
GRANT ALL ON TABLE "public"."interaction_metrics" TO "authenticated";
GRANT ALL ON TABLE "public"."interaction_metrics" TO "service_role";



GRANT ALL ON TABLE "public"."longterm_memory" TO "anon";
GRANT ALL ON TABLE "public"."longterm_memory" TO "authenticated";
GRANT ALL ON TABLE "public"."longterm_memory" TO "service_role";



GRANT ALL ON TABLE "public"."meeting_recordings" TO "anon";
GRANT ALL ON TABLE "public"."meeting_recordings" TO "authenticated";
GRANT ALL ON TABLE "public"."meeting_recordings" TO "service_role";



GRANT ALL ON TABLE "public"."meetings" TO "anon";
GRANT ALL ON TABLE "public"."meetings" TO "authenticated";
GRANT ALL ON TABLE "public"."meetings" TO "service_role";



GRANT ALL ON SEQUENCE "public"."meetings_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."meetings_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."meetings_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."memory" TO "anon";
GRANT ALL ON TABLE "public"."memory" TO "authenticated";
GRANT ALL ON TABLE "public"."memory" TO "service_role";



GRANT ALL ON TABLE "public"."project_overview" TO "anon";
GRANT ALL ON TABLE "public"."project_overview" TO "authenticated";
GRANT ALL ON TABLE "public"."project_overview" TO "service_role";



GRANT ALL ON TABLE "public"."project_updates" TO "anon";
GRANT ALL ON TABLE "public"."project_updates" TO "authenticated";
GRANT ALL ON TABLE "public"."project_updates" TO "service_role";



GRANT ALL ON TABLE "public"."slack_installations" TO "anon";
GRANT ALL ON TABLE "public"."slack_installations" TO "authenticated";
GRANT ALL ON TABLE "public"."slack_installations" TO "service_role";



GRANT ALL ON TABLE "public"."teams" TO "anon";
GRANT ALL ON TABLE "public"."teams" TO "authenticated";
GRANT ALL ON TABLE "public"."teams" TO "service_role";



GRANT ALL ON TABLE "public"."teams_creators" TO "anon";
GRANT ALL ON TABLE "public"."teams_creators" TO "authenticated";
GRANT ALL ON TABLE "public"."teams_creators" TO "service_role";



GRANT ALL ON SEQUENCE "public"."teams_creators_team_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."teams_creators_team_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."teams_creators_team_id_seq" TO "service_role";



GRANT ALL ON SEQUENCE "public"."teams_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."teams_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."teams_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."transcript_raw" TO "anon";
GRANT ALL ON TABLE "public"."transcript_raw" TO "authenticated";
GRANT ALL ON TABLE "public"."transcript_raw" TO "service_role";



GRANT ALL ON TABLE "public"."transcripts" TO "anon";
GRANT ALL ON TABLE "public"."transcripts" TO "authenticated";
GRANT ALL ON TABLE "public"."transcripts" TO "service_role";



GRANT ALL ON TABLE "public"."user_feedback" TO "anon";
GRANT ALL ON TABLE "public"."user_feedback" TO "authenticated";
GRANT ALL ON TABLE "public"."user_feedback" TO "service_role";



ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;
