# RAG-for-Job
Multimodal Document RAG：简历生成 + JD 对接 + 面试题/笔试题
├── README.md
├── requirements.txt
├── .env.example
├── configs/
│   ├── default.yaml
│   └── model.yaml
├── data/
│   ├── raw/                # 上传的PDF/图片
│   ├── parsed/             # 解析后的统一schema JSONL
│   ├── indexes/            # faiss/chroma等索引
│   └── eval/               # 测试集与评测结果
├── src/
│   ├── ingest/
│   │   ├── pdf_text.py      # PDF文字抽取
│   │   ├── pdf_images.py    # PDF分页截图+区域切块（可先整页）
│   │   ├── vlm_caption.py   # VLM对图片块做OCR/caption/结构化摘要
│   │   └── schema.py        # 统一chunk schema定义
│   ├── index/
│   │   ├── embed.py         # embedding
│   │   ├── bm25.py          # BM25（可选）
│   │   ├── vector_store.py  # faiss/chroma封装
│   │   └── hybrid.py        # hybrid召回逻辑
│   ├── rag/
│   │   ├── retrieve.py
│   │   ├── rerank.py        # 可选：cross-encoder/llm rerank
│   │   ├── prompt.py        # prompt模板加载
│   │   └── generate.py
│   ├── features/
│   │   ├── resume_builder.py     # 简历生成/改写
│   │   ├── jd_matcher.py         # JD画像提取+匹配度+gap
│   │   └── interview_kit.py      # 面试题/笔试题生成
│   ├── eval/
│   │   ├── citation_metrics.py   # 引用正确率/覆盖率
│   │   ├── keyword_coverage.py   # JD关键词覆盖率
│   │   └── regression.py         # 回归测试
│   └── app/
│       ├── api.py           # FastAPI (可选)
│       └── ui.py            # Gradio/Streamlit
└── scripts/
    ├── 01_ingest.py
    ├── 02_build_index.py
    ├── 03_demo_resume.py
    ├── 04_demo_jd_match.py
    ├── 05_demo_interview.py
    └── 06_eval.py
