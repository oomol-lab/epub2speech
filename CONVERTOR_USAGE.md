# EPUB转M4B转换器使用说明

## 概述

`convertor.py` 是 epub2speech 的主入口文件，它将 EPUB 电子书转换为 M4B 有声书格式。该转换器组装了以下模块：

- **EpubPicker**: EPUB 文件解析和章节提取
- **ChapterTTS**: 章节文本转语音处理
- **TTS 协议**: 支持 Azure 等 TTS 服务
- **M4BGenerator**: 生成带章节导航的 M4B 文件

## 快速开始

### 基本用法

```python
from pathlib import Path
from epub2speech.convertor import convert_epub_to_m4b
from epub2speech.tts.azure_provider import AzureTextToSpeech

# 配置参数
epub_path = Path("book.epub")
workspace = Path("temp_workspace")
output_path = Path("output/book.m4b")

# 创建 TTS 协议实例
tts_protocol = AzureTextToSpeech()

# 执行转换
result = convert_epub_to_m4b(
    epub_path=epub_path,
    workspace=workspace,
    output_path=output_path,
    tts_protocol=tts_protocol,
    max_chapters=10,  # 可选：限制章节数
    voice="zh-CN-XiaoxiaoNeural"  # 可选：指定语音
)

print(f"转换完成: {result}")
```

### 使用进度回调

```python
def progress_callback(progress):
    print(f"进度: {progress.progress_percentage:.1f}% - {progress.current_step}")
    if progress.chapter_title:
        print(f"  当前章节: {progress.chapter_title}")

result = convert_epub_to_m4b(
    epub_path=epub_path,
    workspace=workspace,
    output_path=output_path,
    tts_protocol=tts_protocol,
    progress_callback=progress_callback
)
```

## 类接口

### EpubToSpeechConverter

主要转换器类，提供更细粒度的控制。

```python
from epub2speech.convertor import EpubToSpeechConverter

# 创建转换器实例
converter = EpubToSpeechConverter(
    epub_path=Path("book.epub"),
    workspace=Path("temp_workspace"),
    output_path=Path("output.m4b"),
    tts_protocol=AzureTextToSpeech()
)

# 执行转换
result = converter.convert(
    max_chapters=5,
    voice="zh-CN-XiaoxiaoNeural"
)
```

### 参数说明

#### convert_epub_to_m4b 函数参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `epub_path` | Path | 是 | EPUB 文件路径 |
| `workspace` | Path | 是 | 工作目录（临时文件存放） |
| `output_path` | Path | 是 | 输出 M4B 文件路径 |
| `tts_protocol` | TextToSpeechProtocol | 是 | TTS 协议实例 |
| `max_chapters` | int | 否 | 最大转换章节数 |
| `voice` | str | 否 | TTS 语音名称 |
| `progress_callback` | Callable | 否 | 进度回调函数 |

#### ConversionProgress 类

进度信息数据结构：

```python
@dataclass
class ConversionProgress:
    current_chapter: int      # 当前章节序号
    total_chapters: int       # 总章节数
    current_step: str         # 当前步骤描述
    chapter_title: str        # 当前章节标题

    @property
    def progress_percentage(self) -> float:
        # 返回进度百分比
```

## TTS 配置

### Azure TTS

需要配置 Azure 语音服务凭据：

```python
from epub2speech.tts.azure_provider import AzureTextToSpeech

tts_protocol = AzureTextToSpeech()

# 检查配置
if not tts_protocol.validate_config():
    print("需要配置 Azure 语音服务凭据")
    # 配置方法：
    # 1. 创建配置文件 ~/.epub2speech/azure_config.json
    # 2. 包含 subscription_key 和 region 信息
```

### 支持的语言和语音

- **中文**: zh-CN-XiaoxiaoNeural, zh-CN-YunxiNeural
- **英文**: en-US-JennyNeural, en-US-GuyNeural
- **日文**: ja-JP-NanamiNeural, ja-JP-KeitaNeural

## 工作目录结构

转换过程中会在工作目录创建以下结构：

```
temp_workspace/
├── audio_chapters/          # 章节音频文件
│   ├── chapter_001_序言.wav
│   ├── chapter_002_第一章.wav
│   └── ...
├── temp_chapter_1/          # 临时处理目录
├── temp_chapter_2/
├── cover.jpg               # 封面图片（如果有）
└── output.m4b              # 生成的 M4B 文件
```

## 错误处理

转换器会自动处理常见错误：

- **EPUB 解析失败**: 抛出 `ValueError`
- **章节文本为空**: 跳过该章节
- **TTS 转换失败**: 记录错误并继续
- **音频文件生成失败**: 抛出 `RuntimeError`

```python
try:
    result = convert_epub_to_m4b(...)
except ValueError as e:
    print(f"EPUB 文件无效: {e}")
except RuntimeError as e:
    print(f"转换失败: {e}")
```

## 性能优化建议

1. **批量处理**: 使用 `max_chapters` 参数分批处理大文件
2. **工作目录**: 使用 SSD 存储工作目录以提高性能
3. **语音选择**: 选择合适的语音以平衡质量和速度
4. **清理**: 及时清理工作目录释放空间

## 示例项目

查看 `example_usage.py` 获取完整的使用示例。

运行测试：
```bash
python test_convertor.py
```

## 依赖要求

- Azure 认知服务订阅（用于 TTS）
- FFmpeg（用于音频处理）
- 足够的磁盘空间（临时文件 + 输出文件）