# RAG-for-Job

一个基于 **RAG（检索增强生成）** 的职业匹配示例服务：
- 上传简历文本文件（`.txt/.md/.csv`）
- 系统从岗位知识库中检索最相关岗位
- 生成匹配结果与命中技能说明

## 项目结构

```text
.
├── app/
│   ├── main.py           # FastAPI 接口
│   └── rag_matcher.py    # RAG 检索+生成逻辑
├── data/
│   └── job_profiles.json # 岗位知识库
├── tests/
│   └── test_rag_matcher.py
└── requirements.txt
```

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 调用示例

```bash
curl -X POST 'http://127.0.0.1:8000/match-job?top_k=3' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@resume.txt;type=text/plain'
```

返回示例（节选）：

```json
{
  "filename": "resume.txt",
  "result": {
    "summary": "基于简历内容检索岗位知识库并生成匹配建议。",
    "top_matches": [
      {
        "job_title": "数据分析师",
        "score": 0.61,
        "matched_skills": ["python", "sql"],
        "reason": "检索到该岗位与简历在能力描述上语义相近，并命中技能关键词：python, sql。"
      }
    ]
  }
}
```

## 测试

```bash
python -m unittest discover -s tests -q
```
