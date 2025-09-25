import uuid
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Optional, Callable, Generator
from spacy.lang.xx import MultiLanguage
from spacy.language import Language
from spacy.tokens import Span

from .tts import TextToSpeechProtocol
from resource_segmentation import split, Resource, Segment

SEGMENT_LEVEL = 1
SENTENCE_LEVEL = 2

class ChapterTTS:
    def __init__(
        self,
        tts_protocol: TextToSpeechProtocol,
        sample_rate: int = 24000,
        max_segment_length: int = 500,
        language_model: Optional[str] = None
    ):
        self.tts_protocol = tts_protocol
        self.sample_rate = sample_rate
        self.max_segment_length = max_segment_length
        self._nlp = self._load_language_model(language_model)

    def _load_language_model(self, language_model: Optional[str]) -> Language:
        if language_model:
            try:
                import spacy
                return spacy.load(language_model)
            except OSError:
                pass

        nlp: Language = MultiLanguage()
        nlp.add_pipe("sentencizer")
        return nlp

    def process_chapter(
        self,
        text: str,
        output_path: Path,
        workspace_path: Path,
        voice: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        # TODO: 重构 temp 逻辑，不需要 temp 这个概念了
        segments = list(self.split_text_into_segments(text))
        if not segments:
            return

        audio_segments = []
        temp_files_created = []
        try:
            for i, segment in enumerate(segments):
                if progress_callback:
                    progress_callback(i + 1, len(segments))

                session_id = str(uuid.uuid4())[:8]
                temp_audio_path = workspace_path / f"{session_id}_segment_{i:04d}.wav"
                temp_files_created.append(temp_audio_path)

                self.tts_protocol.convert_text_to_audio(
                    text=segment,
                    output_path=temp_audio_path,
                    voice=voice
                )
                if not temp_audio_path.exists():
                    continue

                audio_data: np.ndarray
                sr: int
                audio_data, sr = sf.read(temp_audio_path)
                if sr != self.sample_rate:
                    pass
                audio_segments.append(audio_data)

            final_audio = np.concatenate(audio_segments)
            sf.write(output_path, final_audio, self.sample_rate)

        finally:
            for temp_file in temp_files_created:
                if temp_file.exists():
                    temp_file.unlink()

    def split_text_into_segments(self, text: str) -> Generator[str, None, None]:
        text = text.strip()
        if not text:
            return

        all_resources = []
        doc = self._nlp(text)
        next_start_incision = 2

        for sent in doc.sents:
            segment_text = sent.text.strip()
            if not segment_text:
                continue

            resources = list(self._build_segment_internal_structure(sent))
            if not resources:
                continue

            resources[0].start_incision = next_start_incision
            resources[-1].end_incision = 2
            next_start_incision = 2

            all_resources.extend(resources)

        if not all_resources:
            text_resource = Resource(
                count=len(text),
                start_incision=SENTENCE_LEVEL,
                end_incision=SENTENCE_LEVEL,
                payload=text
            )
            all_resources.append(text_resource)

        yield from self._split_by_resource_segmentation(all_resources)

    def _build_segment_internal_structure(self, sent: Span) -> Generator[Resource, None, None]:
        current_fragment: list[str] = []
        for token in sent:
            if token.is_punct:
                if current_fragment:
                    fragment_text = "".join(current_fragment)
                    fragment_resource = Resource(
                        count=len(fragment_text),
                        start_incision=SEGMENT_LEVEL,
                        end_incision=SEGMENT_LEVEL,
                        payload=fragment_text
                    )
                    yield fragment_resource
                    current_fragment = []

                punct_resource = Resource(
                    count=len(token.text),
                    start_incision=SEGMENT_LEVEL,
                    end_incision=SEGMENT_LEVEL,
                    payload=token.text
                )
                yield punct_resource
            else:
                current_fragment.append(token.text_with_ws)

        if current_fragment:
            fragment_text = "".join(current_fragment)
            fragment_resource = Resource(
                count=len(fragment_text),
                start_incision=SEGMENT_LEVEL,
                end_incision=SEGMENT_LEVEL,
                payload=fragment_text
            )
            yield fragment_resource

    def _split_by_resource_segmentation(self, resources: List[Resource]) -> Generator[str, None, None]:
        max_byte_length = self.max_segment_length * 3
        groups = list(split(
            iter(resources),
            max_segment_count=max_byte_length,
            border_incision=1,
            gap_rate=0.0,
            tail_rate=0.0
        ))

        for group in groups:
            segment_chars = []
            for item in group.body:
                if isinstance(item, Segment):
                    for resource in item.resources:
                        segment_chars.append(resource.payload)
                elif isinstance(item, Resource):
                    segment_chars.append(item.payload)

            combined_text = "".join(segment_chars).strip()
            if combined_text:
                yield combined_text