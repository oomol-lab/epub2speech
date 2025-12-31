#!/usr/bin/env python3
import os
import random
import sys
import traceback
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech.epub_picker import EpubPicker

TEST_BOOKS = [
    {
        "filename": "The little prince.epub",
        "sample_chapters": [
            {
                "nav_title": "Chapter I",
                "href": "7358.xhtml",
                "expected_head": "Chapter I Once when I was six years old I saw a magnificent picture in a book, called True Stories from Nature, about the primeval forest. It was a pi",
                "expected_tail": "el. I would talk to him about bridge, and golf, and politics, and neckties. And the grown-up would be greatly pleased to have met such a sensible man.",
            },
            {
                "nav_title": "Chapter II",
                "href": "7521.xhtml",
                "expected_head": "Chapter II So I lived my life alone, without anyone that I could really talk to, until I had an accident with my plane in the Desert of Sahara, six ye",
                "expected_tail": '" He bent his head over the drawing: "Not so small that-- Look! He has gone to sleep..." And that is how I made the acquaintance of the little prince.',
            },
            {
                "nav_title": "Chapter III",
                "href": "7664.xhtml",
                "expected_head": "Chapter III It took me a long time to learn where he came from. The little prince, who asked me so many questions, never seemed to hear the ones I ask",
                "expected_tail": 'esn\'t matter. Where I live, everything is so small!" And, with perhaps a hint of sadness, he added: "Straight ahead of him, nobody can go very far..."',
            },
            {
                "nav_title": "Chapter IV",
                "href": "7747.xhtml",
                "expected_head": "Chapter IV I had thus learned a second fact of great importance: this was that the planet the little prince came from was scarcely any larger than a h",
                "expected_tail": " like himself. But I, alas, do not know how to see sheep through the walls of boxes. Perhaps I am a little like the grown-ups. I have had to grow old.",
            },
            {
                "nav_title": "Chapter X",
                "href": "8525.xhtml",
                "expected_head": "Chapter X He found himself in the neighbourhood of the asteroids 325, 326, 327, 328, 329, and 330. He began, therefore, by visiting them, in order to ",
                "expected_tail": ', hastily. He had a magnificent air of authority. "The grown-ups are very strange," the little prince said to himself, as he continued on his journey.',
            },
        ],
    },
    {
        "filename": "明朝那些事儿.epub",
        "sample_chapters": [
            {
                "nav_title": "序言",
                "href": "chap_1.xhtml",
                "expected_head": "序言 本书由爱上阅读的网友搜集整理，更多精彩书籍请访问https://www.isyd.net 声明：本书来自互联网，仅供参考、查阅资料，版权归作者所有！！ 敬告：请在下载后的24小时内删除",
                "expected_tail": "我想写的，是一部可以在轻松中了解历史的书，一部好看的历史。 仅此而已！ 好了，就此开始吧。",
            },
            {
                "nav_title": "第一章 童年",
                "href": "chap_2.xhtml",
                "expected_head": "第一章 童年 我们从一份档案开始。 姓名：朱元璋 别名（外号）：朱重八、朱国瑞 性别：男 民族：汉 血型：？ 学历：无文凭，秀才举人进士统统的不是",
                "expected_tail": "这一年，他十七岁。 很快一场灾难就要降临到他的身上，但同时，一个伟大的事业也在等待着他。只有像传说中的凤凰一样，历经苦难，投入火中",
            },
            {
                "nav_title": "后记\n本来没想写，但还是写一个吧，毕竟那么多字都写了。",
                "href": "chap_159.xhtml",
                "expected_head": "后记 本来没想写，但还是写一个吧，毕竟那么多字都写了。",
                "expected_tail": "论著合集》，商鸿逵，北京大学出版社1988年版； 《二十五史新编》，上海古籍出版社2004年版； 《清史新考》，王锺翰，辽宁大学出版社1990年版； 《明清史新析》，韦庆远，中国社会科学出版社1995年版； 《明亡清兴六十年》，阎崇年，中华书局2006年版； 《袁崇焕传》，阎崇年，中华书局2005年版； 《杨大洪先生文集》，（明）杨涟； 《三垣笔记》，（明）李清； 《杨文弱先生集》，（明）杨嗣昌。",
            },
        ],
    },
    {
        "filename": "Ming dynasty.epub",
        "sample_chapters": [
            {
                "nav_title": "Start",
                "href": "index.html",
                "expected_head": "The Ming dynasty, officially the Great Ming, was an imperial dynasty of China that ruled from 1368 to 1644, following the collapse of the Mongol-led Y",
                "expected_tail": "t it was defeated shortly afterwards by the Manchu-led Eight Banner armies of the Qing dynasty, with the help of the defecting Ming general Wu Sangui.",
            }
        ],
    },
    {
        "filename": "Ming dynasty no ncx ref.epub",
        "sample_chapters": [
            {
                "nav_title": "Index",
                "href": "index.html",
                "expected_head": "The Ming dynasty, officially the Great Ming, was an imperial dynasty of China that ruled from 1368 to 1644, following the collapse of the Mongol-led Y",
                "expected_tail": "t it was defeated shortly afterwards by the Manchu-led Eight Banner armies of the Qing dynasty, with the help of the defecting Ming general Wu Sangui.",
            }
        ],
    },
]


def compare_text_head_tail(extracted_text, expected_head, expected_tail, max_chars=200):
    if not extracted_text:
        return False, False, "", ""

    head_actual = extracted_text[:max_chars] if len(extracted_text) > max_chars else extracted_text
    tail_actual = extracted_text[-max_chars:] if len(extracted_text) > max_chars else extracted_text

    head_match = expected_head.lower() in head_actual.lower()
    tail_match = expected_tail.lower() in tail_actual.lower()

    return head_match, tail_match, head_actual, tail_actual


class TestTextExtractor(unittest.TestCase):
    """Test cases for text extraction functionality"""

    def test_extractor_functionality(self):
        """Test text extractor functionality"""
        print("🧪 Starting text extractor functionality test...\n")

        all_passed = True

        for book_data in TEST_BOOKS:
            filename = book_data["filename"]
            sample_chapters = book_data["sample_chapters"]

            print(f"📚 Testing book: {filename}")

            with self.subTest(book=filename):
                try:
                    epub_path = Path(__file__).parent / "assets" / filename
                    picker = EpubPicker(epub_path)

                    for i, chapter_data in enumerate(sample_chapters):
                        nav_title = chapter_data["nav_title"]
                        href = chapter_data["href"]
                        expected_head = chapter_data["expected_head"]
                        expected_tail = chapter_data["expected_tail"]

                        print(f"   📄 Testing chapter {i + 1}: {nav_title}")

                        extracted_text = picker.extract_text(href)

                        if not extracted_text:
                            print(f"      ⚠️  No text extracted from {href}")
                            continue

                        head_match, tail_match, head_actual, tail_actual = compare_text_head_tail(
                            extracted_text, expected_head, expected_tail
                        )

                        self.assertTrue(
                            head_match,
                            f"Head mismatch for {nav_title}\nExpected: ...{expected_head[-50:]}...\nActual:   ...{head_actual[-50:]}...",
                        )
                        self.assertTrue(
                            tail_match,
                            f"Tail mismatch for {nav_title}\nExpected: ...{expected_tail[:50]}...\nActual:   ...{tail_actual[:50:]}...",
                        )

                        head_chars = min(200, len(head_actual))
                        print(f"      ✅ Head matches (first ~{head_chars} chars)")
                        tail_chars = min(200, len(tail_actual))
                        print(f"      ✅ Tail matches (last ~{tail_chars} chars)")
                        print(f"      📊 Extracted {len(extracted_text)} characters total")

                    print(f"   ✅ {filename} text extraction tests completed\n")

                except Exception as e:
                    print(f"   ❌ {filename} test failed: {e}")
                    all_passed = False
                    traceback.print_exc()

        self.assertTrue(all_passed, "Some text extraction tests failed!")
        print("🎉 All text extraction tests passed!")

    def generate_test_data(self):
        """Generate test data from EPUB files - utility method"""
        print("🔧 Generating test data from EPUB files...\n")

        test_books = [book["filename"] for book in TEST_BOOKS]
        generated_data = []

        for filename in test_books:
            print(f"📊 Analyzing {filename}...")

            try:
                epub_path = Path(__file__).parent / "assets" / filename
                picker = EpubPicker(epub_path)
                nav_items = list(picker.get_nav_items())

                if not nav_items:
                    print(f"   ⚠️  No navigation items found in {filename}")
                    continue

                print(f"   Found {len(nav_items)} chapters")

                sample_size = min(3, len(nav_items))
                if len(nav_items) > sample_size:
                    sample_items = random.sample(nav_items, sample_size)
                else:
                    sample_items = nav_items

                book_data = {"filename": filename, "sample_chapters": []}

                for nav_title, href in sample_items:
                    print(f"   📄 Sampling: {nav_title}")

                    extracted_text = picker.extract_text(href)

                    if extracted_text:
                        head_text = extracted_text[:200] if len(extracted_text) > 200 else extracted_text
                        tail_text = extracted_text[-200:] if len(extracted_text) > 200 else extracted_text

                        chapter_data = {
                            "nav_title": nav_title,
                            "href": href,
                            "expected_head": head_text,
                            "expected_tail": tail_text,
                        }
                        book_data["sample_chapters"].append(chapter_data)

                        char_count = len(extracted_text)
                        print(f"      ✓ Extracted {char_count} characters")
                    else:
                        print("      ⚠️  No text extracted")

                if book_data["sample_chapters"]:
                    generated_data.append(book_data)
                    chapter_count = len(book_data["sample_chapters"])
                    print(f"   ✅ Generated data for {chapter_count} chapters\n")
                else:
                    print(f"   ⚠️  No valid chapters found for {filename}")
                    print()

            except Exception as e:
                print(f"   ❌ Error processing {filename}: {e}")
                print()
                traceback.print_exc()

        print("📋 Generated test data structure:")
        print("You can copy this to replace TEST_BOOKS in test_extractor.py")
        print("=" * 60)
        print("TEST_BOOKS = [")
        for book_data in generated_data:
            print("    {")
            print(f'        "filename": "{book_data["filename"]}",')
            print('        "sample_chapters": [')
            for chapter in book_data["sample_chapters"]:
                print("            {")
                print(f'                "nav_title": "{chapter["nav_title"]}",')
                print(f'                "href": "{chapter["href"]}",')
                head_escaped = chapter["expected_head"].replace('"', '\\"').replace("\n", "\\n")
                tail_escaped = chapter["expected_tail"].replace('"', '\\"').replace("\n", "\\n")
                print(f'                "expected_head": "{head_escaped}",')
                print(f'                "expected_tail": "{tail_escaped}"')
                print("            },")
            print("        ]")
            print("    },")
        print("]")
        print("=" * 60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
