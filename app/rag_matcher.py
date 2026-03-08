from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class JobProfile:
    title: str
    description: str
    skills: list[str]

    @property
    def document(self) -> str:
        return f"{self.title}。{self.description}。技能：{' '.join(self.skills)}"


class JobMatcherRAG:
    """Local RAG pipeline: retrieve with token similarity, then generate reasons."""

    def __init__(self, knowledge_base_path: str | Path) -> None:
        self.knowledge_base_path = Path(knowledge_base_path)
        self.jobs = self._load_jobs()

    def _load_jobs(self) -> list[JobProfile]:
        payload = json.loads(self.knowledge_base_path.read_text(encoding="utf-8"))
        return [JobProfile(**item) for item in payload]

    @staticmethod
    def normalize_text(content: str) -> str:
        return re.sub(r"\s+", " ", content).strip().lower()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        segments = re.split(r"[^\w\u4e00-\u9fff]+", text.lower())
        return [seg for seg in segments if seg]

    @classmethod
    def _cosine(cls, text_a: str, text_b: str) -> float:
        tokens_a = cls._tokenize(text_a)
        tokens_b = cls._tokenize(text_b)
        if not tokens_a or not tokens_b:
            return 0.0

        vec_a = Counter(tokens_a)
        vec_b = Counter(tokens_b)
        dot = sum(vec_a[token] * vec_b.get(token, 0) for token in vec_a)
        norm_a = math.sqrt(sum(value * value for value in vec_a.values()))
        norm_b = math.sqrt(sum(value * value for value in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _extract_keywords(resume_text: str, job: JobProfile) -> list[str]:
        lowered = resume_text.lower()
        return [skill for skill in job.skills if skill.lower() in lowered]

    def retrieve(self, resume_text: str, top_k: int = 3) -> list[tuple[JobProfile, float]]:
        cleaned_resume = self.normalize_text(resume_text)
        scored = [(job, self._cosine(cleaned_resume, job.document)) for job in self.jobs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]

    def generate_match_report(self, resume_text: str, top_k: int = 3) -> dict:
        candidates = self.retrieve(resume_text, top_k=top_k)
        report = []
        for job, score in candidates:
            matched_skills = self._extract_keywords(resume_text, job)
            report.append(
                {
                    "job_title": job.title,
                    "score": round(score, 4),
                    "matched_skills": matched_skills,
                    "reason": (
                        f"检索到该岗位与简历在能力描述上语义相近，"
                        f"并命中技能关键词：{', '.join(matched_skills) if matched_skills else '无明显命中'}。"
                    ),
                }
            )
        return {
            "summary": "基于简历内容检索岗位知识库并生成匹配建议。",
            "top_matches": report,
        }


def parse_uploaded_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return content.decode("utf-8", errors="ignore")
    raise ValueError("暂仅支持 .txt/.md/.csv 文件，请先转换后上传。")


def merge_text_blocks(blocks: Iterable[str]) -> str:
    return "\n".join([block for block in blocks if block])
