# RAG-for-Job

一个基于 **RAG（检索增强生成）** 的职业匹配示例服务：
- 上传简历文本文件（`.txt/.md/.csv`）
- 系统从岗位知识库中检索最相关岗位
- 生成匹配结果与命中技能说明
- 每周自动爬取大厂招聘页面，并将新增岗位汇总到本地知识库

## 项目结构

```text
.
├── app/
│   ├── main.py           # FastAPI 接口
│   ├── rag_matcher.py    # RAG 检索+生成逻辑
│   └── job_sync.py       # 招聘信息抓取与知识库同步
├── data/
│   └── job_profiles.json # 岗位知识库
├── tests/
│   ├── test_rag_matcher.py
│   └── test_job_sync.py
└── requirements.txt
```

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

服务启动后会在后台定期（每隔一周）执行一次招聘信息同步任务。

## 接口说明

### 1) 简历匹配岗位

```bash
curl -X POST 'http://127.0.0.1:8000/match-job?top_k=3' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@resume.txt;type=text/plain'
```

### 2) 手动触发招聘同步

```bash
curl -X POST 'http://127.0.0.1:8000/sync-jobs'
```

返回示例：

```json
{
  "crawled": 10,
  "inserted": 6
}
```

## 测试

```bash
python -m unittest discover -s tests -q
```
