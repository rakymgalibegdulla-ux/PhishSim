"""
sheets_logger.py — Запись результатов теста в Google Sheets
Используется gspread + google-auth (сервисный аккаунт)
"""

import streamlit as st
from datetime import datetime


def _get_client():
    """
    Подключение к Google Sheets через сервисный аккаунт.
    Credentials читаются из st.secrets (secrets.toml или Streamlit Cloud).
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )
        return gspread.authorize(creds)
    except Exception as e:
        return None


def _get_or_create_sheet(client, spreadsheet_id: str, sheet_name: str):
    """Открывает таблицу и лист, создаёт заголовки если лист пустой."""
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
    except Exception:
        return None

    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except Exception:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

    # Если лист пустой — добавляем заголовки
    if sheet.row_count == 0 or not sheet.get_all_values():
        headers = [
            "Дата и время",
            "Имя",
            "Отдел",
            "Стаж",
            "Возраст",
            "Обучение по ИБ",
            "Всего вопросов",
            "Верных ответов",
            "Результат %",
            "Failure Rate %",
            "Reporting Rate %",
            "Resilience Rate %",
            "False Positive Rate %",
            "Уровень риска",
            "Лучший тип вопросов",
            "Худший тип вопросов",
            "Среднее время верного (сек)",
            "Среднее время ошибки (сек)",
        ]
        sheet.append_row(headers)

    return sheet


def log_result(profile: dict, stats: dict, risk: dict) -> bool:
    """
    Записывает итоги теста одного пользователя в Google Sheets.

    Parameters
    ----------
    profile : dict  — данные профиля (department, experience, age_group, had_training)
    stats   : dict  — результат compute_stats() из app.py
    risk    : dict  — результат get_risk_profile() из app.py

    Returns True если запись успешна, False если ошибка.
    """
    try:
        spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
        sheet_name     = st.secrets["sheets"].get("sheet_name", "Результаты")
    except Exception:
        return False  # secrets не настроены — тихо пропускаем

    client = _get_client()
    if client is None:
        return False

    sheet = _get_or_create_sheet(client, spreadsheet_id, sheet_name)
    if sheet is None:
        return False

    # Определяем лучший и худший тип вопросов
    by_type = stats.get("by_type", {})
    best_type  = max(by_type.values(), key=lambda d: d["rate"])["label"] if by_type else "—"
    worst_type = min(by_type.values(), key=lambda d: d["rate"])["label"] if by_type else "—"

    row = [
        datetime.now().strftime("%d.%m.%Y %H:%M"),
        profile.get("name", "Аноним"),
        profile.get("department", "—"),
        profile.get("experience", "—"),
        profile.get("age_group", "—"),
        "Да" if profile.get("had_training") else "Нет",
        stats.get("total", 0),
        stats.get("correct", 0),
        stats.get("score_pct", 0),
        stats.get("failure_rate", 0),
        stats.get("reporting_rate", 0),
        stats.get("resilience", 0),
        stats.get("fp_rate", 0),
        risk.get("level_ru", "—"),
        best_type,
        worst_type,
        stats.get("avg_ok", 0),
        stats.get("avg_fail", 0),
    ]

    try:
        sheet.append_row(row)
        return True
    except Exception:
        return False


def get_all_results() -> list[dict]:
    """
    Загружает все результаты из Google Sheets для аналитики.
    Возвращает список словарей (заголовок → значение).
    """
    try:
        spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
        sheet_name     = st.secrets["sheets"].get("sheet_name", "Результаты")
    except Exception:
        return []

    client = _get_client()
    if client is None:
        return []

    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet       = spreadsheet.worksheet(sheet_name)
        records     = sheet.get_all_records()
        return records
    except Exception:
        return []
