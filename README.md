# RAG-for-Job
Multimodal Document RAG：简历生成 + JD 对接 + 面试题/笔试题

安装依赖
上传文件到 data/raw/（你的 CV、论文 PDF、证书图片都行）

依次运行：

python scripts/01_ingest.py

python scripts/02_build_index.py

python scripts/03_demo_resume.py --role "Multimodal RAG Engineer"

python scripts/04_demo_jd_match.py --jd_file data/raw/jd.txt

python scripts/05_demo_interview.py --jd_file data/raw/jd.txt

python scripts/06_eval.py

输出：

outputs/resume_en.md outputs/resume_zh.md

outputs/jd_report.json

outputs/interview_kit.md

data/eval/report.json
