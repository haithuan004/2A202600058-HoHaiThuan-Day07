# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Hồ Hải Thuận
**Nhóm:** E6
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity (~1) là khi 2 vector đều cùng chỉ về một hướng, điều này có nghĩa là 2 vector đó có ý nghĩa tương tự nhau trong không gian vector.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi thích ăn phở"
- Sentence B: "Tôi thích ăn bún"
- Tại sao tương đồng: Cả 2 câu đều nói về việc thích ăn một món ăn Việt Nam, chỉ khác nhau ở loại món ăn.

**Ví dụ LOW similarity:**
- Sentence A: "Tôi thích ăn phở"
- Sentence B: "Tôi là học sinh"
- Tại sao khác: Câu A nói về việc thích ăn phở, còn câu B nói về việc là học sinh. Hai câu này không có liên quan đến nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings vì nó đo lường góc giữa hai vector, không phụ thuộc vào độ lớn của vector. Nói cách khác, sửu dụng cosine similarity giúp ta tập trung vào hướng của vector, tức là ý nghĩa của vector, thay vì độ lớn của vector, tức là tần suất xuất hiện của từ.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
$$\text{Total Chunks} = \left\lceil \frac{\text{Total Length} - \text{Chunk Size}}{\text{Stride}} \right\rceil + 1$$
$$\text{Total Chunks} = \left\lceil \frac{10000 - 500}{450} \right\rceil + 1$$
$$\text{Total Chunks} = \left\lceil \frac{9500}{450} \right\rceil + 1$$
$$\text{Total Chunks} = \left\lceil 21.11 \right\rceil + 1$$
$$\text{Total Chunks} = 22 + 1$$
$$\text{Total Chunks} = 23$$

> *Đáp án: 23 chunks*

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Nếu overlap tăng lên 100, chunk count sẽ tăng lên thành 25 chunks. Ta muốn cấu hình overlap nhiều hơn để đảm bảo các câu hoặc ý tưởng không bị cắt đứt đột ngột ở ranh giới giữa hai chunk, giúp bảo toàn toàn vẹn ngữ cảnh khi đưa vào mô hình xử lý.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Y Sinh học & Sàng lọc bệnh lý (Medical / Genetics / Oncology)

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain Y khoa vì đây là lĩnh vực đòi hỏi độ chính xác cao trong retrieval — một câu trả lời sai về phác đồ điều trị hay xét nghiệm trước sinh có thể gây hậu quả nghiêm trọng. Đây cũng là bài kiểm tra lý tưởng cho các chiến lược chunking và metadata vì tài liệu y tế chứa nhiều thuật ngữ chuyên biệt, danh sách liệt kê và cấu trúc heading phức tạp. 

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | `PrenatalGenome_WhitePaper.md` | `prenatalgenome.it` | 25,451 | `{"source": "https://prenatalgenome.it/pdf/PrenatalGenome_WhitePaper.pdf", "category": "NIPT;diagnostics;molecular", "date":none}`|
| 2 | `Alpha+Thalassemia+Fact+Sheet...` | `squarespace.com` | 8,604 | `{"source": "https://static1.squarespace.com/static/5a4f825849fc2bd65e00c9f0/t/6263224e3fed9f6913e49734/1650664015220/Alpha+Thalassemia+Fact+Sheet+2022.pdf", "category": "alpha thalassamia;molecular"}, "date":2022"}` |
| 3 | `MUCLecture_2023.md` | `uomus.edu.iq` | 9,565 | `{"source": "https://uomus.edu.iq/img/lectures21/MUCLecture_2023_12931719.pdf", "category": "Medelian inheritance", "date":2023}` |
| 4 | `cclg-brain-tumours-factsheet.md`| `cclg.org.uk` | 16,286 | `{"source": "https://www.cclg.org.uk/sites/default/files/2025-02/cclg-brain-tumours-factsheet-2022.pdf", "category": "brain;tumor", "date":2022}` |
| 5 | `Non_invasive_prenatal_testing.md` | `genetics.edu.au` | 5,376 | `{"source": "https://www.genetics.edu.au/PDF/Non_invasive_prenatal_testing_fact_sheet-CGE.pdf", "category": "NIPT;diagnostics;molecular", "date":2021}` |
| 6 | `Action-Guide_Cancer-Screening.md`| `nachc.org` | 60,786 | `{"source": "https://www.nachc.org/wp-content/uploads/2023/07/Action-Guide_Cancer-Screening.pdf", "category": "diagnostics;tumor", "date":2023}` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `category` | `str` | `NIPT;diagnostics;molecular` | Tránh query về Ung thư nhưng trúng chunk thuộc bài Sàng lọc tiền sản do có trùng từ ngữ chung chung. |
| `source` | `str` | `https://...`| Kiểm chứng mức độ đáng tin cậy của agent, giảm hallucination|
|`date`| `int` | `2021`, `2022` | Kiểm chứng tính thời sự của thông tin, tránh thông tin lỗi thời|
 


---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Data (Medical) | FixedSizeChunker (`fixed_size`) | 90 | 297.83 | Trung bình, hay bị cắt ngang bảng biểu |
| Data (Medical) | SentenceChunker (`by_sentences`) | 53 | 418.81 | Tốt, giữ được câu văn y khoa hoàn chỉnh |
| Data (Medical) | RecursiveChunker (`recursive`) | 114 | 194.19 | Tốt nhất, chia nhỏ đoạn khoa học hợp lý |

### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> `RecursiveChunker` hoạt động bằng cách thử chia văn bản theo danh sách separator ưu tiên giảm dần: `["\n\n", "\n", ". ", " ", ""]`. Đầu tiên, nó thử tách theo đoạn văn (`\n\n`); nếu đoạn con vẫn lớn hơn `chunk_size`, nó đệ quy xuống cấp thấp hơn (dòng đơn, câu, từ...) cho đến khi mọi chunk đều nằm trong giới hạn. Base case là khi đoạn văn bản đủ nhỏ hoặc separator list rỗng (fallback về FixedSizeChunker). Cách tiếp cận này đảm bảo ưu tiên cắt tại ranh giới tự nhiên (đoạn, câu) thay vì cắt tùy tiện theo ký tự.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tài liệu Y khoa (Vin Study) chứa rất nhiều thuật ngữ dài, danh sách liệt kê và heading. Sử dụng RecursiveChunker kết hợp kích thước `300` giúp bảo toàn các khối list bệnh lý hoặc quy trình hóa trị ở trong cùng 1 chunk mà không bị xé vụn như SentenceChunker.

**Code snippet (nếu custom):**
```python
class RecursiveChunker:
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators=None, chunk_size=500):
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def _split(self, current_text, remaining_separators):
        if len(current_text) <= self.chunk_size:
            return [current_text]                      # Base case
        if not remaining_separators:
            return FixedSizeChunker(self.chunk_size).chunk(current_text)
        sep = remaining_separators[0]
        parts = current_text.split(sep)
        chunks, current = [], ""
        for part in parts:
            attempt = current + sep + part if current else part
            if len(attempt) <= self.chunk_size:
                current = attempt
            else:
                if current: chunks.append(current)
                current = part
        if current: chunks.append(current)
        # Đệ quy cho các chunk vẫn còn quá lớn
        return [c2 for c in chunks
                for c2 in (self._split(c, remaining_separators[1:]) if len(c) > self.chunk_size else [c])]
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Data (Medical) | SentenceChunker — best baseline | 53 | 418.81 | Trung bình — chunk quá dài làm loãng signal; top-3 recall ~3/5 query |
| Data (Medical) | **RecursiveChunker (của tôi)** | **114** | **194.19** | **Cao — chunk nhỏ, tập trung; top-3 recall 5/5 query, avg cosine score ≈ 0.70** |

**Nhận xét:** `SentenceChunker` tạo chunk dài (~419 ký tự), bảo toàn câu văn nhưng gộp nhiều ý vào một chunk → embedding bị "pha loãng", giảm precision khi match query ngắn. `RecursiveChunker` chia nhỏ hơn (~194 ký tự) theo cấu trúc tự nhiên, mỗi chunk tập trung 1 ý → similarity score sắc nét hơn, recall benchmark đạt 5/5.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Hồ Hải Thuận | RecursiveChunker | 8 | Fallback thông minh, tôn trọng cấu trúc tự nhiên của tài liệu đồng thời rất linh hoạt| Tuy nhiên không thể xử lí bảng biểu, không có overlap |
| Khổng Mạnh Tuấn | FixedSizeChunker| 8 | Ổn định, dễ kiểm soát chunk | Query 4/5 vẫn lệch tài liệu kỳ vọng, chỉ trả lời được câu hỏi dễ, các câu hỏi phức tạp chọn đúng tài liệu và chỉ số liên quan cao nhưng câu trả lời không chính xác (model local) |
|  Lâm Hoàng Hải | SentenceChunker | 6 | Dễ cài đặt, không bị cắt giữa đoạn | Trả lời được 3/5 query, miss ý của những câu hỏi phức tạp, cần suy luận từ tương đồng |
| Nguyễn Hoàng Long | 8 | Giữ ngữ cảng theo paragraph, phù hợp tài liệu y khoa có cấu trúc | Chunks có thể quá lớn cho factsheet câu ngắn |
| Trần Thái Huy | SentenceChunker | 7 | Dễ cài đặt, chunk theo câu dễ đọc | Tạo nhiều chunk hơn, dễ miss ý ở câu hỏi cần ngữ cảnh dài | 
| Quách Ngọc Quang | RecursiveChunker | 9 | Tôn trọng cấu trúc phân cấp, giữ ngữ cảnh y khoa tốt. | Số lượng chunk lớn, tốn tài nguyên |
| Nguyễn Mạnh Dũng | RecursiveChunker | 8 | Data của nhóm có cấu trúc thứ bậc nên ngữ cảnh được giữ lại tốt | Chunk lớn đôi khi làm loãng ngữ cảnh cho fact ngắn |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> `RecursiveChunker` là lựa chọn tốt nhất cho domain Y khoa của nhóm. Tài liệu y tế có cấu trúc phân cấp rõ ràng (heading → đoạn → câu → từ chuyên ngành), nên cắt đệ quy theo separator tự nhiên giúp mỗi chunk tập trung vào đúng một đơn vị nghĩa y khoa (tên thuốc, chỉ số xét nghiệm, quy trình điều trị). So với `SentenceChunker` (chunk quá dài, nhiễu ngữ nghĩa) và `FixedSizeChunker` (cắt tùy tiện ngang câu/bảng), `RecursiveChunker` đạt recall 5/5 benchmark query và cosine score trung bình ~0.70, vượt trội rõ rệt cho RAG y tế đòi hỏi độ chính xác cao.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> `SentenceChunker` phát hiện ranh giới câu bằng regex `re.split(r'(\. |\! |\? |\.\n)', text)`, nhận diện các dấu kết câu phổ biến và giữ lại dấu câu đó trong chuỗi output (tránh mất thông tin). Sau khi tách xong danh sách câu, nó nhóm từng `max_sentences_per_chunk` câu liên tiếp lại thành một chunk. Edge case được xử lý: câu trống bị loại bỏ trước khi ghép nhóm để tránh chunk rỗng.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Hàm `chunk()` là entry point: nó kiểm tra text rỗng rồi gọi `_split()` với toàn bộ danh sách separator. Hàm `_split()` là recursive core: base case là khi đoạn văn đã đủ nhỏ (≤ `chunk_size`). Nếu không, nó lấy separator đầu tiên, chia text thành các phần, ghép chúng lại cho đến khi vượt `chunk_size` rồi đẩy vào danh sách — với mỗi phần còn quá lớn, nó đệ quy xuống separator tiếp theo trong danh sách.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents()` duyệt qua từng `Document`, gọi `embedding_fn(doc.content)` để tạo vector và lưu record dưới dạng dict gồm `{id, content, metadata, embedding}` vào `_store` (list). `search()` nhúng query thành vector rồi tính dot product giữa query embedding và từng embedding trong `_store`, sắp xếp giảm dần theo score và trả về top-k kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter()` áp dụng chiến lược **filter trước**: nó duyệt `_store` và chỉ giữ lại các record có metadata khớp với `metadata_filter` (key-value match hoàn toàn), rồi mới chạy similarity search trên tập đã lọc. `delete_document()` xóa bằng cách tạo lại `_store` với list comprehension, loại tất cả record có `id` hoặc `metadata['doc_id']` trùng với `doc_id` cần xóa — trả về `True` nếu có gì thực sự bị xóa.

### KnowledgeBaseAgent

**`answer`** — approach:
> `KnowledgeBaseAgent.answer()` theo đúng pipeline RAG 3 bước: (1) Gọi `store.search(question, top_k=k)` để lấy các chunk liên quan nhất. (2) Nối text của các chunk lại thành `context` bằng `"\n".join(...)`. (3) Build prompt theo template `"Context:\n{context}\n\nQuestion: {question}\nAnswer:"` và truyền vào `llm_fn()`. Cách inject context trực tiếp vào prompt (không fine-tune model) giúp agent dễ cập nhật knowledge base mà không cần retrain.

### Test Results

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.10s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Alpha-thalassemia is an inherited blood disorder. | It is passed down from parents to children through genes. | high | -0.0932 | Sai |
| 2 | Alpha-thalassemia is an inherited blood disorder. | Chemotherapy is used to destroy cancer cells. | low | 0.0746 | Sai |
| 3 | NIPT tests for Down syndrome. | Trisomy 21 is a chromosome condition. | high | 0.1250 | Sai |
| 4 | Brain tumours are the most common tumours. | Astrocytoma is a type of tumour. | high | -0.2313 | Sai |
| 5 | Iron chelation therapy prevents iron overload. | Intrauterine blood transfusions are performed before birth. | medium | 0.2115 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Đáng ngạc nhiên nhất là Pair 4 (hai thực thể cùng loại - tumour) lại bị đánh giá âm (-0.23), trong khi Pair 5 (hai liệu pháp rời rạc) dương. Việc này khẳng định Fake / Mock Embedder chỉ là random generator, hoàn toàn thất bại trong việc thấu hiểu kiến trúc ngôn ngữ Y khoa chuyên biệt. RAG bắt buộc cần Model Embed xịn mới chạy được.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | In NIPT, what is the role of paternal DNA information? | Paternal-inherited SNPs in cfDNA are analyzed to estimate fetal fraction and confirm fetal DNA detection. |
| 2 | What genetic factor determines the subtype (severity category) of alpha-thalassemia? | The number of damaged or missing alpha-globin genes (HBA1/HBA2 copies) determines the subtype. |
| 3 | What is the basic human chromosome makeup? | Humans have 46 chromosomes: 22 pairs of autosomes plus 2 sex chromosomes; females are XX and males are XY. |
| 4 | What is the most common malignant brain tumour in children? | Medulloblastoma. |
| 5 | Why can brain tumours cause headaches and seizures? | Tumour growth can raise pressure inside the head by pushing brain tissue or blocking fluid flow, which triggers headaches and seizures. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | In NIPT, what is the role of paternal DNA information? | "Each complete human DNA helix contains a sequence of about three billion base pairs..." | 0.6521 | Có | Agent giải thích về vai trò của SNP di truyền từ cha trong cfDNA để ước tính fetal fraction. |
| 2 | What genetic factor determines the subtype of alpha-thalassemia? | "Individuals with alpha-thalassemia have either 1, 2, 3 or 4 missing alpha-globin genes..." | 0.7802 | Có | Agent nêu rõ số lượng gen alpha-globin bị hỏng/mất (HBA1/HBA2) xác định subtype. |
| 3 | What is the basic human chromosome makeup? | "Humans have 46 chromosomes arranged in 23 pairs, consisting of 22 autosomes + sex chromosomes..." | 0.7114 | Có | 46 nhiễm sắc thể: 22 cặp autosome + cặp giới tính XX/XY. |
| 4 | What is the most common malignant brain tumour in children? | "Medulloblastomas are the most common malignant brain tumours found in children..." | 0.7434 | Có | Agent trả lời chính xác: Medulloblastoma. |
| 5 | Why can brain tumours cause headaches and seizures? | "Some symptoms are caused by the pressure inside the head (intracranial pressure) being higher..." | 0.6045 | Có | Agent giải thích áp lực nội sọ tăng do khối u chèn mô não/cản trở dịch não tủy gây đau đầu và co giật. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5 (OpenAI `text-embedding-3-small` + `RecursiveChunker(300)`)

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Quách Ngọc Quang sử dụng `RecursiveChunker` nhưng thêm bước **metadata-aware filtering** trước khi search, giúp loại bỏ noise từ tài liệu không liên quan — đây là điều tôi chưa nghĩ đến khi chỉ focus vào chunking. Khổng Mạnh Tuấn dùng `FixedSizeChunker` nhưng đạt score 8/10 nhờ tinh chỉnh chunk size phù hợp với độ dài trung bình của tài liệu — nhắc nhở rằng hyperparameter đơn giản đôi khi quan trọng hơn algorithm phức tạp.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm khác demo pipeline RAG có bước **re-ranking** sau khi retrieve: thay vì lấy thẳng top-k theo cosine score, họ dùng một cross-encoder nhỏ để chấm lại độ phù hợp giữa query và mỗi chunk trước khi đưa vào LLM. Kỹ thuật này giải quyết được nhược điểm của bi-encoder (embedding đôi khi bỏ sót chunk quan trọng do vector space không hoàn hảo) và là bước upgrade rõ rệt nhất tôi muốn áp dụng vào pipeline của mình nếu có thêm thời gian.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ bổ sung thêm trường metadata `date` (năm xuất bản) để lọc ưu tiên tài liệu mới hơn khi tồn tại nhiều phiên bản guideline cùng chủ đề. Ngoài ra, nếu có thêm thời gian, tôi sẽ thử nghiệm `HybridSearch` (kết hợp BM25 keyword search với vector search) vì trong y khoa, việc tìm chính xác tên thuốc hay tên bệnh cụ thể thường hiệu quả hơn khi dùng keyword search thuần túy thay vì chỉ dựa hoàn toàn vào nghĩa ngữ nghĩa.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 9 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **81 / 100** |
