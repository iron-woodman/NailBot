/*
  # Добавление колонок для отслеживания напоминаний о записи

  1. Changes
    - `appointments.reminder_24h_sent` - отправлено ли напоминание за 24 часа
    - `appointments.reminder_2h_sent` - отправлено ли напоминание за 2 часа
*/

ALTER TABLE appointments
  ADD COLUMN IF NOT EXISTS reminder_24h_sent BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE appointments
  ADD COLUMN IF NOT EXISTS reminder_2h_sent BOOLEAN NOT NULL DEFAULT false;
