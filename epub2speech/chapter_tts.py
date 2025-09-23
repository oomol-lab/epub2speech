import uuid
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from spacy.lang.xx import MultiLanguage
from spacy.language import Language

from .tts import TextToSpeechProtocol


class ChapterTTS:
    """Convert chapter text to speech using sentence-by-sentence processing"""

    def __init__(
        self,
        tts_protocol: TextToSpeechProtocol,
        sample_rate: int = 24000,
        max_sentence_length: int = 500,
        language_model: Optional[str] = None
    ):
        """
        Initialize Chapter TTS processor

        Args:
            tts_protocol: TTS protocol instance for audio generation
            sample_rate: Audio sample rate in Hz
            max_sentence_length: Maximum characters per sentence
            language_model: spaCy language model to use (default: xx_ent_wiki_sm)
        """
        self.tts_protocol = tts_protocol
        self.sample_rate = sample_rate
        self.max_sentence_length = max_sentence_length
        self._nlp = self._load_language_model(language_model)

    def _load_language_model(self, language_model: Optional[str]) -> Language:
        """Load spaCy language model"""
        if language_model:
            try:
                import spacy
                return spacy.load(language_model)
            except OSError:
                pass  # Model not found, fall back to built-in sentencizer

        # Fallback to built-in sentencizer
        nlp: Language = MultiLanguage()
        nlp.add_pipe("sentencizer")
        return nlp

    def process_chapter(
        self,
        text: str,
        output_path: Path,
        temp_dir: Path,
        voice: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Process a chapter of text and convert to speech

        Args:
            text: Chapter text content
            output_path: Path to save the audio file
            temp_dir: Directory for temporary audio files
            voice: Voice to use for TTS
            progress_callback: Optional callback for progress updates (current, total)

        Returns:
            True if successful, False otherwise
        """
        # Ensure temp directory exists
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Process text into sentences
        sentences = self.split_text_into_sentences(text)
        if not sentences:
            return False

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate audio for each sentence
        audio_segments = []
        temp_files_created = []  # Track temp files for cleanup

        try:
            for i, sentence in enumerate(sentences):
                if progress_callback:
                    progress_callback(i + 1, len(sentences))

                # Generate temporary audio file with UUID prefix
                session_id = str(uuid.uuid4())[:8]  # Short UUID for filename
                temp_audio_path = temp_dir / f"{session_id}_sentence_{i:04d}.wav"
                temp_files_created.append(temp_audio_path)

                success = self.tts_protocol.convert_text_to_audio(
                    text=sentence,
                    output_path=temp_audio_path,
                    voice=voice
                )

                if success and temp_audio_path.exists():
                    # Load audio data
                    audio_data: np.ndarray
                    sr: int
                    audio_data, sr = sf.read(temp_audio_path)
                    if sr != self.sample_rate:
                        # Handle sample rate mismatch if needed
                        pass
                    audio_segments.append(audio_data)
                else:
                    # Continue with next sentence instead of failing completely
                    continue

            if not audio_segments:
                return False

            # Concatenate all audio segments
            final_audio = np.concatenate(audio_segments)

            # Save final audio file
            sf.write(output_path, final_audio, self.sample_rate)
            return True

        finally:
            # Clean up temporary files
            for temp_file in temp_files_created:
                if temp_file.exists():
                    temp_file.unlink()

    def split_text_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy with CJK punctuation support"""
        # Clean text
        text = text.strip()
        if not text:
            return []

        # First, split on CJK sentence-ending punctuation
        cjk_sentences = self._split_cjk_sentences(text)

        # Then process each sentence with spaCy for further splitting
        all_sentences = []
        for sentence in cjk_sentences:
            if not sentence.strip():
                continue

            # Process with spaCy
            doc = self._nlp(sentence)

            for sent in doc.sents:
                sentence_text = sent.text.strip()
                if len(sentence_text) > self.max_sentence_length:
                    # Split long sentences at punctuation
                    sub_sentences = self._split_long_sentence(sentence_text)
                    all_sentences.extend(sub_sentences)
                else:
                    all_sentences.append(sentence_text)

        # Filter out empty sentences, but keep very short ones (even single words)
        sentences = [s for s in all_sentences if s.strip()]

        return sentences

    def _split_cjk_sentences(self, text: str) -> List[str]:
        """Split text on CJK sentence-ending punctuation and major clause separators"""
        # CJK sentence-ending punctuation (highest priority)
        cjk_endings = [
            "。",  # Chinese/Japanese period
            "！",  # Chinese/Japanese exclamation
            "？",  # Chinese/Japanese question
            ".",   # Western period
            "!",   # Western exclamation
            "?",   # Western question
        ]

        # Major clause separators (lower priority, only split if sentence is still long)
        clause_separators = [
            "；",  # Chinese semicolon
            "：",  # Chinese colon
            "，",  # Chinese comma
            "；",  # Chinese semicolon
            ":",   # Western colon
            ";",   # Western semicolon
            ",",   # Western comma (for very long sentences)
        ]

        def split_on_chars(text: str, split_chars: List[str]) -> List[str]:
            """Split text on specific characters"""
            sentences = []
            current_sentence = ""

            for char in text:
                current_sentence += char
                if char in split_chars:
                    # Found split point, add current sentence
                    if current_sentence.strip():
                        sentences.append(current_sentence.strip())
                    current_sentence = ""

            # Add any remaining text
            if current_sentence.strip():
                sentences.append(current_sentence.strip())

            # If no split points found, return original text
            if not sentences:
                return [text]

            return sentences

        # First split on sentence endings
        sentences = split_on_chars(text, cjk_endings)

        # For each resulting sentence, if it's still very long, split on clause separators
        final_sentences = []
        for sentence in sentences:
            if len(sentence) > self.max_sentence_length // 2:  # If longer than half max length
                clause_parts = split_on_chars(sentence, clause_separators)
                final_sentences.extend(clause_parts)
            else:
                final_sentences.append(sentence)

        return final_sentences

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split a long sentence at punctuation marks - supports CJK languages"""
        # Split at common punctuation (tuple for immutability and performance)
        split_points = (
            # Western punctuation
            ",", ";", ":",
            # Em dashes and en dashes
            "—", "–", "-",
            # Chinese punctuation
            "，", "；", "：", "、", "——",
            # Japanese punctuation
            "、", "。", "，", "；", "：",
            # Korean punctuation
            "，", "；", "：", "、",
            # Other useful separators
            "（", "）", "【", "】", "《", "》", "〈", "〉"
        )

        for punct in split_points:
            if punct in sentence:
                parts = sentence.split(punct)
                result = []
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part:
                        # Add punctuation back except for last part
                        if i < len(parts) - 1:
                            part += punct
                        result.append(part)
                return result

        # If no punctuation found, split by length
        words = sentence.split()
        mid_point = len(words) // 2

        first_half = " ".join(words[:mid_point])
        second_half = " ".join(words[mid_point:])

        return [first_half, second_half]

    def get_chapter_info(self, text: str) -> Dict[str, Any]:
        """Get information about a chapter"""
        sentences = self.split_text_into_sentences(text)

        return {
            "total_characters": len(text),
            "total_sentences": len(sentences),
            "average_sentence_length": sum(len(s) for s in sentences) / len(sentences) if sentences else 0,
            "longest_sentence": max(sentences, key=len) if sentences else "",
            "sample_sentences": sentences[:3] if len(sentences) > 3 else sentences
        }