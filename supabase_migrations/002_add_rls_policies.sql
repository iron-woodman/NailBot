/*
  # Добавление Row Level Security политик

  1. Users table
    - Пользователи могут читать свои данные
    - Пользователи могут обновлять свои данные
    - Администратор может читать все данные

  2. Services table
    - Все могут читать активные услуги
    - Только администратор может изменять

  3. Appointments table
    - Пользователи могут видеть свои записи
    - Администратор может видеть все записи
    - Пользователи могут создавать записи для себя

  4. Work Schedule & Holidays
    - Все могут читать
    - Только администратор может изменять

  5. Settings table
    - Только администратор может читать/изменять
*/

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE holidays ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  USING (auth.uid()::TEXT::BIGINT = telegram_id OR auth.jwt()->>'role' = 'admin');

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid()::TEXT::BIGINT = telegram_id)
  WITH CHECK (auth.uid()::TEXT::BIGINT = telegram_id);

CREATE POLICY "Allow inserting users"
  ON users FOR INSERT
  WITH CHECK (true);

-- Services policies
CREATE POLICY "Everyone can view active services"
  ON services FOR SELECT
  USING (active = true OR auth.jwt()->>'role' = 'admin');

CREATE POLICY "Admin can manage services"
  ON services FOR INSERT
  WITH CHECK (auth.jwt()->>'role' = 'admin');

CREATE POLICY "Admin can update services"
  ON services FOR UPDATE
  USING (auth.jwt()->>'role' = 'admin')
  WITH CHECK (auth.jwt()->>'role' = 'admin');

CREATE POLICY "Admin can delete services"
  ON services FOR DELETE
  USING (auth.jwt()->>'role' = 'admin');

-- Appointments policies
CREATE POLICY "Users can view own appointments"
  ON appointments FOR SELECT
  USING (
    user_id = (SELECT id FROM users WHERE telegram_id = auth.uid()::TEXT::BIGINT)
    OR auth.jwt()->>'role' = 'admin'
  );

CREATE POLICY "Users can create appointments"
  ON appointments FOR INSERT
  WITH CHECK (
    user_id = (SELECT id FROM users WHERE telegram_id = auth.uid()::TEXT::BIGINT)
    OR auth.jwt()->>'role' = 'admin'
  );

CREATE POLICY "Users can update own appointments"
  ON appointments FOR UPDATE
  USING (
    user_id = (SELECT id FROM users WHERE telegram_id = auth.uid()::TEXT::BIGINT)
    OR auth.jwt()->>'role' = 'admin'
  )
  WITH CHECK (
    user_id = (SELECT id FROM users WHERE telegram_id = auth.uid()::TEXT::BIGINT)
    OR auth.jwt()->>'role' = 'admin'
  );

-- Work Schedule policies
CREATE POLICY "Everyone can view work schedule"
  ON work_schedule FOR SELECT
  USING (true);

CREATE POLICY "Admin can manage work schedule"
  ON work_schedule FOR UPDATE
  USING (auth.jwt()->>'role' = 'admin')
  WITH CHECK (auth.jwt()->>'role' = 'admin');

-- Holidays policies
CREATE POLICY "Everyone can view holidays"
  ON holidays FOR SELECT
  USING (true);

CREATE POLICY "Admin can manage holidays"
  ON holidays FOR INSERT
  WITH CHECK (auth.jwt()->>'role' = 'admin');

CREATE POLICY "Admin can update holidays"
  ON holidays FOR UPDATE
  USING (auth.jwt()->>'role' = 'admin')
  WITH CHECK (auth.jwt()->>'role' = 'admin');

CREATE POLICY "Admin can delete holidays"
  ON holidays FOR DELETE
  USING (auth.jwt()->>'role' = 'admin');

-- Settings policies
CREATE POLICY "Admin can view settings"
  ON settings FOR SELECT
  USING (auth.jwt()->>'role' = 'admin');

CREATE POLICY "Admin can update settings"
  ON settings FOR UPDATE
  USING (auth.jwt()->>'role' = 'admin')
  WITH CHECK (auth.jwt()->>'role' = 'admin');
