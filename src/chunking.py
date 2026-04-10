from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker: #Nhận diện và cắt câu dựa trên dấu câu
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text: return []
        parts = re.split(r'(\. |\! |\? |\.\n)', text)
        sentences = []
        for i in range(0, len(parts), 2):
            s = parts[i]
            if i + 1 < len(parts):
                s += parts[i+1]
            s = s.strip()
            if s:
                sentences.append(s)
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i:i + self.max_sentences_per_chunk]
            chunks.append(" ".join(chunk_sentences).strip())
        return chunks


class RecursiveChunker: #Chia nhỏ đoạn văn bản thỏa mãn kích thước chunk dựa trên thứ tự separator
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(self.separators) == 0:
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(text)
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(current_text)
        
        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]
        
        if sep == "":
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(current_text)
            
        parts = current_text.split(sep)
        chunks = []
        current_chunk = ""
        
        for part in parts:
            if current_chunk:
                attempt = current_chunk + sep + part
            else:
                attempt = part
                
            if len(attempt) <= self.chunk_size:
                current_chunk = attempt
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = part
        
        if current_chunk:
            chunks.append(current_chunk)
            
        final_chunks = []
        for c in chunks:
            if len(c) > self.chunk_size:
                final_chunks.extend(self._split(c, next_seps))
            else:
                final_chunks.append(c)
        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator: #Khởi tạo 3 phương pháp và tổng kết 
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        results = {}
        
        fc = FixedSizeChunker(chunk_size=chunk_size)
        fc_chunks = fc.chunk(text)
        results['fixed_size'] = {
            'count': len(fc_chunks),
            'avg_length': sum(len(c) for c in fc_chunks) / max(1, len(fc_chunks)),
            'chunks': fc_chunks
        }
        
        sc = SentenceChunker(max_sentences_per_chunk=3)
        sc_chunks = sc.chunk(text)
        results['by_sentences'] = {
            'count': len(sc_chunks),
            'avg_length': sum(len(c) for c in sc_chunks) / max(1, len(sc_chunks)),
            'chunks': sc_chunks
        }
        
        rc = RecursiveChunker(chunk_size=chunk_size)
        rc_chunks = rc.chunk(text)
        results['recursive'] = {
            'count': len(rc_chunks),
            'avg_length': sum(len(c) for c in rc_chunks) / max(1, len(rc_chunks)),
            'chunks': rc_chunks
        }
        
        return results
