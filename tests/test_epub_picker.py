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
                ("第二章 灾难", "chap_3.xhtml"),
                ("第三章 踏上征途", "chap_4.xhtml"),
                ("第四章 就从这里起步", "chap_5.xhtml"),
                ("第五章 储蓄资本", "chap_6.xhtml"),
                ("第六章 霸业的开始", "chap_7.xhtml"),
                ("第七章 可怕的对手", "chap_8.xhtml"),
                ("第八章 可怕的陈友谅", "chap_9.xhtml"),
                ("第九章 决战不可避免", "chap_10.xhtml"),
                ("第十章 等待最好的时机", "chap_11.xhtml"),
                ("第十一章 洪都的奇迹", "chap_12.xhtml"),
                ("第十二章 鄱阳湖！决死战！", "chap_13.xhtml"),
                ("第十三章 下一个目标，张士诚！", "chap_14.xhtml"),
                ("第十四章 复仇", "chap_15.xhtml"),
                ("第十五章 远征沙漠", "chap_16.xhtml"),
                ("第十六章 建国", "chap_17.xhtml"),
                ("第十七章 胡惟庸案件", "chap_18.xhtml"),
                ("第十八章 扫除一切腐败者！", "chap_19.xhtml"),
                ("第十九章 空印案郭桓案", "chap_20.xhtml"),
                ("第二十章 最后的名将——蓝玉", "chap_21.xhtml"),
                ("第二十一章 蓝玉的覆灭", "chap_22.xhtml"),
                ("第二十二章 制度后的秘密", "chap_23.xhtml"),
                ("第二十三章 终点，起点：最后的朋友们", "chap_24.xhtml"),
                ("第二十四章 建文帝：建文帝的忧虑", "chap_25.xhtml"),
                ("第二十五章 等待中的朱棣：朱棣的痛苦", "chap_26.xhtml"),
                ("第二十六章 准备行动", "chap_27.xhtml"),
                ("第二十七章 不得不反了！", "chap_28.xhtml"),
                ("第二十八章 你死我活的战争", "chap_29.xhtml"),
                ("第二十九章 朱棣的对手", "chap_30.xhtml"),
                ("第三十章 离胜利只差一步！", "chap_31.xhtml"),
                ("第三十一章 殉国、疑团、残暴、软弱", "chap_32.xhtml"),
                ("第贰部 万国来朝", "volume_2.xhtml"),
                ("第一章 帝王的烦恼", "chap_33.xhtml"),
                ("第二章 帝王的荣耀", "chap_34.xhtml"),
                ("第三章 帝王的抉择", "chap_35.xhtml"),
                ("第四章 郑和之后，再无郑和", "chap_36.xhtml"),
                ("第五章 纵横天下", "chap_37.xhtml"),
                ("第六章 天子守国门！", "chap_38.xhtml"),
                ("第七章 逆命者必剪除之！", "chap_39.xhtml"),
                ("第八章 帝王的财产", "chap_40.xhtml"),
                ("第九章 生死相搏", "chap_41.xhtml"),
                ("第十章 最后的秘密", "chap_42.xhtml"),
                ("第十一章 朱高炽的勇气和疑团", "chap_43.xhtml"),
                ("第十二章 朱瞻基是个好同志", "chap_44.xhtml"),
                ("第十三章 祸根", "chap_45.xhtml"),
                ("第十四章 土木堡", "chap_46.xhtml"),
                ("尾声\n正统十四年（1449）九月十二日。", "chap_47.xhtml"),
                ("第十五章 力挽狂澜", "chap_48.xhtml"),
                ("第十六章 决断！", "chap_49.xhtml"),
                ("第十七章 信念", "chap_50.xhtml"),
                ("第十八章 北京保卫战", "chap_51.xhtml"),
                ("第十九章 朱祁镇的奋斗", "chap_52.xhtml"),
                ("第二十章 回家", "chap_53.xhtml"),
                ("第二十一章 囚徒朱祁镇", "chap_54.xhtml"),
                ("第二十二章 夺门", "chap_55.xhtml"),
                ("第叁部 妖孽宫廷", "volume_3.xhtml"),
                ("第一章 有冤报冤，有仇报仇", "chap_56.xhtml"),
                ("第二章 隐藏的敌人", "chap_57.xhtml"),
                ("第三章 公道", "chap_58.xhtml"),
                ("第四章 不伦之恋", "chap_59.xhtml"),
                ("第五章 武林大会", "chap_60.xhtml"),
                ("第六章 明君", "chap_61.xhtml"),
                ("第七章 斗争，还是隐忍？", "chap_62.xhtml"),
                ("第八章 传奇就此开始", "chap_63.xhtml"),
                ("第九章 悟道", "chap_64.xhtml"),
                ("第十章 机会终于到来", "chap_65.xhtml"),
                ("第十一章 必杀刘瑾", "chap_66.xhtml"),
                ("第十二章 皇帝的幸福生活", "chap_67.xhtml"),
                ("第十三章 无人知晓的胜利", "chap_68.xhtml"),
                ("第十四章 东山再起", "chap_69.xhtml"),
                ("第十五章 孤军", "chap_70.xhtml"),
                ("第十六章 奋战", "chap_71.xhtml"),
                ("第十七章 死亡的阴谋", "chap_72.xhtml"),
                ("第十八章 沉默的较量", "chap_73.xhtml"),
                ("第十九章 终结的归宿", "chap_74.xhtml"),
                ("第二十章 新的开始", "chap_75.xhtml"),
                ("第肆部 粉饰太平", "volume_4.xhtml"),
                ("第一章 皇帝很脆弱", "chap_76.xhtml"),
                ("第二章 大臣很强悍", "chap_77.xhtml"),
                ("第三章 解脱", "chap_78.xhtml"),
                ("第四章 龙争虎斗", "chap_79.xhtml"),
                ("第五章 锋芒", "chap_80.xhtml"),
                ("第六章 最阴险的敌人", "chap_81.xhtml"),
                ("第七章 徐阶的觉醒", "chap_82.xhtml"),
                ("第八章 天下，三人而已", "chap_83.xhtml"),
                ("第九章 致命的疏漏", "chap_84.xhtml"),
                ("第十章 隐藏的精英", "chap_85.xhtml"),
                ("第十一章 勇气", "chap_86.xhtml"),
                ("第十二章 东南的奇才", "chap_87.xhtml"),
                ("第十三章 天下第一幕僚", "chap_88.xhtml"),
                ("第十四章 强敌", "chap_89.xhtml"),
                ("第十五章 天才的谋略", "chap_90.xhtml"),
                ("第十六章 战争——最后的抉择", "chap_91.xhtml"),
                ("第十七章 名将的起点", "chap_92.xhtml"),
                ("第十八章 制胜之道", "chap_93.xhtml"),
                ("第十九章 侵略者的末日", "chap_94.xhtml"),
                ("第二十章 英雄的结局", "chap_95.xhtml"),
                ("第二十一章 曙光", "chap_96.xhtml"),
                ("第二十二章 胜利", "chap_97.xhtml"),
                ("第伍部 帝国飘摇", "volume_5.xhtml"),
                ("第一章 致命的正义", "chap_98.xhtml"),
                ("第二章 奇怪的人", "chap_99.xhtml"),
                ("第三章 天才的对弈", "chap_100.xhtml"),
                ("第四章 成熟", "chap_101.xhtml"),
                ("第五章 最终的乱战", "chap_102.xhtml"),
                ("第六章 高拱的成就", "chap_103.xhtml"),
                ("第七章 死斗", "chap_104.xhtml"),
                ("第八章 阴谋", "chap_105.xhtml"),
                ("第九章 张居正的缺陷", "chap_106.xhtml"),
                ("第十章 敌人", "chap_107.xhtml"),
                ("第十一章 千古，唯此一人", "chap_108.xhtml"),
                ("第十二章 谜团", "chap_109.xhtml"),
                ("第十三章 野心的起始", "chap_110.xhtml"),
                ("第十四章 明朝的愤怒", "chap_111.xhtml"),
                ("第十五章 兵不厌诈", "chap_112.xhtml"),
                ("第十六章 平壤，血战", "chap_113.xhtml"),
                ("第十七章 不世出之名将", "chap_114.xhtml"),
                ("第十八章 二次摊牌", "chap_115.xhtml"),
                ("第十九章 胜算", "chap_116.xhtml"),
                ("第二十章 为了忘却的纪念", "chap_117.xhtml"),
                ("第陆部 日暮西山", "volume_6.xhtml"),
                ("第一章 绝顶的官僚", "chap_118.xhtml"),
                ("第二章 和稀泥的艺术", "chap_119.xhtml"),
                ("第三章 游戏的开始", "chap_120.xhtml"),
                ("第四章 混战", "chap_121.xhtml"),
                ("第五章 东林崛起", "chap_122.xhtml"),
                ("第六章 谋杀", "chap_123.xhtml"),
                ("第七章 不起眼的敌人", "chap_124.xhtml"),
                ("第八章 萨尔浒", "chap_125.xhtml"),
                ("第九章 东林党的实力", "chap_126.xhtml"),
                ("第十章 小人物的奋斗", "chap_127.xhtml"),
                ("第十一章 强大，无比强大", "chap_128.xhtml"),
                ("第十二章 天才的敌手", "chap_129.xhtml"),
                ("第十三章 一个监狱看守", "chap_130.xhtml"),
                ("第十四章 毁灭之路", "chap_131.xhtml"),
                ("第十五章 道统", "chap_132.xhtml"),
                ("第十六章 杨涟", "chap_133.xhtml"),
                ("第十七章 殉道", "chap_134.xhtml"),
                ("第十八章 袁崇焕", "chap_135.xhtml"),
                ("第十九章 决心", "chap_136.xhtml"),
                ("第二十章 胜利 结局", "chap_137.xhtml"),
                ("第柒部 大结局", "volume_7.xhtml"),
                ("第一章 皇太极", "chap_138.xhtml"),
                ("第二章 宁远，决战", "chap_139.xhtml"),
                ("第三章 疑惑", "chap_140.xhtml"),
                ("第四章 夜半歌声", "chap_141.xhtml"),
                ("第五章 算账", "chap_142.xhtml"),
                ("第六章 起复", "chap_143.xhtml"),
                ("第七章 杀人", "chap_144.xhtml"),
                ("第八章 坚持到底的人", "chap_145.xhtml"),
                ("第九章 阴谋", "chap_146.xhtml"),
                ("第十章 斗争技术", "chap_147.xhtml"),
                ("第十一章 投降？", "chap_148.xhtml"),
                ("第十二章 纯属偶然", "chap_149.xhtml"),
                ("第十三章 第二个猛人", "chap_150.xhtml"),
                ("第十四章 突围", "chap_151.xhtml"),
                ("第十五章 一个文雅的人", "chap_152.xhtml"),
                ("第十六章 孙传庭", "chap_153.xhtml"),
                ("第十七章 奇迹", "chap_154.xhtml"),
                ("第十八章 天才的计划", "chap_155.xhtml"),
                ("第十九章 选择", "chap_156.xhtml"),
                ("第二十章 没有选择", "chap_157.xhtml"),
                ("第二十一章 结束了？", "chap_158.xhtml"),
                ("后记\n本来没想写，但还是写一个吧，毕竟那么多字都写了。", "chap_159.xhtml")
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