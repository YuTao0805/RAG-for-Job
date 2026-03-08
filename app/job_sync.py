from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


@dataclass
class CrawlSource:
    name: str
    url: str


@dataclass
class CrawledJob:
    company: str
    title: str
    url: str
    summary: str
    crawled_at: str


class _AnchorParser(HTMLParser):
    """提取 HTML 中与招聘相关的锚文本。"""

    def __init__(self) -> None:
        super().__init__()
        self._in_anchor = False
        self._current_href = ""
        self._current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        self._in_anchor = True
        self._current_text = []
        attrs_dict = dict(attrs)
        self._current_href = attrs_dict.get("href") or ""

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._in_anchor:
            return
        text = re.sub(r"\s+", " ", "".join(self._current_text)).strip()
        if text:
            self.links.append((self._current_href, text))
        self._in_anchor = False
        self._current_text = []
        self._current_href = ""


class WeeklyJobSyncService:
    """每周抓取招聘页面并合并到本地知识库。"""

    DEFAULT_SOURCES = [
        CrawlSource("腾讯", "https://careers.tencent.com/search.html?query=工程师"),
        CrawlSource("阿里巴巴", "https://talent.alibaba.com/off-campus/position-list?keyword=工程师"),
        CrawlSource("字节跳动", "https://jobs.bytedance.com/society/position?keywords=工程师"),
    ]

    def __init__(
        self,
        knowledge_base_path: str | Path,
        *,
        snapshot_path: str | Path | None = None,
        interval_days: int = 7,
        sources: list[CrawlSource] | None = None,
        fetcher: Callable[[str], str] | None = None,
    ) -> None:
        self.knowledge_base_path = Path(knowledge_base_path)
        self.snapshot_path = Path(snapshot_path or self.knowledge_base_path.parent / "crawled_jobs.json")
        self.interval_seconds = interval_days * 24 * 60 * 60
        self.sources = sources or self.DEFAULT_SOURCES
        self._fetcher = fetcher or self._fetch_html

    @staticmethod
    def _fetch_html(url: str) -> str:
        request = Request(url, headers={"User-Agent": "RAG-for-Job/1.0"})
        with urlopen(request, timeout=15) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="ignore")

    @staticmethod
    def _infer_skills(text: str) -> list[str]:
        skill_aliases = {
            "python": ["python"],
            "java": ["java"],
            "sql": ["sql", "mysql", "postgresql"],
            "前端": ["javascript", "typescript", "react", "vue"],
            "后端": ["后端", "服务端", "backend"],
            "算法": ["算法", "机器学习", "深度学习", "llm"],
            "数据分析": ["数据分析", "可视化", "bi"],
        }
        lowered = text.lower()
        skills = [name for name, aliases in skill_aliases.items() if any(alias in lowered for alias in aliases)]
        return skills or ["通用能力"]

    @staticmethod
    def _relevant(title: str) -> bool:
        return bool(re.search(r"工程师|开发|算法|数据|产品|前端|后端|测试", title, flags=re.IGNORECASE))

    def crawl_once(self) -> list[CrawledJob]:
        jobs: list[CrawledJob] = []
        now = datetime.now(timezone.utc).isoformat()

        for source in self.sources:
            try:
                html = self._fetcher(source.url)
            except URLError as exc:
                logger.warning("抓取 %s 失败: %s", source.name, exc)
                continue
            except Exception as exc:  # noqa: BLE001
                logger.warning("抓取 %s 发生异常: %s", source.name, exc)
                continue

            parser = _AnchorParser()
            parser.feed(html)

            for href, text in parser.links:
                if not self._relevant(text):
                    continue
                jobs.append(
                    CrawledJob(
                        company=source.name,
                        title=text,
                        url=href if href.startswith("http") else source.url,
                        summary=f"来自{source.name}招聘页的岗位：{text}",
                        crawled_at=now,
                    )
                )

        dedup: dict[tuple[str, str], CrawledJob] = {}
        for job in jobs:
            key = (job.company, job.title)
            dedup[key] = job
        return list(dedup.values())

    def _load_json(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: list[dict]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _merge_into_knowledge_base(self, jobs: list[CrawledJob]) -> int:
        kb = self._load_json(self.knowledge_base_path)
        existing_titles = {item.get("title", "") for item in kb}
        inserted = 0

        for job in jobs:
            normalized_title = f"{job.company}-{job.title}"[:80]
            if normalized_title in existing_titles:
                continue
            kb.append(
                {
                    "title": normalized_title,
                    "description": job.summary,
                    "skills": self._infer_skills(f"{job.title} {job.summary}"),
                }
            )
            inserted += 1

        if inserted:
            self._write_json(self.knowledge_base_path, kb)
        return inserted

    def run_sync(self) -> dict[str, int]:
        jobs = self.crawl_once()
        inserted = self._merge_into_knowledge_base(jobs)

        snapshots = self._load_json(self.snapshot_path)
        snapshots.extend([job.__dict__ for job in jobs])
        self._write_json(self.snapshot_path, snapshots)

        return {"crawled": len(jobs), "inserted": inserted}

    async def run_forever(self) -> None:
        while True:
            result = self.run_sync()
            logger.info("招聘信息同步完成: %s", result)
            await asyncio.sleep(self.interval_seconds)
