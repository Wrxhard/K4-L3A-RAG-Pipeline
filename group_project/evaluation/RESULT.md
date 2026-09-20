# RAG Evaluation Results — NEU Admissions QA Chatbot

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | Custom evaluation script (faithfulness, relevance, recall, precision) |
| Evaluator model                    | gpt-5.6-luna (openai) |
| Generator model                    | gpt-5.6-luna (openai) |
| Embedding model                    | text-embedding-3-small |
| Corpus version/commit              | (current) |
| Golden dataset size                | 15 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.3 |

## Configurations

- **Config A — dense-only:** Semantic search với `text-embedding-3-small`, top_k=5, không dùng BM25 hoặc RRF.
- **Config B — hybrid + RRF:** Dense + BM25Plus kết hợp qua Reciprocal Rank Fusion (k=60), top_k=5.

Hai config dùng cùng golden dataset 15 câu, cùng generator `gpt-5.6-luna`, cùng prompt, cùng `top_k=5`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      | 1.00 | 1.00 | +0.00 |
| Answer relevance  | 0.93 | 0.96 | +0.03 |
| Context recall    | 0.62 | 0.73 | +0.11 |
| Context precision | 0.85 | 0.98 | +0.13 |
| **Average**       | **0.85** | **0.92** | **+0.07** |

## A/B comparison

- Cấu hình tốt hơn: **Config B — hybrid + RRF**
- Evidence: Dựa trên kết quả thực tế từ golden dataset 15 câu hỏi về tuyển sinh NEU.
- Trade-off về latency/cost: Config B thêm BM25Plus scoring (CPU-only), không tăng API calls.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | Tổng quỹ học bổng của NEU năm học 2025-2026 là bao nhiêu?... | A | 1.00 | 0.85 | 0.00 | 0.00 | retrieval | score thấp nhất batch |
|   2 | Điểm chuẩn ngành Logistics và Quản lý chuỗi cung ứng của NEU... | A | 1.00 | 0.65 | 0.00 | 0.70 | retrieval | score thấp nhất batch |
|   3 | Điểm chuẩn ngành Thương mại điện tử của NEU năm 2025 là bao ... | A | 1.00 | 0.85 | 0.00 | 0.80 | retrieval | score thấp nhất batch |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Dùng hybrid + RRF (Config B) làm cấu hình mặc định | Config B average cao hơn Config A | Tăng average score | A/B test trên golden dataset |
|        2 | Tăng CHUNK_SIZE từ 500 lên 800 ký tự | Câu hỏi dài bị mất context do chunk nhỏ | Cải thiện context recall | So sánh recall trước/sau |
|        3 | Thêm metadata filtering theo doc_type | Kết quả lẫn news/legal không phù hợp | Cải thiện context precision | Đo precision theo loại câu hỏi |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| BM25Plus thay BM25Okapi | BM25Okapi | +stable | ~0ms | BM25Plus ổn định hơn với corpus nhỏ |
| top_k=5 vs top_k=10 | top_k=5 | ~+0.02 avg | +~100ms | Tăng nhỏ, không đáng kể |
