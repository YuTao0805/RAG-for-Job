import unittest
from pathlib import Path

from app.rag_matcher import JobMatcherRAG, parse_uploaded_text


class TestRagMatcher(unittest.TestCase):
    def test_retrieve_should_return_ranked_jobs(self) -> None:
        matcher = JobMatcherRAG(Path("data/job_profiles.json"))
        resume = "熟悉Python、SQL和数据可视化，做过业务分析看板。"
        report = matcher.generate_match_report(resume, top_k=2)

        self.assertEqual(len(report["top_matches"]), 2)
        self.assertIn(report["top_matches"][0]["job_title"], {"数据分析师", "后端开发工程师"})

    def test_parse_uploaded_text_supports_txt(self) -> None:
        content = "Python developer".encode("utf-8")
        text = parse_uploaded_text("resume.txt", content)
        self.assertIn("Python", text)


if __name__ == "__main__":
    unittest.main()
