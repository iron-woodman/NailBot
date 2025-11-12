const API_BASE_URL = window.location.origin;
let tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const authHeader = `tma ${tg.initData}`;

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification show ${type}`;
    setTimeout(() => {
        notification.className = 'notification';
    }, 3000);
}

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');

    switch(tabName) {
        case 'services':
            loadServices();
            break;
        case 'schedule':
            loadSchedule();
            break;
        case 'appointments':
            loadAppointments();
            break;
        case 'holidays':
            loadHolidays();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': authHeader,
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка запроса');
        }

        return await response.json();
    } catch (error) {
        showNotification(error.message, 'error');
        throw error;
    }
}

async function loadServices() {
    const services = await apiRequest('/api/services');
    const container = document.getElementById('services-list');
    container.innerHTML = services.map(service => `
        <div class="list-item">
            <div class="list-item-header">
                <div class="list-item-title">${service.name}</div>
                <div class="list-item-actions">
                    <button class="btn btn-secondary" onclick="editService(${service.id})">Изменить</button>
                    <button class="btn btn-danger" onclick="deleteService(${service.id})">Удалить</button>
                </div>
            </div>
            <div class="list-item-body">
                <div>Длительность: ${service.duration_minutes} мин</div>
                <div>Цена: ${service.price} руб.</div>
                <div>Описание: ${service.description || 'Нет'}</div>
                <div>Статус: ${service.active ? 'Активна' : 'Неактивна'}</div>
            </div>
        </div>
    `).join('');
}

function showAddServiceModal() {
    document.getElementById('modal-body').innerHTML = `
        <h3>Добавить услугу</h3>
        <form id="service-form">
            <div class="form-group">
                <label>Название</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Длительность (минуты)</label>
                <input type="number" name="duration_minutes" required>
            </div>
            <div class="form-group">
                <label>Цена (руб.)</label>
                <input type="number" name="price" step="0.01" required>
            </div>
            <div class="form-group">
                <label>Описание</label>
                <textarea name="description"></textarea>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Сохранить</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;

    document.getElementById('service-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            name: formData.get('name'),
            duration_minutes: parseInt(formData.get('duration_minutes')),
            price: parseFloat(formData.get('price')),
            description: formData.get('description'),
            active: true
        };

        await apiRequest('/api/services', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        closeModal();
        loadServices();
        showNotification('Услуга добавлена');
    };

    document.getElementById('modal').classList.add('show');
}

async function deleteService(id) {
    if (confirm('Вы уверены, что хотите деактивировать эту услугу?')) {
        await apiRequest(`/api/services/${id}`, { method: 'DELETE' });
        loadServices();
        showNotification('Услуга деактивирована');
    }
}

async function loadSchedule() {
    const schedule = await apiRequest('/api/work-schedule');
    const days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];
    const container = document.getElementById('schedule-list');

    container.innerHTML = schedule.map(day => `
        <div class="schedule-day">
            <div class="schedule-day-name">${days[day.weekday]}</div>
            <div class="schedule-day-time">
                <input type="time" value="${day.start_time}" id="start-${day.weekday}">
                <span>-</span>
                <input type="time" value="${day.end_time}" id="end-${day.weekday}">
            </div>
            <label class="toggle">
                <input type="checkbox" ${day.is_working ? 'checked' : ''} id="working-${day.weekday}">
                <span class="slider"></span>
            </label>
            <button class="btn btn-primary" onclick="updateSchedule(${day.weekday})">Сохранить</button>
        </div>
    `).join('');
}

async function updateSchedule(weekday) {
    const data = {
        start_time: document.getElementById(`start-${weekday}`).value,
        end_time: document.getElementById(`end-${weekday}`).value,
        is_working: document.getElementById(`working-${weekday}`).checked
    };

    await apiRequest(`/api/work-schedule/${weekday}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });

    showNotification('Расписание обновлено');
}

async function loadAppointments() {
    const status = document.getElementById('status-filter').value;
    const params = status ? `?status=${status}` : '';
    const appointments = await apiRequest(`/api/appointments${params}`);
    const container = document.getElementById('appointments-list');

    container.innerHTML = appointments.map(app => `
        <div class="list-item">
            <div class="list-item-header">
                <div class="list-item-title">${app.user_name} (@${app.user_username || 'N/A'})</div>
                <span class="status-badge status-${app.status}">${app.status}</span>
            </div>
            <div class="list-item-body">
                <div>Услуга: ${app.service_name}</div>
                <div>Дата: ${new Date(app.start_time).toLocaleDateString('ru-RU')}</div>
                <div>Время: ${new Date(app.start_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'})}</div>
            </div>
            <div class="list-item-actions" style="margin-top: 12px;">
                ${app.status !== 'cancelled' ? `
                    <button class="btn btn-danger" onclick="cancelAppointment(${app.id})">Отменить</button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function cancelAppointment(id) {
    if (confirm('Отменить эту запись?')) {
        await apiRequest(`/api/appointments/${id}`, { method: 'DELETE' });
        loadAppointments();
        showNotification('Запись отменена');
    }
}

async function loadHolidays() {
    const holidays = await apiRequest('/api/holidays');
    const container = document.getElementById('holidays-list');

    container.innerHTML = holidays.map(holiday => `
        <div class="list-item">
            <div class="list-item-header">
                <div class="list-item-title">${new Date(holiday.date).toLocaleDateString('ru-RU')}</div>
                <button class="btn btn-danger" onclick="deleteHoliday(${holiday.id})">Удалить</button>
            </div>
            <div class="list-item-body">${holiday.reason || 'Без причины'}</div>
        </div>
    `).join('');
}

function showAddHolidayModal() {
    document.getElementById('modal-body').innerHTML = `
        <h3>Добавить выходной день</h3>
        <form id="holiday-form">
            <div class="form-group">
                <label>Дата</label>
                <input type="date" name="date" required>
            </div>
            <div class="form-group">
                <label>Причина</label>
                <input type="text" name="reason">
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Сохранить</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;

    document.getElementById('holiday-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            date: formData.get('date'),
            reason: formData.get('reason')
        };

        await apiRequest('/api/holidays', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        closeModal();
        loadHolidays();
        showNotification('Выходной день добавлен');
    };

    document.getElementById('modal').classList.add('show');
}

async function deleteHoliday(id) {
    if (confirm('Удалить этот выходной день?')) {
        await apiRequest(`/api/holidays/${id}`, { method: 'DELETE' });
        loadHolidays();
        showNotification('Выходной день удален');
    }
}

async function loadSettings() {
    const settings = await apiRequest('/api/settings');
    const container = document.getElementById('settings-form');

    container.innerHTML = `
        <form id="settings-update-form">
            <div class="form-group">
                <label>Горизонт планирования (дней)</label>
                <input type="number" name="planning_horizon_days" value="${settings.planning_horizon_days}" required>
            </div>
            <div class="form-group">
                <label>Часовой пояс</label>
                <input type="text" name="timezone" value="${settings.timezone}" required>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Сохранить</button>
            </div>
        </form>
    `;

    document.getElementById('settings-update-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            planning_horizon_days: parseInt(formData.get('planning_horizon_days')),
            timezone: formData.get('timezone')
        };

        await apiRequest('/api/settings', {
            method: 'PUT',
            body: JSON.stringify(data)
        });

        showNotification('Настройки обновлены');
    };
}

function closeModal() {
    document.getElementById('modal').classList.remove('show');
}

document.getElementById('user-info').textContent = tg.initDataUnsafe?.user?.first_name || 'Администратор';

loadServices();
