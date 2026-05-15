"""
app.py — PhishSim: Анализ поведения сотрудников
Дипломный проект АУЭС · «Анализ влияния фишинга на поведение сотрудников»
Загружает questions.json, проводит тест из 15 случайных вопросов, анализирует поведение.
"""

import streamlit as st
import json
import random
import time
import csv
import io
from pathlib import Path
from collections import Counter
from behavior_tracker import BehaviorTracker
from sheets_logger import log_result, get_all_results

# ══════════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="PhishSim — Анализ поведения",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DEPARTMENTS = [
    "Финансовый отдел", "IT-отдел", "HR-отдел", "Бухгалтерия",
    "Юридический отдел", "Руководство", "Продажи", "Другое",
]
EXPERIENCE  = ["Менее 1 года", "1–3 года", "3–5 лет", "Более 5 лет"]
AGE_GROUPS  = ["20–30 лет", "31–40 лет", "41–50 лет", "Старше 50 лет"]

TYPE_LABELS = {
    "email_analysis": "Анализ письма",
    "url_analysis":   "Анализ ссылки",
    "sms_analysis":   "Анализ SMS",
    "situational":    "Ситуационная задача",
    "multi_choice":   "Множественный выбор",
    "action_after":   "Действия после инцидента",
}

QUESTIONS_FILE = Path(__file__).parent / "questions.json"

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

*, html, body { box-sizing:border-box; font-family:'Inter',sans-serif !important; }
html, body    { background:#0b0f1a !important; }

[class*="css"], .main, section.main, .block-container,
[data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"],
[data-testid="column"], .element-container, .stMarkdown {
    background:#0b0f1a !important;
    background-color:#0b0f1a !important;
    background-image:none !important;
    color:#b8c4d4 !important;
}
.block-container { padding:2.5rem 3.5rem !important; max-width:1060px !important; }

/* ── Шапка ── */
.ps-header { display:flex; align-items:center; gap:13px;
    padding-bottom:1.6rem; border-bottom:1px solid #0f1e35; margin-bottom:1.8rem; }
.ps-logo { width:38px; height:38px; border-radius:8px;
    background:linear-gradient(135deg,#1e3a5f,#2563eb);
    display:flex; align-items:center; justify-content:center; font-size:1.1rem; }
.ps-title { font-size:1.2rem; font-weight:700; color:#e2e8f0; letter-spacing:-0.01em; line-height:1; }
.ps-sub   { font-size:0.6rem; color:#2d4a6e; letter-spacing:0.14em;
    text-transform:uppercase; margin-top:4px; }

/* ── Секции ── */
.sec-label { font-size:0.58rem; font-weight:600; letter-spacing:0.22em;
    text-transform:uppercase; color:#3b6fd4;
    padding-bottom:6px; margin:22px 0 12px; border-bottom:1px solid #0f1e35; }

/* ── Карточки ── */
.ps-card { background:#0d1625; border:1px solid #152035;
    border-radius:10px; padding:18px 22px; margin-bottom:12px; }

/* ── Email/SMS поля ── */
.field-label { font-size:0.58rem; font-weight:600; letter-spacing:0.18em;
    text-transform:uppercase; color:#2d4a6e; margin-bottom:3px; }
.field-value { font-size:0.82rem; color:#c9d9ec; margin-bottom:12px; }
.field-divider { height:1px; background:#0f1e35; margin:12px 0; }
.field-body   { font-size:0.8rem; color:#9db4cc; line-height:1.75; white-space:pre-wrap; }

/* ── Бейдж типа вопроса ── */
.q-badge { display:inline-block; font-size:0.6rem; font-weight:600;
    letter-spacing:0.12em; text-transform:uppercase; padding:3px 9px;
    border-radius:4px; background:#0f1e35; color:#3b6fd4;
    border:1px solid #1a2e4a; margin-bottom:10px; }

/* ── Прогресс-бар ── */
.prog-wrap  { margin-bottom:18px; }
.prog-label { font-size:0.68rem; color:#2d4a6e; margin-bottom:5px; }
.prog-bg    { height:3px; background:#0f1e35; border-radius:2px; }
.prog-fill  { height:3px; border-radius:2px;
    background:linear-gradient(90deg,#1d4ed8,#3b82f6); transition:width 0.3s; }

/* ── Кнопки ── */
.stButton > button {
    background:#0d1625 !important; border:1px solid #1a2e4a !important;
    border-radius:8px !important; color:#7a9bb5 !important;
    font-family:'Inter',sans-serif !important; font-size:0.8rem !important;
    padding:0.55rem 1.2rem !important; transition:all 0.16s !important;
}
.stButton > button:hover {
    border-color:#2563eb !important; color:#60a5fa !important;
    background:#0f1e35 !important; }
.stButton > button > div, .stButton > button p, .stButton > button span {
    background:transparent !important; color:inherit !important;
    padding:0 !important; margin:0 !important; }

/* ── Бинарные кнопки (Фишинг / Легитимное) ── */
div[data-testid="column"]:nth-child(1) button.phish-btn,
div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button {
    background:rgba(239,68,68,0.07) !important;
    border:1px solid rgba(239,68,68,0.3) !important;
    color:#f87171 !important; font-weight:600 !important;
    font-size:0.88rem !important; padding:0.8rem !important;
    letter-spacing:0.03em !important;
}
div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button:hover {
    background:rgba(239,68,68,0.16) !important;
    border-color:#ef4444 !important;
    box-shadow:0 3px 16px rgba(239,68,68,0.18) !important; }

div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button {
    background:rgba(34,197,94,0.07) !important;
    border:1px solid rgba(34,197,94,0.3) !important;
    color:#4ade80 !important; font-weight:600 !important;
    font-size:0.88rem !important; padding:0.8rem !important;
    letter-spacing:0.03em !important;
}
div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button:hover {
    background:rgba(34,197,94,0.16) !important;
    border-color:#22c55e !important;
    box-shadow:0 3px 16px rgba(34,197,94,0.18) !important; }

/* ── Радио ── */
.stRadio > label { color:#4a6280 !important; font-size:0.72rem !important; }
.stRadio div[role="radiogroup"] label {
    background:#0d1625 !important; border:1px solid #152035 !important;
    border-radius:7px !important; padding:9px 14px !important;
    margin-bottom:6px !important; color:#c9d9ec !important;
    font-size:0.8rem !important; cursor:pointer !important;
    transition:border-color 0.15s !important;
}
.stRadio div[role="radiogroup"] label:hover { border-color:#2563eb !important; }

/* ── Чекбоксы ── */
.stCheckbox label { color:#c9d9ec !important; font-size:0.8rem !important; }
.stCheckbox { background:#0d1625 !important; border:1px solid #152035 !important;
    border-radius:7px !important; padding:8px 12px !important; margin-bottom:5px !important; }

/* ── Фидбэк ── */
.fb-card   { border-radius:10px; padding:16px 20px; margin:14px 0; }
.fb-ok     { background:rgba(34,197,94,0.05);  border:1px solid rgba(34,197,94,0.2); }
.fb-wrong  { background:rgba(239,68,68,0.05);  border:1px solid rgba(239,68,68,0.2); }
.fb-title  { font-size:0.95rem; font-weight:700; margin-bottom:5px; }
.fb-explain { font-size:0.78rem; color:#7a9bb5; line-height:1.65; margin-top:8px; }

/* ── Метрики ── */
.m-card { background:#0d1625; border:1px solid #152035;
    border-radius:10px; padding:16px 18px; }
.m-label { font-size:0.56rem; font-weight:600; letter-spacing:0.18em;
    text-transform:uppercase; color:#2d4a6e; margin-bottom:5px; }
.m-value { font-size:1.55rem; font-weight:700; line-height:1;
    letter-spacing:-0.02em; margin-bottom:8px; }
.m-bar-bg { height:3px; background:#0f1e35; border-radius:2px; }
.m-bar    { height:3px; border-radius:2px; }
.m-desc   { font-size:0.65rem; color:#2d4a6e; margin-top:6px; line-height:1.4; }

/* ── Профиль риска ── */
.risk-card { border-radius:10px; padding:16px 22px; margin:14px 0; }
.risk-low  { background:rgba(34,197,94,0.05);  border:1px solid rgba(34,197,94,0.18); }
.risk-mid  { background:rgba(245,158,11,0.05); border:1px solid rgba(245,158,11,0.18); }
.risk-high { background:rgba(239,68,68,0.05);  border:1px solid rgba(239,68,68,0.18); }
.risk-title { font-size:0.95rem; font-weight:700; margin-bottom:6px; }
.risk-desc  { font-size:0.77rem; color:#7a9bb5; line-height:1.65; }
.rec-item   { font-size:0.74rem; color:#7a9bb5; padding:6px 0;
    border-bottom:1px solid #0d1a2a; line-height:1.55; }

/* ── Таблица ответов ── */
.ans-row { display:flex; align-items:center; gap:10px; padding:7px 12px;
    border-radius:6px; margin-bottom:3px; font-size:0.73rem; }
.ans-ok   { background:#0a150a; }
.ans-fail { background:#150a0a; }

/* ── URL-блок ── */
.url-block { background:#060d18; border:1px solid #1a2e4a; border-radius:7px;
    padding:10px 16px; font-family:monospace; font-size:0.82rem;
    color:#60a5fa; word-break:break-all; margin:10px 0; }

/* ── SMS-блок ── */
.sms-bubble { background:#0d1e0d; border:1px solid rgba(34,197,94,0.2);
    border-radius:10px 10px 10px 2px; padding:12px 16px; margin:10px 0;
    font-size:0.82rem; color:#c9d9ec; line-height:1.6; }
.sms-sender { font-size:0.65rem; color:#4ade80; margin-bottom:5px;
    font-weight:600; letter-spacing:0.05em; }

/* Скрыть Streamlit меню */
#MainMenu, footer, header { visibility:hidden !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ══════════════════════════════════════════════════════════════════════════════

def start_question_timer():
    """Засечь время начала ответа на текущий вопрос."""
    st.session_state.q_start_time = time.time()


@st.cache_data
def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["questions"]


def select_random_questions(questions: list, n: int = 15) -> list:
    """Возвращает n случайных вопросов из полного списка."""
    return random.sample(questions, min(n, len(questions)))


def render_header(subtitle: str = ""):
    sub = subtitle or "Анализ поведения сотрудников"
    st.markdown(f"""
    <div class="ps-header">
        <div class="ps-logo">🎯</div>
        <div>
            <div class="ps-title">PhishSim</div>
            <div class="ps-sub">{sub}</div>
        </div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

DEFAULTS = {
    "page":           "profile",
    "profile":        {},
    "questions":      [],
    "idx":            0,
    "answers":        [],       # [{q_id, type, user_answer, correct_answer, correct, time_sec}]
    "show_feedback":  False,
    "last_correct":   False,
    "last_user_ans":  None,
    "q_start_time":   None,
    "mc_checks":      {},       # для multi_choice: {letter: bool}
    "tracker":        None,     # экземпляр BehaviorTracker
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# СТАТИСТИКА И МЕТРИКИ
# ══════════════════════════════════════════════════════════════════════════════

def compute_stats(answers: list, questions: list) -> dict:
    q_map = {q["id"]: q for q in questions}

    phishing_types = {"email_analysis", "url_analysis", "sms_analysis"}
    all_q    = answers
    phishing = [a for a in answers if a["type"] in phishing_types]

    correct_total = sum(1 for a in answers if a["correct"])
    total = len(answers)
    score_pct = correct_total / total * 100 if total else 0

    # Failure Rate — % фишинговых писем/ссылок/SMS, которые пользователь пропустил
    phish_only = []
    for a in phishing:
        q = q_map[a["q_id"]]
        if q["correct_answer"] in ("Фишинг", "Фишинговая"):
            phish_only.append(a)
    missed = [a for a in phish_only if not a["correct"]]
    failure_rate = len(missed) / len(phish_only) * 100 if phish_only else 0.0

    # Reporting Rate — % фишинга, который правильно идентифицировал
    reporting_rate = 100.0 - failure_rate

    # False Positive Rate — % легитимных, которые назвал фишингом
    legit_only = [a for a in answers if q_map[a["q_id"]]["correct_answer"] in ("Легитимное", "Безопасная")]
    fp = [a for a in legit_only if a["user_answer"] == "Фишинг"]  # назвал фишингом когда легитимное
    fp_rate = len(fp) / len(legit_only) * 100 if legit_only else 0.0

    # Resilience Rate — % трудных вопросов (difficulty >= 4), решённых верно
    hard = [a for a in answers if q_map[a["q_id"]]["difficulty"] >= 4]
    hard_correct = [a for a in hard if a["correct"]]
    resilience = len(hard_correct) / len(hard) * 100 if hard else 0.0

    # По типам
    by_type = {}
    for a in answers:
        t = a["type"]
        if t not in by_type:
            by_type[t] = {"total": 0, "correct": 0, "label": TYPE_LABELS.get(t, t), "times": []}
        by_type[t]["total"] += 1
        if a["correct"]:
            by_type[t]["correct"] += 1
        by_type[t]["times"].append(a["time_sec"])
    for d in by_type.values():
        d["rate"] = d["correct"] / d["total"] * 100 if d["total"] else 0
        d["avg_time"] = sum(d["times"]) / len(d["times"]) if d["times"] else 0

    # Время
    times_ok   = [a["time_sec"] for a in answers if a["correct"]]
    times_fail = [a["time_sec"] for a in answers if not a["correct"]]
    avg_ok   = sum(times_ok)   / len(times_ok)   if times_ok   else 0.0
    avg_fail = sum(times_fail) / len(times_fail) if times_fail else 0.0

    return {
        "total":          total,
        "correct":        correct_total,
        "score_pct":      round(score_pct, 1),
        "failure_rate":   round(failure_rate, 1),
        "reporting_rate": round(reporting_rate, 1),
        "fp_rate":        round(fp_rate, 1),
        "resilience":     round(resilience, 1),
        "by_type":        by_type,
        "avg_ok":         round(avg_ok, 1),
        "avg_fail":       round(avg_fail, 1),
    }


def get_risk_profile(stats: dict, profile: dict) -> dict:
    """
    Уровень риска определяется комбинацией Failure Rate и Resilience Rate.

    Failure Rate  < 25% И Resilience >= 61% → НИЗКИЙ
    Failure Rate  > 60% ИЛИ Resilience < 30% → ВЫСОКИЙ
    Иначе                                     → СРЕДНИЙ
    """
    fr  = stats["failure_rate"]
    res = stats["resilience"]

    if fr <= 25 and res >= 61:
        lvl, lvl_ru = "low", "НИЗКИЙ"
        desc = ("Сотрудник демонстрирует высокий уровень осведомлённости о фишинге — "
                "в том числе устойчив к сложным целевым атакам. "
                "Риск стать жертвой реальной фишинговой атаки минимальный.")
    elif fr > 60 or res < 30:
        lvl, lvl_ru = "high", "ВЫСОКИЙ"
        desc = ("Сотрудник с высокой вероятностью станет жертвой реальной атаки. "
                "Пропускает большинство фишинга или уязвим к сложным схемам. "
                "Необходимо срочное обучение по информационной безопасности.")
    else:
        lvl, lvl_ru = "medium", "СРЕДНИЙ"
        desc = ("Сотрудник распознаёт очевидный фишинг, но уязвим к более сложным "
                "и целевым атакам (BEC, CEO-фрод, спуфинг доменов). "
                "Рекомендуется дополнительное обучение.")

    recs = []
    if fr > 25:
        recs.append("Пройти обучение по распознаванию фишинговых писем и ссылок")
    if res < 60:
        recs.append("Отработать сложные сценарии: BEC-атаки, CEO-фрод, поддельные домены")
    if stats["fp_rate"] > 30:
        recs.append("Изучить признаки легитимных корпоративных писем — "
                    "избыточная подозрительность снижает эффективность работы")
    if stats["avg_fail"] > 0 and stats["avg_fail"] < stats["avg_ok"]:
        recs.append("Не торопиться с ответом — быстрые решения чаще оказываются ошибочными")
    if not profile.get("had_training"):
        recs.append("Пройти обязательный инструктаж по ИБ — "
                    "необученные сотрудники попадаются на фишинг в 3× чаще")

    return {"level": lvl, "level_ru": lvl_ru, "desc": desc, "recs": recs}


# ══════════════════════════════════════════════════════════════════════════════
# CSV ЭКСПОРТ
# ══════════════════════════════════════════════════════════════════════════════

def generate_csv(answers: list, questions: list, profile: dict) -> str:
    q_map  = {q["id"]: q for q in questions}
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Профиль"])
    writer.writerow(["Имя", profile.get("name", "Аноним")])
    writer.writerow(["Отдел", profile.get("department", "—")])
    writer.writerow(["Стаж", profile.get("experience", "—")])
    writer.writerow(["Возраст", profile.get("age_group", "—")])
    writer.writerow(["Обучение по ИБ", "Да" if profile.get("had_training") else "Нет"])
    writer.writerow([])
    writer.writerow(["№", "Тип вопроса", "Название", "Сложность",
                     "Ответ пользователя", "Правильный ответ", "Верно", "Время (сек)"])

    for i, a in enumerate(answers, 1):
        q = q_map.get(a["q_id"])
        if not q:
            continue
        user_ans = a["user_answer"]
        if isinstance(user_ans, list):
            user_ans = ", ".join(user_ans)
        correct_ans = q["correct_answer"]
        if isinstance(correct_ans, list):
            correct_ans = ", ".join(correct_ans)
        writer.writerow([
            i,
            TYPE_LABELS.get(q["type"], q["type"]),
            q["title"],
            q["difficulty"],
            user_ans,
            correct_ans,
            "Да" if a["correct"] else "Нет",
            a["time_sec"],
        ])

    return output.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# ЭКРАН 1 — ПРОФИЛЬ
# ══════════════════════════════════════════════════════════════════════════════

def page_profile():
    render_header()

    st.markdown("""
    <div class="ps-card" style="font-size:0.8rem;color:#4a6280;line-height:1.75">
        <div style="color:#c9d9ec;font-size:0.85rem;font-weight:600;margin-bottom:7px">
            Как работает PhishSim?
        </div>
        PhishSim оценивает вашу готовность к фишинг-угрозам через <strong style="color:#60a5fa">15 реальных сценариев</strong>
        (письма, ссылки, SMS, ситуационные задачи).<br>
        По результатам система определит ваш <strong style="color:#60a5fa">уровень риска</strong> и даст <strong style="color:#60a5fa">рекомендации</strong>.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Профиль сотрудника</div>', unsafe_allow_html=True)

    name = st.text_input(
        "Имя (необязательно — можно оставить анонимным)",
        placeholder="Например: Алия К. или Аноним",
        max_chars=60,
    )

    c1, c2 = st.columns(2)
    with c1:
        dept     = st.selectbox("Отдел", DEPARTMENTS)
        exp      = st.selectbox("Стаж работы", EXPERIENCE)
    with c2:
        age      = st.selectbox("Возрастная группа", AGE_GROUPS)
        training = st.selectbox("Проходили обучение по ИБ?",
                                ["Нет", "Да — менее года назад", "Да — более года назад"])

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

    if st.button("Начать тестирование", use_container_width=True):
        all_qs = load_questions()
        selected = select_random_questions(all_qs, n=15)

        for k, v in DEFAULTS.items():
            st.session_state[k] = v

        st.session_state.profile = {
            "name":         name.strip() if name.strip() else "Аноним",
            "department":   dept,
            "experience":   exp,
            "age_group":    age,
            "had_training": training != "Нет",
        }
        st.session_state.questions = selected
        st.session_state.q_start_time = None
        st.session_state.page      = "test"
        tracker = BehaviorTracker()
        tracker.start_session()
        st.session_state.tracker   = tracker
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ЭКРАН 2 — ТЕСТ
# ══════════════════════════════════════════════════════════════════════════════

def page_test():
    questions = st.session_state.questions
    idx       = st.session_state.idx
    total     = len(questions)

    if idx >= total:
        st.session_state.page = "result"
        st.rerun()

    q = questions[idx]
    render_header(f"Вопрос {idx + 1} из {total}")

    # Прогресс-бар
    pct = int(idx / total * 100)
    st.markdown(f"""
    <div class="prog-wrap">
        <div class="prog-label">Пройдено: {idx} / {total}</div>
        <div class="prog-bg"><div class="prog-fill" style="width:{pct}%"></div></div>
    </div>""", unsafe_allow_html=True)

    # Засечь время начала вопроса
    if st.session_state.q_start_time is None:
        start_question_timer()

    if not st.session_state.show_feedback:
        render_question(q)
    else:
        render_question(q)
        render_feedback(q)

        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        btn_label = "Следующий вопрос →" if idx + 1 < total else "Показать результаты"
        if st.button(btn_label, use_container_width=True, key="btn_next"):
            st.session_state.idx         += 1
            st.session_state.show_feedback = False
            st.session_state.last_user_ans = None
            st.session_state.mc_checks     = {}
            st.session_state.q_start_time  = None
            if st.session_state.idx >= total:
                st.session_state.page = "result"
            st.rerun()


def render_question(q: dict):
    qtype = q["type"]
    badge = TYPE_LABELS.get(qtype, qtype)
    st.markdown(f'<div class="q-badge">{badge} · сложность {q["difficulty"]}/5</div>',
                unsafe_allow_html=True)

    content = q["content"]

    # ── email_analysis ────────────────────────────────────────────────────────
    if qtype == "email_analysis":
        st.markdown(f"""
        <div class="ps-card">
            <div class="field-label">Отправитель</div>
            <div class="field-value">{content.get("from","—")}</div>
            <div class="field-label">Тема</div>
            <div class="field-value">{content.get("subject","—")}</div>
            <div class="field-divider"></div>
            <div class="field-body">{content.get("body","")}</div>
        </div>""", unsafe_allow_html=True)
        if content.get("links"):
            st.markdown('<div class="field-label" style="margin-top:4px">Ссылки в письме</div>',
                        unsafe_allow_html=True)
            for link in content["links"]:
                st.markdown(f'<div class="url-block">{link}</div>', unsafe_allow_html=True)

    # ── url_analysis ──────────────────────────────────────────────────────────
    elif qtype == "url_analysis":
        preview = content.get("email_preview")
        if preview:
            st.markdown(f"""
            <div class="ps-card">
                <div class="field-label">Письмо, в котором пришла ссылка</div>
                <div style="font-size:0.7rem;color:#4a6280;margin-top:6px;margin-bottom:2px">
                    От: <span style="color:#9db4cc">{preview.get("from","")}</span>
                </div>
                <div style="font-size:0.78rem;color:#c9d9ec;font-weight:600;margin-bottom:10px">
                    {preview.get("subject","")}
                </div>
                <div style="font-size:0.78rem;color:#9db4cc;line-height:1.6;
                            padding-top:10px;border-top:1px solid #0f1e35">
                    {preview.get("snippet","")}
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ps-card">
                <div class="field-label">Контекст</div>
                <div class="field-value">{content.get("context","")}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="field-label" style="margin-top:4px">Ссылка для анализа</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="url-block">{content.get("url","")}</div>',
                    unsafe_allow_html=True)

    # ── sms_analysis ──────────────────────────────────────────────────────────
    elif qtype == "sms_analysis":
        st.markdown(f"""
        <div class="ps-card">
            <div class="sms-sender">{content.get("sender","Неизвестно")}</div>
            <div class="sms-bubble">{content.get("body","")}</div>
        </div>""", unsafe_allow_html=True)
        if content.get("links"):
            st.markdown('<div class="field-label">Ссылки в сообщении</div>',
                        unsafe_allow_html=True)
            for link in content["links"]:
                st.markdown(f'<div class="url-block">{link}</div>', unsafe_allow_html=True)

    # ── situational / action_after ────────────────────────────────────────────
    elif qtype in ("situational", "action_after"):
        scenario = content.get("scenario", "")
        quest    = content.get("question", "Что следует сделать?")
        st.markdown(f"""
        <div class="ps-card">
            <div class="field-body">{scenario}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.82rem;color:#c9d9ec;margin:10px 0 6px;font-weight:600">'
                    f'{quest}</div>', unsafe_allow_html=True)

    # ── multi_choice ──────────────────────────────────────────────────────────
    elif qtype == "multi_choice":
        st.markdown(f"""
        <div class="ps-card">
            <div class="field-body">{content.get("scenario","")}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.8rem;color:#4a6280;margin-bottom:8px">'
                    'Отметьте ВСЕ верные варианты:</div>', unsafe_allow_html=True)

    # ── Интерфейс ответа ──────────────────────────────────────────────────────
    if not st.session_state.show_feedback:
        render_answer_ui(q)


# Типы с бинарными кнопками (2 варианта: фишинг / легитимное)
BINARY_TYPES = {"email_analysis", "url_analysis", "sms_analysis"}

def render_answer_ui(q: dict):
    qtype   = q["type"]
    options = q.get("options", [])
    key_pre = f"q_{q['id']}"

    # ── Множественный выбор (чекбоксы) ───────────────────────────────────────
    if qtype == "multi_choice":
        items = q["content"].get("items", [])
        if not st.session_state.mc_checks:
            st.session_state.mc_checks = {opt: False for opt in options}
        for item in items:
            letter = item.split(")")[0].strip()
            # Заменяем backticks на моноширинный текст для email/url
            import re as _re
            display = _re.sub(r"`([^`]+)`", r"``\1``", item)
            # Экранируем @ чтобы Streamlit не превращал email в ссылку
            display = display.replace("@", r"\@")
            checked = st.checkbox(display, key=f"{key_pre}_cb_{letter}",
                                  value=st.session_state.mc_checks.get(letter, False))
            st.session_state.mc_checks[letter] = checked
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        if st.button("Подтвердить выбор", use_container_width=True, key=f"{key_pre}_submit"):
            selected = [l for l, v in st.session_state.mc_checks.items() if v]
            submit_answer(q, selected)

    # ── Бинарные кнопки (email / url / sms — ровно 2 варианта) ──────────────
    elif qtype in BINARY_TYPES and len(options) == 2:
        st.markdown('<div class="sec-label">Ваше решение</div>', unsafe_allow_html=True)
        # Определяем порядок: первый вариант может быть "Фишинг" или "Легитимное"
        opt_a, opt_b = options[0], options[1]
        # Красная кнопка — всегда для "фишинговых" вариантов
        if "Фишинг" in opt_a or "Фишинговая" in opt_a:
            label_red, label_green = opt_a, opt_b
        else:
            label_red, label_green = opt_b, opt_a
        col_red, col_green = st.columns(2)
        with col_red:
            if st.button(f"🚨  {label_red}", use_container_width=True, key=f"{key_pre}_red"):
                submit_answer(q, label_red)
        with col_green:
            if st.button(f"✅  {label_green}", use_container_width=True, key=f"{key_pre}_green"):
                submit_answer(q, label_green)

    # ── Радио (situational, action_after — много вариантов) ──────────────────
    else:
        choice = st.radio("", options, index=None,
                          key=f"{key_pre}_radio", label_visibility="collapsed")
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        if st.button("Подтвердить ответ", use_container_width=True, key=f"{key_pre}_submit"):
            if choice is None:
                st.warning("Пожалуйста, выберите вариант ответа.")
            else:
                submit_answer(q, choice)


def submit_answer(q: dict, user_answer):
    # Точный замер времени
    elapsed = round(time.time() - (st.session_state.q_start_time or time.time()), 1)
    correct_answer = q["correct_answer"]

    # Проверка правильности
    if isinstance(correct_answer, list):
        correct = set(user_answer) == set(correct_answer)
    else:
        correct = user_answer == correct_answer

    # Запись в session_state.answers (для compute_stats)
    st.session_state.answers.append({
        "q_id":           q["id"],
        "type":           q["type"],
        "user_answer":    user_answer,
        "correct_answer": correct_answer,
        "correct":        correct,
        "time_sec":       elapsed,
    })

    # Параллельная запись через BehaviorTracker
    tracker = st.session_state.get("tracker")
    if tracker:
        triggers = [f"difficulty:{q['difficulty']}"]
        tracker.log_answer(
            question_id    = q["id"],
            question_type  = q["type"],
            question_title = q["title"],
            user_answer    = user_answer,
            correct_answer = correct_answer,
            is_correct     = correct,
            triggers       = triggers,
        )

    st.session_state.last_correct   = correct
    st.session_state.last_user_ans  = user_answer
    st.session_state.show_feedback  = True
    st.rerun()


def render_feedback(q: dict):
    correct     = st.session_state.last_correct
    user_ans    = st.session_state.last_user_ans
    explanation = q.get("explanation", "")

    cls   = "fb-ok" if correct else "fb-wrong"
    icon  = "✅" if correct else "❌"
    title = "Правильно!" if correct else "Неверно"
    color = "#4ade80" if correct else "#f87171"

    if isinstance(user_ans, list):
        user_ans_str = ", ".join(user_ans) if user_ans else "ничего не выбрано"
    else:
        user_ans_str = str(user_ans)

    correct_ans = q["correct_answer"]
    if isinstance(correct_ans, list):
        correct_ans_str = ", ".join(correct_ans)
    else:
        correct_ans_str = str(correct_ans)

    st.markdown(f"""
    <div class="fb-card {cls}">
        <div class="fb-title" style="color:{color}">{icon} {title}</div>
        <div style="font-size:0.72rem;color:#4a6280;margin-bottom:4px">
            Ваш ответ: <span style="color:#c9d9ec">{user_ans_str}</span>
            &nbsp;·&nbsp;
            Правильно: <span style="color:{color}">{correct_ans_str}</span>
        </div>
        <div class="fb-explain">{explanation}</div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ЭКРАН 3 — РЕЗУЛЬТАТЫ
# ══════════════════════════════════════════════════════════════════════════════

def page_result():
    render_header("Анализ поведения сотрудника")

    profile   = st.session_state.profile
    answers   = st.session_state.answers
    questions = st.session_state.questions

    if not answers:
        st.warning("Нет данных для анализа.")
        return

    stats = compute_stats(answers, questions)
    risk  = get_risk_profile(stats, profile)

    # ── Профиль ───────────────────────────────────────────────────────────────
    train_color = "4ade80" if profile.get("had_training") else "f87171"
    train_text  = "✓ Обучение пройдено" if profile.get("had_training") else "✗ Обучение не проходили"
    name_display = profile.get("name", "Аноним")
    st.markdown(f"""
    <div style="margin-bottom:16px">
        <div style="font-size:1rem;font-weight:600;color:#e2e8f0;margin-bottom:8px">
            {name_display}
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;font-size:0.7rem">
            <span style="background:#0d1625;border:1px solid #1a2e4a;border-radius:5px;
                  padding:3px 10px;color:#7a9bb5">{profile.get("department","—")}</span>
            <span style="background:#0d1625;border:1px solid #1a2e4a;border-radius:5px;
                  padding:3px 10px;color:#7a9bb5">{profile.get("experience","—")}</span>
            <span style="background:#0d1625;border:1px solid #1a2e4a;border-radius:5px;
                  padding:3px 10px;color:#7a9bb5">{profile.get("age_group","—")}</span>
            <span style="background:#0d1625;border:1px solid #1a2e4a;border-radius:5px;
                  padding:3px 10px;color:#{train_color}">{train_text}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Общий балл ────────────────────────────────────────────────────────────
    score_color = ("#22c55e" if stats["score_pct"] >= 75
                   else "#f59e0b" if stats["score_pct"] >= 50 else "#ef4444")
    st.markdown(f"""
    <div class="ps-card" style="display:flex;align-items:center;gap:20px;margin-bottom:8px">
        <div style="font-size:2.4rem;font-weight:700;color:{score_color};
                    letter-spacing:-0.03em;line-height:1">
            {stats["score_pct"]:.0f}%
        </div>
        <div>
            <div style="font-size:0.85rem;font-weight:600;color:#c9d9ec">
                Общий результат</div>
            <div style="font-size:0.72rem;color:#2d4a6e;margin-top:3px">
                {stats["correct"]} верных ответов из {stats["total"]} вопросов</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── 4 метрики ─────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Ключевые метрики поведения</div>',
                unsafe_allow_html=True)

    fr_col  = "#ef4444" if stats["failure_rate"]   > 60 else \
              "#f59e0b" if stats["failure_rate"]   > 25 else "#22c55e"
    rr_col  = "#22c55e" if stats["reporting_rate"] > 75 else \
              "#f59e0b" if stats["reporting_rate"] > 50 else "#ef4444"
    res_col = "#22c55e" if stats["resilience"]     > 60 else \
              "#f59e0b" if stats["resilience"]     > 30 else "#ef4444"
    fp_col  = "#22c55e" if stats["fp_rate"] < 20 else \
              "#f59e0b" if stats["fp_rate"] < 40 else "#ef4444"

    def metric_card(col, label, value, desc, color):
        bar = min(int(value), 100)
        col.markdown(f"""
        <div class="m-card">
            <div class="m-label">{label}</div>
            <div class="m-value" style="color:{color}">{value}%</div>
            <div class="m-bar-bg">
                <div class="m-bar" style="width:{bar}%;background:{color};opacity:0.75"></div>
            </div>
            <div class="m-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, "Failure Rate",        stats["failure_rate"],
                "% фишинга, который пропустили",        fr_col)
    metric_card(c2, "Reporting Rate",      stats["reporting_rate"],
                "% фишинга, правильно распознанного",   rr_col)
    metric_card(c3, "Resilience Rate",     stats["resilience"],
                "% сложных вопросов (уровень 4+) верно", res_col)
    metric_card(c4, "False Positive Rate", stats["fp_rate"],
                "% легитимного, принятого за фишинг",   fp_col)

    # ── Интерпретация Resilience Rate ─────────────────────────────────────────
    res_val = stats["resilience"]
    if res_val > 60:
        res_interp = "Высокая устойчивость к сложным атакам"
    elif res_val > 30:
        res_interp = "Средняя устойчивость — уязвим к целевым схемам"
    else:
        res_interp = "Низкая устойчивость — высокий риск BEC и CEO-фрода"
    st.markdown(
        f'<div style="font-size:0.7rem;color:#3d5a78;margin-top:6px;margin-bottom:4px">'
        f'Resilience Rate {res_val}% → {res_interp}</div>',
        unsafe_allow_html=True)

    # ── По типам вопросов ─────────────────────────────────────────────────────
    if stats["by_type"]:
        st.markdown('<div class="sec-label" style="margin-top:22px">Результаты по типам вопросов</div>',
                    unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go
            labels  = [d["label"]   for d in stats["by_type"].values()]
            correct = [d["correct"] for d in stats["by_type"].values()]
            totals  = [d["total"]   for d in stats["by_type"].values()]
            wrong   = [t - c for t, c in zip(totals, correct)]

            fig = go.Figure()
            fig.add_trace(go.Bar(name="Верно",   y=labels, x=correct,
                                 orientation="h", marker_color="#22c55e",
                                 marker=dict(line=dict(width=0))))
            fig.add_trace(go.Bar(name="Неверно", y=labels, x=wrong,
                                 orientation="h", marker_color="#ef4444",
                                 marker=dict(line=dict(width=0))))
            fig.update_layout(
                barmode="stack", height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#7a9bb5", size=11, family="Inter"),
                margin=dict(l=0, r=20, t=10, b=20),
                legend=dict(orientation="h", y=-0.2, font=dict(color="#4a6280", size=10)),
                xaxis=dict(gridcolor="#0f1e35", color="#4a6280", dtick=1),
                yaxis=dict(gridcolor="#0f1e35", color="#9db4cc"),
            )
            col_chart, col_detail = st.columns([3, 2])
            with col_chart:
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})
            with col_detail:
                for d in stats["by_type"].values():
                    r   = d["rate"]
                    col = "#22c55e" if r >= 75 else "#f59e0b" if r >= 50 else "#ef4444"
                    st.markdown(f"""
                    <div style="padding:8px 0;border-bottom:1px solid #0d1a2a">
                        <div style="display:flex;justify-content:space-between;
                                    align-items:baseline;margin-bottom:4px">
                            <span style="font-size:0.7rem;color:#7a9bb5">{d['label']}</span>
                            <span style="font-size:0.8rem;font-weight:600;color:{col}">{r:.0f}%</span>
                        </div>
                        <div style="height:2px;background:#0f1e35;border-radius:1px">
                            <div style="height:2px;width:{int(r)}%;background:{col};
                                        border-radius:1px;opacity:0.8"></div>
                        </div>
                        <div style="font-size:0.6rem;color:#2d4a6e;margin-top:3px">
                            {d['correct']} из {d['total']} верно</div>
                    </div>""", unsafe_allow_html=True)
        except ImportError:
            for d in stats["by_type"].values():
                r   = d["rate"]
                col = "#22c55e" if r >= 75 else "#f59e0b" if r >= 50 else "#ef4444"
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#9db4cc;margin-bottom:6px">'
                    f'{d["label"]}: <span style="color:{col};font-weight:600">'
                    f'{r:.0f}%</span> ({d["correct"]}/{d["total"]})</div>',
                    unsafe_allow_html=True)

    # ── Таблица по типам вопросов ───────────────────────────────────────────────
    if stats["by_type"]:
        st.markdown('<div class="sec-label" style="margin-top:22px">Детальная статистика по типам</div>',
                    unsafe_allow_html=True)
        # Заголовок таблицы
        h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 1, 1])
        for col, label in zip([h1,h2,h3,h4,h5],
                               ["Тип вопроса","Верно","Всего","%","Ср. время"]):
            col.markdown(
                f'<div style="font-size:0.58rem;font-weight:600;letter-spacing:0.18em;'
                f'text-transform:uppercase;color:#2d4a6e;padding-bottom:5px;'
                f'border-bottom:1px solid #0f1e35">{label}</div>',
                unsafe_allow_html=True)
        # Строки
        for d in stats["by_type"].values():
            r   = d["rate"]
            col = "#22c55e" if r >= 75 else "#f59e0b" if r >= 50 else "#ef4444"
            avg = f'{d["avg_time"]:.1f}с'
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.markdown(f'<div style="font-size:0.77rem;color:#9db4cc;padding:6px 0;'
                        f'border-bottom:1px solid #0a1525">{d["label"]}</div>',
                        unsafe_allow_html=True)
            for col_w, val, clr in [
                (c2, str(d["correct"]),    "#9db4cc"),
                (c3, str(d["total"]),      "#9db4cc"),
                (c4, f'{r:.0f}%',          col),
                (c5, avg,                  "#7a9bb5"),
            ]:
                col_w.markdown(
                    f'<div style="font-size:0.77rem;font-weight:600;color:{clr};'
                    f'padding:6px 0;border-bottom:1px solid #0a1525">{val}</div>',
                    unsafe_allow_html=True)

    # ── Поведенческий анализ (время) ──────────────────────────────────────────
    if stats["avg_ok"] > 0 or stats["avg_fail"] > 0:
        st.markdown('<div class="sec-label" style="margin-top:22px">Поведенческий анализ</div>',
                    unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            t_insight = ""
            t_col = "#4ade80"
            if stats["avg_fail"] > 0 and stats["avg_ok"] > 0:
                if stats["avg_fail"] < stats["avg_ok"]:
                    t_insight = "Ошибки принимались быстрее — спешка повышает риск"
                    t_col = "#f59e0b"
                else:
                    t_insight = "Медленные ответы чаще верны — вдумчивость помогает"
            st.markdown(f"""
            <div class="ps-card">
                <div class="field-label">Время принятия решений</div>
                <div style="display:flex;gap:24px;margin-top:10px">
                    <div>
                        <div style="font-size:1.2rem;font-weight:600;color:#4ade80;
                                    letter-spacing:-0.01em">{stats['avg_ok']:.1f}с</div>
                        <div style="font-size:0.62rem;color:#2d4a6e;margin-top:2px">при верном</div>
                    </div>
                    <div style="width:1px;background:#0f1e35"></div>
                    <div>
                        <div style="font-size:1.2rem;font-weight:600;color:#f87171;
                                    letter-spacing:-0.01em">{stats['avg_fail']:.1f}с</div>
                        <div style="font-size:0.62rem;color:#2d4a6e;margin-top:2px">при ошибке</div>
                    </div>
                </div>
                {f'<div style="font-size:0.72rem;color:{t_col};margin-top:10px">{t_insight}</div>' if t_insight else ''}
            </div>""", unsafe_allow_html=True)

        with cb:
            # Самый сложный тип
            worst = min(stats["by_type"].values(), key=lambda d: d["rate"]) \
                    if stats["by_type"] else None
            worst_txt = (f"Наибольшие затруднения вызвал тип: "
                         f"<strong style='color:#f87171'>{worst['label']}</strong> "
                         f"({worst['rate']:.0f}% верно)"
                         if worst else "—")
            st.markdown(f"""
            <div class="ps-card">
                <div class="field-label">Уязвимый тип вопросов</div>
                <div style="font-size:0.78rem;color:#9db4cc;margin-top:10px;line-height:1.65">
                    {worst_txt}
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Профиль риска ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label" style="margin-top:22px">Профиль риска</div>',
                unsafe_allow_html=True)

    lvl = risk["level"]
    col_r = {"low": "#4ade80", "medium": "#f59e0b", "high": "#ef4444"}[lvl]
    cls_r = {"low": "risk-low",  "medium": "risk-mid", "high": "risk-high"}[lvl]

    st.markdown(f"""
    <div class="risk-card {cls_r}">
        <div style="display:flex;align-items:center;gap:9px;margin-bottom:7px">
            <div style="width:8px;height:8px;border-radius:50%;background:{col_r}"></div>
            <div class="risk-title" style="color:{col_r}">Уровень риска: {risk['level_ru']}</div>
        </div>
        <div class="risk-desc">{risk['desc']}</div>
    </div>""", unsafe_allow_html=True)

    if risk["recs"]:
        st.markdown('<div class="field-label" style="margin-top:14px">'
                    'Рекомендации для отдела ИБ</div>', unsafe_allow_html=True)
        for i, rec in enumerate(risk["recs"], 1):
            st.markdown(f'<div class="rec-item">{i}. {rec}</div>', unsafe_allow_html=True)

    # ── Журнал ответов ────────────────────────────────────────────────────────
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    if "show_journal" not in st.session_state:
        st.session_state.show_journal = False

    btn_lbl = "Скрыть журнал ответов" if st.session_state.show_journal \
              else "Показать журнал ответов"
    if st.button(btn_lbl, key="btn_journal"):
        st.session_state.show_journal = not st.session_state.show_journal
        st.rerun()

    if st.session_state.show_journal:
        st.markdown('<div class="sec-label">Журнал ответов</div>', unsafe_allow_html=True)
        q_map = {q["id"]: q for q in questions}
        for i, a in enumerate(answers, 1):
            q = q_map.get(a["q_id"])
            if not q:
                continue
            cls_row = "ans-ok" if a["correct"] else "ans-fail"
            icon    = "✅" if a["correct"] else "❌"
            ua = ", ".join(a["user_answer"]) if isinstance(a["user_answer"], list) \
                 else str(a["user_answer"])
            st.markdown(f"""
            <div class="ans-row {cls_row}">
                <span>{icon}</span>
                <span style="flex:1;color:#9db4cc">{q['title']} — {q['content'].get('subject',q['content'].get('url',q['content'].get('sender','')))[:55]}</span>
                <span style="color:#4a6280;min-width:110px;font-size:0.7rem">{TYPE_LABELS.get(q['type'],q['type'])}</span>
                <span style="color:#2d4a6e;min-width:55px;font-size:0.7rem">{a['time_sec']}с</span>
            </div>""", unsafe_allow_html=True)

    # ── Запись в Google Sheets ────────────────────────────────────────────────
    if not st.session_state.get("saved_to_sheets"):
        saved = log_result(profile, stats, risk)
        if saved:
            st.session_state.saved_to_sheets = True
            st.markdown(
                '<div style="background:rgba(34,197,94,0.07);border:1px solid '
                'rgba(34,197,94,0.2);border-radius:8px;padding:10px 16px;'
                'font-size:0.75rem;color:#4ade80;margin-bottom:12px">'
                '✓ Результаты сохранены в общую таблицу</div>',
                unsafe_allow_html=True,
            )

    # ── CSV СКАЧАТЬ ───────────────────────────────────────────────────────────
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    col_dl, col_restart = st.columns([1, 1])

    with col_dl:
        csv_data = generate_csv(answers, questions, profile)
        st.download_button(
            label="Скачать результаты (CSV)",
            data=csv_data,
            file_name="phishsim_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_restart:
        if st.button("Пройти тест заново", use_container_width=True, key="btn_restart"):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.session_state.saved_to_sheets = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# РОУТЕР
# ══════════════════════════════════════════════════════════════════════════════

page = st.session_state.page
if   page == "profile": page_profile()
elif page == "test":    page_test()
elif page == "result":  page_result()