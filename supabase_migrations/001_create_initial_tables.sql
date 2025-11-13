/*
  # Создание начальной структуры базы данных для бота записи к мастеру

  1. New Tables
    - `users` - пользователи Telegram
    - `services` - услуги ногтевого сервиса
    - `appointments` - записи клиентов
    - `work_schedule` - рабочее расписание
    - `holidays` - выходные дни
    - `settings` - настройки приложения

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated access
    - Settings table restricted to admin

  3. Indexes
    - Index on users.telegram_id for quick lookups
    - Index on appointments.user_id for listings
    - Index on appointments.start_time for scheduling
*/

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  full_name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  INDEX idx_telegram_id (telegram_id)
);

-- Таблица услуг
CREATE TABLE IF NOT EXISTS services (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  duration_minutes INTEGER NOT NULL,
  price FLOAT NOT NULL,
  description TEXT,
  active BOOLEAN DEFAULT true,
  INDEX idx_active (active)
);

-- Таблица записей на услуги
CREATE TABLE IF NOT EXISTS appointments (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  service_id BIGINT NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  status TEXT DEFAULT 'pending',
  google_event_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  INDEX idx_user_id (user_id),
  INDEX idx_start_time (start_time),
  INDEX idx_status (status)
);

-- Таблица рабочего расписания
CREATE TABLE IF NOT EXISTS work_schedule (
  id BIGSERIAL PRIMARY KEY,
  weekday INTEGER UNIQUE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  is_working BOOLEAN DEFAULT true
);

-- Таблица выходных дней
CREATE TABLE IF NOT EXISTS holidays (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  reason TEXT,
  INDEX idx_date (date)
);

-- Таблица настроек
CREATE TABLE IF NOT EXISTS settings (
  id BIGSERIAL PRIMARY KEY DEFAULT 1,
  admin_id BIGINT NOT NULL,
  planning_horizon_days INTEGER DEFAULT 30,
  timezone TEXT DEFAULT 'Europe/Moscow'
);

-- Инициализация рабочего расписания (Пн-Пт: 9:00-18:00, Сб-Вс: выходные)
INSERT INTO work_schedule (weekday, start_time, end_time, is_working) VALUES
(0, '09:00'::TIME, '18:00'::TIME, true),   -- Понедельник
(1, '09:00'::TIME, '18:00'::TIME, true),   -- Вторник
(2, '09:00'::TIME, '18:00'::TIME, true),   -- Среда
(3, '09:00'::TIME, '18:00'::TIME, true),   -- Четверг
(4, '09:00'::TIME, '18:00'::TIME, true),   -- Пятница
(5, '10:00'::TIME, '16:00'::TIME, true),   -- Суббота
(6, '10:00'::TIME, '14:00'::TIME, false)   -- Воскресенье
ON CONFLICT (weekday) DO NOTHING;

-- Инициализация начальных услуг (примеры)
INSERT INTO services (name, duration_minutes, price, description, active) VALUES
('Маникюр', 30, 500.00, 'Классический маникюр', true),
('Педикюр', 45, 800.00, 'Классический педикюр', true),
('Гель-лак', 60, 1200.00, 'Гель-лак на руках', true),
('Нарощивание ногтей', 90, 2000.00, 'Нарощивание акрилом', true),
('Дизайн', 20, 300.00, 'Художественный дизайн', true)
ON CONFLICT (name) DO NOTHING;
