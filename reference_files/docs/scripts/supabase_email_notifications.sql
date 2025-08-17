-- Supabase Email Notifications for Table Inserts
-- This script sets up email notifications for inserts on key tables.
-- It is idempotent: drops triggers if they exist before creating new ones.

-- 1. Create the notification function (shared by all triggers)
create or replace function notify_admin_on_insert()
returns trigger as $$
declare
  email_subject text;
  email_body text;
begin
  email_subject := format('New %s entry on Fridays at Four', TG_TABLE_NAME);
  email_body := format(
    'A new row was added to table "%s":%s%s',
    TG_TABLE_NAME,
    chr(10),
    row_to_json(NEW)
  );
  perform net.smtp_send(
    "from" := 'iso@fridaysatfour.co',
    "to" := 'iso@fridaysatfour.co',
    subject := email_subject,
    body := email_body
  );
  return NEW;
end;
$$ language plpgsql;

-- 2. Drop and create triggers for each table
-- Applications
DROP TRIGGER IF EXISTS notify_admin_on_applications_insert ON applications;
CREATE TRIGGER notify_admin_on_applications_insert
AFTER INSERT ON applications
FOR EACH ROW EXECUTE FUNCTION notify_admin_on_insert();

-- Beta Feedback
DROP TRIGGER IF EXISTS notify_admin_on_beta_feedback_insert ON beta_feedback;
CREATE TRIGGER notify_admin_on_beta_feedback_insert
AFTER INSERT ON beta_feedback
FOR EACH ROW EXECUTE FUNCTION notify_admin_on_insert();

-- Creativity Test Results
DROP TRIGGER IF EXISTS notify_admin_on_creativity_test_results_insert ON creativity_test_results;
CREATE TRIGGER notify_admin_on_creativity_test_results_insert
AFTER INSERT ON creativity_test_results
FOR EACH ROW EXECUTE FUNCTION notify_admin_on_insert();

-- Creator Profiles
DROP TRIGGER IF EXISTS notify_admin_on_creator_profiles_insert ON creator_profiles;
CREATE TRIGGER notify_admin_on_creator_profiles_insert
AFTER INSERT ON creator_profiles
FOR EACH ROW EXECUTE FUNCTION notify_admin_on_insert();

-- Waitlist
DROP TRIGGER IF EXISTS notify_admin_on_waitlist_insert ON waitlist;
CREATE TRIGGER notify_admin_on_waitlist_insert
AFTER INSERT ON waitlist
FOR EACH ROW EXECUTE FUNCTION notify_admin_on_insert();

-- Done. Run this file in the Supabase SQL editor. All new inserts will send an email to iso@fridaysatfour.co. 