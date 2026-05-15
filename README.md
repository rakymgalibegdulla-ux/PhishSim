# PhishSim — Анализатор поведения при фишинге

**Дипломный проект АУЭС:** "Анализ влияния фишинга на поведение сотрудников финансовой компании"

---

## 📋 Структура проекта

```
PhishSim/
├── app.py                    ← Главное Streamlit приложение
├── behavior_tracker.py       ← Трекер поведения и метрик
├── sheets_logger.py          ← Запись в Google Sheets
├── questions.json            ← 30 вопросов для теста
├── requirements.txt          ← Зависимости Python
├── .gitignore               ← Защита secrets
└── .streamlit/
    ├── config.toml          ← Конфиг Streamlit
    ├── secrets.toml         ← Google API credentials (создай сам)
    └── secrets_TEMPLATE.toml ← Шаблон для secrets.toml
```

---

## 🚀 Быстрый старт (локально)

### 1. Установить зависимости

```bash
pip install -r requirements.txt
```

### 2. Настроить Google Sheets (опционально)

Если хочешь сохранять результаты в таблицу:

1. Создай Google Table на sheets.google.com
2. Скопируй ID таблицы (из URL: `...spreadsheets/d/[ID_ЗДЕСЬ]/...`)
3. Создай Service Account в Google Cloud Console
4. Скачай JSON-ключ сервис-аккаунта
5. Переименуй `.streamlit/secrets_TEMPLATE.toml` → `.streamlit/secrets.toml`
6. Заполни данные из JSON-ключа

### 3. Запустить приложение

```bash
streamlit run app.py
```

Откроется на `http://localhost:8501`

---

## ☁️ Развертывание на Streamlit Cloud

### 1. Загрузить на GitHub

```bash
git init
git add .
git commit -m "PhishSim v1.0"
git push origin main
```

### 2. Развернуть на Streamlit Cloud

1. Зайди на https://share.streamlit.io
2. Подключи свой GitHub репозиторий
3. В Settings → Secrets вставь содержимое `secrets.toml`
4. Deploy!

---

## 📊 Что программа делает

### Страница 1: Профиль
- ФИ (опционально)
- Отдел (выбор)
- Стаж работы (выбор)
- Возрастная группа (выбор)
- Прошли ли обучение по ИБ (да/нет)

### Страница 2: Тест
- 15 случайных вопросов из 30
- Типы: письма, ссылки, SMS, сценарии, множественный выбор
- Таймер на каждый вопрос
- Прогресс-бар

### Страница 3: Результаты
- **Метрики риска:**
  - Failure Rate — % пропущенного фишинга
  - Reporting Rate — готовность сообщать об угрозах
  - Resilience Rate — устойчивость к сложным атакам
- **Профиль риска:** НИЗКИЙ / СРЕДНИЙ / ВЫСОКИЙ
- **Статистика по типам вопросов**
- **Поведенческий анализ:** скорость принятия решений
- **CSV-экспорт результатов**
- **Автосохранение в Google Sheets** (если настроено)

---

## 🔐 Безопасность

⚠️ **ВАЖНО:**
- `secrets.toml` содержит Google API ключ — НИКОГДА не загружай на GitHub!
- Используется `.gitignore` для защиты
- На Streamlit Cloud вводи secrets через UI, не в коде

---

## 📈 Интерпретация метрик

| Метрика | Формула | Низкий риск | Средний | Высокий |
|---------|---------|----------|---------|---------|
| **Failure Rate** | % пропущенного фишинга | <25% | 25-60% | >60% |
| **Reporting Rate** | 100% - FR | >75% | 50-75% | <50% |
| **Resilience Rate** | % верных сложных | >60% | 31-60% | <30% |

---

## 🛠️ Зависимости

- **streamlit** — веб-фреймворк
- **pandas** — обработка данных
- **gspread** — работа с Google Sheets
- **google-auth** — аутентификация Google

---

## 📝 Примечания

- Вопросы редактируются в `questions.json`
- Логика метрик в `behavior_tracker.py`
- Стили CSS в `app.py` (переменные в `.streamlit/config.toml`)

---

## 👤 Автор

**Aiko** — студент АУЭС, специальность Information Security Systems

**Связь:** Discord / Email
