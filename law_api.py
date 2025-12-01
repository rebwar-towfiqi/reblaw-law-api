# law_api.py
from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from typing import Optional

DB_PATH = "iran_laws.db"  # همین فایل را کنار law_api.py روی Railway قرار می‌دهی

app = FastAPI(
    title="RebLaw Legal API",
    description="Official law article API for RebLaw (Iranian laws)",
    version="1.0.0",
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class ArticleByNameRequest(BaseModel):
    law_name: str        # مثال: "قانون مدنی"
    article_number: int  # مثال: 10


class ArticleResponse(BaseModel):
    success: bool
    law_name: Optional[str] = None
    law_code: Optional[str] = None
    article_number: Optional[int] = None
    text: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None


def map_law_name_to_code(law_name: str) -> Optional[str]:
    """
    تبدیل نام قانون (فارسی) به ستون code در جدول articles.
    این را با ساختار واقعی دیتابیس خودت هماهنگ می‌کنیم.
    """
    name = law_name.strip().replace("‌", "").replace(" ", "")
    if "مدنی" in name:
        return "قانون_مدنی"
    if "آیین" in name and "دادرسی" in name and "مدنی" in name:
        return "قانون_آیین_دادرسی_مدنی"
    if "آیین" in name and "دادرسی" in name and "کیفری" in name:
        return "قانون_آیین_دادرسی_کیفری"
    if "تجارت" in name and "لایحه" not in name:
        return "قانون_تجارت"
    if "مجازات" in name and "کتابپنجم" in name.replace(" ", ""):
        return "کتاب_پنجم_قانون_مجازات_اسلامی_(تعزیرات_و_مجازات‌های_بازدارنده)"
    return None


@app.post("/api/article-by-name", response_model=ArticleResponse)
def get_article_by_name(req: ArticleByNameRequest):
    law_code = map_law_name_to_code(req.law_name)
    if not law_code:
        return ArticleResponse(
            success=False,
            error="نام قانون پشتیبانی نمی‌شود یا ناشناخته است.",
        )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT code, id, text
        FROM articles
        WHERE code = ? AND id = ?
        LIMIT 1
        """,
        (law_code, req.article_number),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return ArticleResponse(
            success=False,
            error="ماده‌ای با این مشخصات در پایگاه داده یافت نشد.",
        )

    return ArticleResponse(
        success=True,
        law_name=req.law_name,
        law_code=row["code"],
        article_number=row["id"],
        text=row["text"],
        source="iran_laws.db – RebLaw official database",
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
