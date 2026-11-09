#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام تنبؤ ذاتي التطور (Self-Evolving Forecaster)
- يقرأ كل ملفات CSV/JSON من مجلد data/ (مثلاً ما تصدّره من Promoter Cloud)
- ينظف البيانات تلقائياً
- يختار أفضل نموذج تلقائياً (تقسيم زمني صحيح بدون تسريب بيانات)
- يكتشف تراجع الدقة (Drift) على البيانات الجديدة ويعيد التدريب تلقائياً
- يعمل كخدمة دائمة: يراقب المجلد لحظياً + إعادة تدريب يومية في ساعة محددة

التثبيت:   pip install pandas numpy scikit-learn joblib
أمثلة:
  python auto_forecaster.py --demo                      # تجربة كاملة ببيانات تجريبية
  python auto_forecaster.py --once --target المبيعات      # دورة واحدة + تنبؤ
  python auto_forecaster.py --daemon --daily-at 03:00   # تشغيل دائم
"""
import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("forecaster")


class AutoForecaster:
    def __init__(self, data_dir="data", model_dir="models", target=None, date_col=None,
                 drift_factor=1.3, min_new_rows=5):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.model_dir.mkdir(exist_ok=True)
        self.target = target
        self.date_col = date_col
        self.feats = []
        self.drift_factor = drift_factor      # الدقة تعتبر متراجعة إذا زاد الخطأ بهذه النسبة
        self.min_new_rows = min_new_rows      # أقل عدد صفوف جديدة لفحص الدرفت
        self.model = None
        self.meta = {"n_trained": 0, "baseline_mae": None, "best_model": None, "trained_at": None}
        self._fingerprint = None
        self._load_saved()

    # ---------- 1) جلب البيانات ----------
    def _files(self):
        return sorted(p for p in self.data_dir.glob("*") if p.suffix.lower() in (".csv", ".json"))

    def fingerprint(self):
        return tuple((p.name, p.stat().st_mtime, p.stat().st_size) for p in self._files())

    def load_raw(self):
        frames = []
        for p in self._files():
            try:
                if p.suffix.lower() == ".csv":
                    frames.append(pd.read_csv(p))
                else:
                    try:
                        frames.append(pd.read_json(p))
                    except ValueError:
                        frames.append(pd.json_normalize(json.loads(p.read_text(encoding="utf-8"))))
            except Exception as e:
                log.warning("تعذّرت قراءة %s: %s", p.name, e)
        if not frames:
            raise FileNotFoundError(f"لا توجد ملفات CSV/JSON داخل {self.data_dir}/")
        return pd.concat(frames, ignore_index=True).drop_duplicates()

    # ---------- 2) التنظيف التلقائي ----------
    def clean(self, df):
        df = df.copy()
        if self.date_col is None:
            for c in df.columns:
                if df[c].dtype == object:
                    parsed = pd.to_datetime(df[c], errors="coerce")
                    if parsed.notna().mean() > 0.8:
                        self.date_col = c
                        break
        if self.date_col is None:
            self.date_col = "_t"
            df["_t"] = pd.date_range("2000-01-01", periods=len(df), freq="D")
        df[self.date_col] = pd.to_datetime(df[self.date_col], errors="coerce")
        df = df.dropna(subset=[self.date_col]).sort_values(self.date_col)
        df = df.drop_duplicates(subset=[self.date_col], keep="last")

        num = [c for c in df.select_dtypes(include=[np.number]).columns]
        if self.target is None:
            self.target = num[-1]
        self.feats = [c for c in num if c != self.target]

        for c in num:
            df[c] = df[c].interpolate(limit_direction="both").fillna(df[c].median())
        for c in self.feats:  # قص القيم الشاذة (Winsorize) للمدخلات فقط
            lo, hi = df[c].quantile([0.01, 0.99])
            df[c] = df[c].clip(lo, hi)
        df = df.dropna(subset=[self.target])
        return df[[self.date_col] + self.feats + [self.target]].reset_index(drop=True)

    # ---------- 3) هندسة الميزات ----------
    def featurize(self, df):
        t, d = self.target, self.date_col
        out = df.copy()
        out["lag_1"] = out[t].shift(1)
        out["lag_7"] = out[t].shift(7)
        out["roll_7"] = out[t].shift(1).rolling(7, min_periods=3).mean()
        out["dow"] = out[d].dt.dayofweek
        out["month"] = out[d].dt.month
        out["dayofyear"] = out[d].dt.dayofyear
        return out

    @property
    def cols(self):
        return self.feats + ["lag_1", "lag_7", "roll_7", "dow", "month", "dayofyear"]

    # ---------- 4) التدريب مع اختيار أفضل نموذج ----------
    def train(self, df):
        feat = self.featurize(df).dropna(subset=self.cols + [self.target])
        if len(feat) < 30:
            raise ValueError("البيانات قليلة جداً (أقل من 30 صفاً بعد التجهيز).")
        cut = int(len(feat) * 0.8)  # تقسيم زمني: الأقدم للتدريب والأحدث للاختبار
        tr, te = feat.iloc[:cut], feat.iloc[cut:]
        candidates = {
            "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
            "GradientBoosting": GradientBoostingRegressor(random_state=42),
            "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        }
        scores = {}
        for name, m in candidates.items():
            m.fit(tr[self.cols], tr[self.target])
            scores[name] = mean_absolute_error(te[self.target], m.predict(te[self.cols]))
        naive = mean_absolute_error(te[self.target], te["lag_1"])
        best = min(scores, key=scores.get)
        log.info("نتائج MAE: %s | خط الأساس (آخر قيمة) = %.2f", {k: round(v, 2) for k, v in scores.items()}, naive)
        log.info("🏆 أفضل نموذج: %s", best)
        if scores[best] >= naive:
            log.warning("⚠️ النموذج لا يتفوق على التوقع الساذج؛ البيانات قد لا تحمل إشارة تنبؤية كافية.")

        final = candidates[best]
        final.fit(feat[self.cols], feat[self.target])  # إعادة تدريب على كل البيانات
        self.model = final
        self.meta = {"n_trained": len(df), "baseline_mae": float(scores[best]), "best_model": best,
                     "naive_mae": float(naive), "trained_at": datetime.now().isoformat(timespec="seconds"),
                     "target": self.target, "date_col": self.date_col, "feats": self.feats}
        self._save()

    # ---------- 5) كشف التراجع (Drift) ----------
    def check_drift(self, df):
        n_new = len(df) - self.meta["n_trained"]
        if n_new < self.min_new_rows:
            return False
        feat = self.featurize(df)
        new = feat.iloc[self.meta["n_trained"]:].dropna(subset=self.cols + [self.target])
        if new.empty:
            return False
        mae = mean_absolute_error(new[self.target], self.model.predict(new[self.cols]))
        limit = self.meta["baseline_mae"] * self.drift_factor
        log.info("📊 فحص الدقة على %d صفاً جديداً: MAE=%.2f (الحد=%.2f)", len(new), mae, limit)
        return mae > limit

    # ---------- 6) الدورة الكاملة ----------
    def cycle(self, force=False):
        df = self.clean(self.load_raw())
        if self.model is None:
            log.info("🆕 لا يوجد نموذج محفوظ، جاري التدريب الأول...")
            self.train(df)
        elif force:
            log.info("⏰ إعادة تدريب مجدولة...")
            self.train(df)
        elif len(df) > self.meta["n_trained"]:
            if self.check_drift(df):
                log.info("⚠️ تراجع في الدقة! إعادة تدريب تلقائية...")
                self.train(df)
            else:
                log.info("✨ النموذج مستقر، لا حاجة لإعادة التدريب.")
        self._fingerprint = self.fingerprint()
        return df

    # ---------- 7) التنبؤ ----------
    def forecast(self, df, steps=7):
        work = df.copy()
        step = work[self.date_col].diff().median()
        preds = []
        for _ in range(steps):
            row = work.iloc[[-1]].copy()
            row[self.date_col] = row[self.date_col].iloc[0] + step
            row[self.target] = np.nan
            work = pd.concat([work, row], ignore_index=True)
            x = self.featurize(work).iloc[[-1]][self.cols]
            p = float(self.model.predict(x)[0])
            work.loc[work.index[-1], self.target] = p
            preds.append((work[self.date_col].iloc[-1], p))
        return pd.DataFrame(preds, columns=[self.date_col, f"{self.target}_متوقع"])

    # ---------- 8) خدمة دائمة ----------
    def daemon(self, poll=30, daily_at="03:00", steps=7):
        log.info("🚀 الخدمة تعمل. مراقبة المجلد كل %ds | تحديث يومي الساعة %s", poll, daily_at)
        last_daily = None
        while True:
            try:
                now = datetime.now()
                due_daily = now.strftime("%H:%M") >= daily_at and last_daily != now.date()
                changed = self.fingerprint() != self._fingerprint
                if due_daily or changed or self.model is None:
                    df = self.cycle(force=due_daily and not changed)
                    if due_daily:
                        last_daily = now.date()
                    out = self.forecast(df, steps)
                    out.to_csv(self.model_dir / "latest_forecast.csv", index=False, encoding="utf-8-sig")
                    log.info("📈 تم حفظ التنبؤ في %s", self.model_dir / "latest_forecast.csv")
            except Exception as e:
                log.error("خطأ (الخدمة مستمرة): %s", e)
            time.sleep(poll)

    # ---------- حفظ/تحميل ----------
    def _save(self):
        joblib.dump(self.model, self.model_dir / "model.joblib")
        (self.model_dir / "meta.json").write_text(json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_saved(self):
        mp, jp = self.model_dir / "model.joblib", self.model_dir / "meta.json"
        if mp.exists() and jp.exists():
            self.model = joblib.load(mp)
            self.meta = json.loads(jp.read_text(encoding="utf-8"))
            self.target = self.target or self.meta.get("target")
            self.date_col = self.date_col or self.meta.get("date_col")
            self.feats = self.meta.get("feats", [])
            log.info("📦 تم تحميل نموذج محفوظ (%s)", self.meta.get("best_model"))


# ---------- بيانات تجريبية ----------
def make_demo(data_dir="data"):
    Path(data_dir).mkdir(exist_ok=True)
    rng = np.random.default_rng(0)
    n = 400
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    price = 100 + rng.normal(0, 3, n).cumsum() * 0.3
    market = 70 + 10 * np.sin(np.arange(n) / 30) + rng.normal(0, 1, n)
    demand = 300 + 0.5 * np.arange(n) + 40 * np.sin(2 * np.pi * np.arange(n) / 7) \
        - 1.5 * price + 2 * market + rng.normal(0, 10, n)
    df = pd.DataFrame({"التاريخ": dates, "السعر": price, "مؤشر_السوق": market, "الطلب": demand})
    df.loc[rng.choice(n, 8, replace=False), "السعر"] = np.nan  # قيم مفقودة للمعالجة
    df.iloc[:300].to_csv(f"{data_dir}/part1.csv", index=False)
    return df.iloc[300:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--model-dir", default="models")
    ap.add_argument("--target")
    ap.add_argument("--date-col")
    ap.add_argument("--steps", type=int, default=7)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--daemon", action="store_true")
    ap.add_argument("--daily-at", default="03:00")
    ap.add_argument("--poll", type=int, default=30)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    if a.demo:
        later = make_demo(a.data_dir)
        bot = AutoForecaster(a.data_dir, a.model_dir, target="الطلب", date_col="التاريخ")
        bot.cycle()
        log.info("--- وصلت بيانات جديدة (يتغير السوق فجأة) ---")
        later = later.copy()
        later["الطلب"] += 250  # تغيّر مفاجئ لإثبات اكتشاف الدرفت
        later.to_csv(f"{a.data_dir}/part2.csv", index=False)
        df = bot.cycle()
        print(bot.forecast(df, a.steps).to_string(index=False))
        return

    bot = AutoForecaster(a.data_dir, a.model_dir, a.target, a.date_col)
    if a.daemon:
        bot.daemon(a.poll, a.daily_at, a.steps)
    else:
        df = bot.cycle()
        print(bot.forecast(df, a.steps).to_string(index=False))


if __name__ == "__main__":
    main()
