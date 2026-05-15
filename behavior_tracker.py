"""
behavior_tracker.py — Трекер поведения сотрудника при тестировании на фишинг
Дипломный проект АУЭС · «Анализ влияния фишинга на поведение сотрудников»
"""

import time
import pandas as pd
from datetime import datetime


class BehaviorTracker:
    def __init__(self):
        self.answers = []
        self.start_time = None
        self.current_question_start = None

    def start_session(self):
        """Начать сессию тестирования."""
        self.answers = []
        self.start_time = datetime.now()

    def start_question(self):
        """Засечь время начала ответа на вопрос."""
        self.current_question_start = time.time()

    def log_answer(self, question_id, question_type, question_title,
                   user_answer, correct_answer, is_correct, triggers=None):
        """Сохранить ответ с метаданными."""
        elapsed = (
            round(time.time() - self.current_question_start, 2)
            if self.current_question_start else None
        )
        if isinstance(user_answer, list):
            user_answer_str = ", ".join(sorted(str(x) for x in user_answer))
        else:
            user_answer_str = str(user_answer)

        if isinstance(correct_answer, list):
            correct_answer_str = ", ".join(sorted(str(x) for x in correct_answer))
        else:
            correct_answer_str = str(correct_answer)

        self.answers.append({
            "timestamp":          datetime.now().isoformat(),
            "question_id":        question_id,
            "question_type":      question_type,
            "question_title":     question_title,
            "user_answer":        user_answer_str,
            "correct_answer":     correct_answer_str,
            "is_correct":         is_correct,
            "time_taken_seconds": elapsed,
            "triggers":           str(triggers) if triggers else "",
        })

    def get_summary_by_type(self):
        """Статистика по типам вопросов."""
        summary = {}
        for answer in self.answers:
            q_type = answer["question_type"]
            if q_type not in summary:
                summary[q_type] = {"correct": 0, "total": 0}
            summary[q_type]["total"] += 1
            if answer["is_correct"]:
                summary[q_type]["correct"] += 1
        for q_type in summary:
            total = summary[q_type]["total"]
            correct = summary[q_type]["correct"]
            summary[q_type]["percent"] = round(correct / total * 100, 1) if total > 0 else 0
        return summary

    def get_total_stats(self):
        """Общая статистика сессии."""
        total = len(self.answers)
        correct = sum(1 for a in self.answers if a["is_correct"])
        return {
            "total":           total,
            "correct":         correct,
            "percent":         round(correct / total * 100, 1) if total > 0 else 0,
            "failure_rate":    round((total - correct) / total * 100, 1) if total > 0 else 0,
            "resilience_rate": round(correct / total * 100, 1) if total > 0 else 0,
        }

    def get_average_time_by_type(self):
        """Среднее время ответа по типам вопросов."""
        avg_time = {}
        for answer in self.answers:
            q_type = answer["question_type"]
            time_taken = answer["time_taken_seconds"]
            if time_taken is None:
                continue
            if q_type not in avg_time:
                avg_time[q_type] = {"total_time": 0, "count": 0}
            avg_time[q_type]["total_time"] += time_taken
            avg_time[q_type]["count"] += 1
        for q_type in avg_time:
            total_t = avg_time[q_type]["total_time"]
            count = avg_time[q_type]["count"]
            avg_time[q_type]["avg_seconds"] = round(total_t / count, 2) if count > 0 else 0
        return avg_time

    def get_failure_rate(self):
        """Failure Rate — % фишинговых вопросов с неверным ответом."""
        phishing_types = {"email_analysis", "url_analysis", "sms_analysis"}
        phishing_answers = [a for a in self.answers if a["question_type"] in phishing_types]
        if not phishing_answers:
            return 0.0
        missed = sum(1 for a in phishing_answers if not a["is_correct"])
        return round(missed / len(phishing_answers) * 100, 1)

    def get_reporting_rate(self):
        """Reporting Rate — % фишинга, правильно распознанного."""
        return round(100.0 - self.get_failure_rate(), 1)

    def get_resilience_rate(self):
        """Resilience Rate — % верных ответов на сложные вопросы (difficulty >= 4)."""
        hard_answers = [
            a for a in self.answers
            if "difficulty:4" in a.get("triggers", "") or
               "difficulty:5" in a.get("triggers", "")
        ]
        if not hard_answers:
            return self.get_total_stats()["resilience_rate"]
        correct = sum(1 for a in hard_answers if a["is_correct"])
        return round(correct / len(hard_answers) * 100, 1)

    def get_slowest_question(self):
        """Вопрос с максимальным временем ответа."""
        timed = [a for a in self.answers if a["time_taken_seconds"] is not None]
        return max(timed, key=lambda a: a["time_taken_seconds"]) if timed else None

    def get_fastest_wrong_answer(self):
        """Самый быстрый неверный ответ — признак невнимательности."""
        wrong = [a for a in self.answers
                 if not a["is_correct"] and a["time_taken_seconds"] is not None]
        return min(wrong, key=lambda a: a["time_taken_seconds"]) if wrong else None

    def get_trigger_vulnerability(self):
        """Анализ уязвимости по психологическим триггерам."""
        trigger_stats = {}
        for answer in self.answers:
            triggers_raw = answer.get("triggers", "")
            if not triggers_raw or triggers_raw == "None":
                continue
            tags = [t.strip() for t in
                    triggers_raw.replace("[","").replace("]","").replace("'","").split(",")
                    if t.strip() and not t.strip().startswith("difficulty")]
            for tag in tags:
                if tag not in trigger_stats:
                    trigger_stats[tag] = {"total": 0, "missed": 0}
                trigger_stats[tag]["total"] += 1
                if not answer["is_correct"]:
                    trigger_stats[tag]["missed"] += 1
        for tag in trigger_stats:
            total = trigger_stats[tag]["total"]
            trigger_stats[tag]["miss_rate"] = (
                round(trigger_stats[tag]["missed"] / total * 100, 1) if total > 0 else 0
            )
        return trigger_stats

    def get_risk_level(self, resilience_rate):
        """
        Уровень риска по Resilience Rate:
        0–30%   → ВЫСОКИЙ
        31–60%  → СРЕДНИЙ
        61–100% → НИЗКИЙ
        """
        if resilience_rate <= 30:
            return (
                "ВЫСОКИЙ",
                "Сотрудник очень уязвим к фишингу. "
                "Пропускает большинство атак, включая очевидные. "
                "Требуется срочное обучение по информационной безопасности.",
            )
        elif resilience_rate <= 60:
            return (
                "СРЕДНИЙ",
                "Сотрудник имеет базовые знания, но уязвим к сложным "
                "целевым атакам: BEC, CEO-фрод, спуфинг доменов. "
                "Рекомендуется дополнительное обучение.",
            )
        else:
            return (
                "НИЗКИЙ",
                "Сотрудник демонстрирует хорошую устойчивость к фишингу — "
                "в том числе к нетривиальным схемам. "
                "Достаточно планового повторного инструктажа.",
            )

    def export_to_csv(self, filename="results.csv"):
        """Экспорт всех ответов в CSV."""
        if not self.answers:
            return None
        df = pd.DataFrame(self.answers)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        return filename

    def export_to_dataframe(self):
        """Ответы как DataFrame."""
        return pd.DataFrame(self.answers) if self.answers else pd.DataFrame()

    def get_full_report(self):
        """Сводный отчёт по всем метрикам."""
        stats = self.get_total_stats()
        res = stats["resilience_rate"]
        lvl, lvl_desc = self.get_risk_level(res)
        return {
            "total_stats":      stats,
            "by_type":          self.get_summary_by_type(),
            "avg_time_by_type": self.get_average_time_by_type(),
            "failure_rate":     self.get_failure_rate(),
            "reporting_rate":   self.get_reporting_rate(),
            "resilience_rate":  res,
            "risk_level":       lvl,
            "risk_description": lvl_desc,
            "trigger_vuln":     self.get_trigger_vulnerability(),
            "slowest_question": self.get_slowest_question(),
            "fastest_wrong":    self.get_fastest_wrong_answer(),
            "session_start":    self.start_time.isoformat() if self.start_time else None,
        }