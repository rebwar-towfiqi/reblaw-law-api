# law_api.py
import os
import sqlite3
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse



DB_PATH = os.getenv("DB_PATH", "iran_laws.db")  # فایل DB کنار law_api.py روی Railway

app = FastAPI(
    title="RebLaw Legal API",
    description="Official law article API + AI Judge score API for RebLaw",
    version="1.1.0",
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# 1) Article By Name API
# =========================
class ArticleByNameRequest(BaseModel):
    law_name: str
    article_number: int


class ArticleResponse(BaseModel):
    success: bool
    law_name: Optional[str] = None
    law_code: Optional[str] = None
    article_number: Optional[int] = None
    text: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None


def map_law_name_to_code(law_name: str) -> Optional[str]:
    name = (law_name or "").strip()
    name = name.replace("‌", "").replace(" ", "")
    name = name.replace("آئین", "آیین")

    if "آیین" in name and "دادرسی" in name and "مدنی" in name:
        return "قانون_آیین_دادرسی_مدنی"

    if "آیین" in name and "دادرسی" in name and "کیفری" in name:
        return "قانون_آیین_دادرسی_کیفری"

    if "اجرای" in name and "احکام" in name and "مدنی" in name:
        return "قانون_اجرای_احکام_مدنی"

    if "تجارت" in name and "لایحه" not in name:
        return "قانون_تجارت"

    if "مجازات" in name and ("تعزیرات" in name or "کتابپنجم" in name or "کتابپنجم" in name.replace(" ", "")):
        return "کتاب_پنجم_قانون_مجازات_اسلامی_(تعزیرات_و_مجازات‌های_بازدارنده)"

    if "مجازات" in name:
        return "حقوق_جزا"

    if "مدنی" in name:
        return "قانون_مدنی"

    return None


@app.post("/api/ai-judge-score", response_model=JudgeScoreResponse)
def ai_judge_score(
    req: JudgeScoreRequest,
    x_reblaw_game_secret: Optional[str] = Header(default=None, alias="X-RebLaw-Game-Secret"),
):
    require_secret(x_reblaw_game_secret)

    payload = {
        "score_total": 86,
        "feedback": {
            "verdict_fa": "با توجه به ساختار منطقی و اشاره به ادله، دفاعیه قابل قبول است.",
            "strengths": ["ساختار استدلال", "اشاره به قرائن"],
            "weaknesses": ["کمبود استناد حقوقی صریح"],
            "tips": ["۲ ماده قانونی مرتبط را صریح ذکر کن.", "زنجیره ادله را با ترتیب زمانی بیان کن."],
            "breakdown": {"logic": 24, "evidence": 20, "law": 18, "structure": 14, "persuasion": 10},
            "confidence": 0.78
        }
    }

    return JSONResponse(
        content=payload,
        media_type="application/json; charset=utf-8"
    )



# =========================
# 2) AI Judge Score API
# =========================

# پلاگین شما این هدر را (اختیاری) می‌فرستد: X-RebLaw-Game-Secret
# اگر در Railway مقدار REBLAW_GAME_SECRET را ست کنید، اینجا چک می‌شود.
def require_secret(x_reblaw_game_secret: Optional[str]):
    expected = (os.getenv("REBLAW_GAME_SECRET") or "").strip()
    if expected and (x_reblaw_game_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class JudgeScoreRequest(BaseModel):
    # بدنه‌ای که پلاگین می‌فرستد؛ بعضی فیلدها اختیاری‌اند
    app: Optional[str] = None
    version: Optional[str] = None
    lang: Optional[str] = "fa"
    user: Optional[Dict[str, Any]] = None
    case: Optional[Dict[str, Any]] = None
    role: str
    argument: str
    rubric: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"  # اگر پلاگین فیلدهای بیشتری فرستاد، خطا ندهد


class JudgeFeedback(BaseModel):
    verdict_fa: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    tips: List[str] = []
    breakdown: Dict[str, int] = {}
    confidence: float = 0.0


class JudgeScoreResponse(BaseModel):
    score_total: int
    feedback: JudgeFeedback


@app.post("/api/ai-judge-score", response_model=JudgeScoreResponse)
def ai_judge_score(
    req: JudgeScoreRequest,
    x_reblaw_game_secret: Optional[str] = Header(default=None, alias="X-RebLaw-Game-Secret"),
):
    require_secret(x_reblaw_game_secret)

    # فعلاً نمونه پاسخ ثابت (برای تست اتصال)
    # در گام بعدی همینجا را به “قاضی واقعی” وصل می‌کنیم.
    return JudgeScoreResponse(
        score_total=86,
        feedback=JudgeFeedback(
            verdict_fa="با توجه به ساختار منطقی و اشاره به ادله، دفاعیه قابل قبول است.",
            strengths=["ساختار استدلال", "اشاره به قرائن"],
            weaknesses=["کمبود استناد حقوقی صریح"],
            tips=["۲ ماده قانونی مرتبط را صریح ذکر کن.", "زنجیره ادله را با ترتیب زمانی بیان کن."],
            breakdown={"logic": 24, "evidence": 20, "law": 18, "structure": 14, "persuasion": 10},
            confidence=0.78,
        ),
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}





