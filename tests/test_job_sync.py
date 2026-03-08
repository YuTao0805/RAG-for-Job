import json
import tempfile
import unittest
from pathlib import Path

from app.job_sync import CrawlSource, WeeklyJobSyncService


class TestWeeklyJobSyncService(unittest.TestCase):
    def test_run_sync_should_crawl_and_merge_into_knowledge_base(self) -> None:
        html = """
        <html><body>
          <a href='https://example.com/job1'>后端开发工程师</a>
          <a href='https://example.com/job2'>算法工程师</a>
          <a href='https://example.com/about'>关于我们</a>
        </body></html>
        """

        with tempfile.TemporaryDirectory() as tmp:
            kb_path = Path(tmp) / "job_profiles.json"
            snapshot_path = Path(tmp) / "crawled_jobs.json"
            kb_path.write_text("[]", encoding="utf-8")

            service = WeeklyJobSyncService(
                kb_path,
                snapshot_path=snapshot_path,
                sources=[CrawlSource("示例公司", "https://example.com/careers")],
                fetcher=lambda _: html,
            )

            result = service.run_sync()

            self.assertEqual(result["crawled"], 2)
            self.assertEqual(result["inserted"], 2)

            kb_payload = json.loads(kb_path.read_text(encoding="utf-8"))
            self.assertEqual(len(kb_payload), 2)
            self.assertTrue(any(item["title"].startswith("示例公司-") for item in kb_payload))

            snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(len(snapshot_payload), 2)


if __name__ == "__main__":
    unittest.main()
