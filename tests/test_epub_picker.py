#!/usr/bin/env python3
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech.epub_picker import EpubPicker

TEST_BOOKS = [
    {
        "filename": "The little prince.epub",
        "expected": {
            "epub_version": "EPUB2",
            "meta_titles": [("The little prince", {})],
            "meta_creators": [
                ("Antoine de Saint-Exupéry", {'{http://www.idpf.org/2007/opf}file-as': 'Saint-Exupéry, Antoine de & Howard, Richard', '{http://www.idpf.org/2007/opf}role': 'aut'}),
                ("Richard Howard", {'{http://www.idpf.org/2007/opf}file-as': 'Saint-Exupéry, Antoine de & Howard, Richard', '{http://www.idpf.org/2007/opf}role': 'aut'})
            ],
            "has_cover": True,
            "nav_items": [
                ("Chapter I", "7358.xhtml"),
                ("Chapter II", "7521.xhtml"),
                ("Chapter III", "7664.xhtml"),
                ("Chapter IV", "7747.xhtml"),
                ("Chapter V", "7850.xhtml"),
                ("Chapter VI", "7921.xhtml"),
                ("Chapter VII", "8066.xhtml"),
                ("Chapter VIII", "8197.xhtml"),
                ("Chapter IX", "8284.xhtml"),
                ("Chapter X", "8525.xhtml"),
                ("Chapter XI", "8616.xhtml"),
                ("Chapter XII", "8671.xhtml"),
                ("Chapter XIII", "8892.xhtml"),
                ("Chapter XIV", "9047.xhtml"),
                ("Chapter XV", "9250.xhtml"),
                ("Chapter XVI", "9281.xhtml"),
                ("Chapter XVII", "9416.xhtml"),
                ("Chapter XVIII", "9459.xhtml"),
                ("Chapter XIX", "9506.xhtml"),
                ("Chapter XX", "9567.xhtml"),
                ("Chapter XXI", "9826.xhtml"),
                ("Chapter XXII", "9901.xhtml"),
                ("Chapter XXIII", "9940.xhtml"),
                ("Chapter XXIV", "10059.xhtml"),
                ("Chapter XXV", "10258.xhtml"),
                ("Chapter XXVI", "10609.xhtml"),
                ("Chapter XXVII", "10740.xhtml"),
                ("Saint-Exupéry: A Short Biography", "10740.xhtml#10664")
            ]
        }
    },
    {
        "filename": "明朝那些事儿.epub",
        "expected": {
            "epub_version": "EPUB2",
            "meta_titles": [("《明朝那些事儿》", {})],
            "meta_creators": [("Unknown Author", {"id": "creator"})],
            "has_cover": False,
            "nav_items": [
                ("序言", "chap_1.xhtml"),
                ("第壹部 洪武大帝", "volume_1.xhtml"),
                ("第一章 童年", "chap_2.xhtml"),
                ("第二章 灾难", "chap_3.xhtml")
            ]
        }
    },
    {
        "filename": "Ming dynasty.epub",
        "expected": {
            "epub_version": "EPUB2",
            "meta_titles": [("Ming dynasty", {})],
            "meta_creators": [("Unknown", {})],
            "has_cover": False,
            "nav_items": [
                ("Start", "index.html")
            ]
        }
    },
    {
        "filename": "Ming dynasty no ncx ref.epub",
        "expected": {
            "epub_version": None,
            "meta_titles": [("Ming dynasty", {})],
            "meta_creators": [("Unknown", {})],
            "has_cover": False,
            "nav_items": [
                ("Index", "index.html")
            ]
        }
    }
]

def test_picker_functionality():
    """Comprehensive test of EpubPicker functionality"""
    print("🧪 Starting comprehensive EpubPicker functionality test...\n")

    for i, test_book in enumerate(TEST_BOOKS, 1):
        filename = test_book["filename"]
        expected = test_book["expected"]

        print(f"📚 Testing book {i}: {filename}")

        try:
            # Create picker instance
            epub_path = Path(__file__).parent / "assets" / filename
            picker = EpubPicker(epub_path)

            # 1. Test EPUB version detection
            actual_version = picker.epub_version
            assert actual_version == expected["epub_version"], f"EPUB version mismatch: expected {expected['epub_version']}, actual {actual_version}"

            # 2. Test metadata extraction
            actual_titles = picker.meta_titles
            assert len(actual_titles) > 0, "Should have title metadata"
            assert actual_titles[0][0] == expected["meta_titles"][0][0], f"Title mismatch: expected '{expected['meta_titles'][0][0]}', actual '{actual_titles[0][0]}'"

            actual_creators = picker.meta_creators
            assert len(actual_creators) > 0, "Should have creator metadata"
            assert actual_creators[0][0] == expected["meta_creators"][0][0], f"Creator mismatch: expected '{expected['meta_creators'][0][0]}', actual '{actual_creators[0][0]}'"

            # 3. Test cover extraction
            has_cover = picker.cover is not None
            assert has_cover == expected["has_cover"], f"Cover existence mismatch: expected {expected['has_cover']}, actual {has_cover}"

            # 4. Test navigation items extraction
            nav_items = list(picker.get_nav_items())
            expected_nav_count = len(expected["nav_items"])
            actual_nav_count = len(nav_items)

            assert actual_nav_count == expected_nav_count, f"Navigation items count mismatch: expected {expected_nav_count}, actual {actual_nav_count}"

            # Verify each navigation item
            for j, (actual_title, actual_href) in enumerate(nav_items):
                expected_title, expected_href = expected["nav_items"][j]
                assert actual_title == expected_title, f"Navigation item {j+1} title mismatch: expected '{expected_title}', actual '{actual_title}'"
                assert actual_href == expected_href, f"Navigation item {j+1} href mismatch: expected '{expected_href}', actual '{actual_href}'"

            # 5. Test text extraction from first chapter
            if nav_items:
                first_href = nav_items[0][1]
                text_content = picker.extract_text(first_href)
                assert len(text_content) > 0, "Should extract text from chapter, got empty string"
                print(f"   📖 Text extraction: {len(text_content)} characters from first chapter")

            print(f"   ✅ {filename} all tests passed")
            print(f"   📊 Version: {actual_version}, Navigation items: {actual_nav_count}")

        except Exception as e:
            print(f"   ❌ {filename} test failed: {e}")
            raise

    print("\n🎉 All books tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_picker_functionality()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)