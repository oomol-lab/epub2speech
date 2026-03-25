<div align=center>
  <h1>EPUB to Speech</h1>
  <p>
    <a href="https://github.com/oomol-lab/epub2speech/actions/workflows/merge-build.yml" target="_blank"><img src="https://img.shields.io/github/actions/workflow/status/oomol-lab/epub2speech/merge-build.yml?branch=main&label=build" alt="build" /></a>
    <a href="https://pypi.org/project/epub2speech/" target="_blank"><img src="https://img.shields.io/badge/pip_install-epub2speech-blue" alt="pip install epub2speech" /></a>
    <a href="https://pypi.org/project/epub2speech/" target="_blank"><img src="https://img.shields.io/pypi/v/epub2speech.svg" alt="pypi epub2speech" /></a>
    <a href="https://pypi.org/project/epub2speech/" target="_blank"><img src="https://img.shields.io/pypi/pyversions/epub2speech.svg" alt="python versions" /></a>
    <a href="https://github.com/oomol-lab/epub2speech/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/oomol-lab/epub2speech" alt="license" /></a>
  </p>
  <p><a href="./README.md">English</a> | 中文</p>
</div>

使用多种文本转语音服务将 EPUB 电子书转换为高质量的有声读物。

## 功能特点

- **📚 EPUB 支持**: 兼容 EPUB 2 和 EPUB 3 格式
- **🎙️ 多 TTS 提供商**: 支持 Azure、豆包和 Qwen TTS 服务
- **🔄 自动检测**: 自动检测已配置的提供商
- **🌍 多语言支持**: 支持多种语言和语音
- **📱 M4B 输出**: 生成带章节导航的标准 M4B 有声读物格式
- **🧹 噪点清洗**: 自动移除常见阅读噪点（目录条目、装饰分隔线、孤立页码）
- **🔧 CLI 界面**: 易于使用的命令行工具，带进度跟踪

## 基本用法

```bash
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
```

## 安装

### 前置要求

- Python 3.11 或更高版本
- FFmpeg（用于音频处理）
- TTS 提供商凭据（Azure、豆包或 Qwen）

### 安装依赖

```bash
# 安装 Python 依赖
pip install poetry
poetry install

# 安装 FFmpeg
# macOS: brew install ffmpeg
# Ubuntu/Debian: sudo apt install ffmpeg
# Windows: 从 https://ffmpeg.org/download.html 下载
```

## 快速开始

### 选项 1：使用 Azure TTS

设置环境变量并运行：

```bash
export AZURE_SPEECH_KEY="您的订阅密钥"
export AZURE_SPEECH_REGION="您的区域"

epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
```

**获取凭据：**
- 在 https://azure.microsoft.com 创建 Azure 账户
- 在 Azure 门户中创建语音服务资源
- 从仪表板获取订阅密钥和区域

**可用语音：**
- 语音列表：https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/language-support?tabs=tts#voice-styles-and-roles
- 语音库（试听）：https://speech.microsoft.com/portal/voicegallery

### 选项 2：使用豆包 TTS

设置环境变量并运行：

```bash
export DOUBAO_ACCESS_TOKEN="您的访问令牌"
export DOUBAO_BASE_URL="您的 API 基础 URL"

epub2speech input.epub output.m4b --voice zh_male_lengkugege_emo_v2_mars_bigtts
```

**获取凭据：**
- 从火山引擎控制台获取豆包访问令牌和 API 基础 URL

**可用语音：** https://www.volcengine.com/docs/6561/1257544?lang=zh
_（在豆包 TTS 文档中查找语音 ID）_

### 选项 3：使用 Qwen TTS

设置环境变量并运行：

```bash
export QWEN_ACCESS_TOKEN="您的访问令牌"
export QWEN_BASE_URL="您的 API 基础 URL"

epub2speech input.epub output.m4b --provider qwen --voice Cherry
```

**获取凭据：**
- 使用您的 fusion-api 访问令牌
- `QWEN_BASE_URL` 指向 `action/generate` 上一级服务地址

**可用语音：** 参考您部署的 Qwen TTS 服务配置

### 提供商自动检测

如果您只配置了一个提供商，它将被自动检测和使用。如果配置了多个提供商，请指定要使用的提供商：

```bash
# 显式使用 Azure
epub2speech input.epub output.m4b --provider azure --voice zh-CN-XiaoxiaoNeural

# 显式使用豆包
epub2speech input.epub output.m4b --provider doubao --voice zh_male_lengkugege_emo_v2_mars_bigtts

# 显式使用 Qwen
epub2speech input.epub output.m4b --provider qwen --voice Cherry
```

## 高级选项

### 通用选项

```bash
# 限制前 5 个章节
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --max-chapters 5

# 使用自定义工作目录
epub2speech input.epub output.m4b --voice zh-CN-YunxiNeural --workspace /tmp/my-workspace

# 安静模式（无进度输出）
epub2speech input.epub output.m4b --voice ja-JP-NanamiNeural --quiet

# 设置每个 TTS 分段的最大字符数（默认：500）
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --max-tts-segment-chars 800

# 使用更保守的清洗策略（尽量保留短文本）
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --cleaning-strictness conservative

# 在工作目录输出每章清洗报告
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --dump-cleaning-report
```

### Azure TTS 配置

通过命令行参数传递凭据：

```bash
epub2speech input.epub output.m4b \
  --voice zh-CN-XiaoxiaoNeural \
  --azure-key YOUR_KEY \
  --azure-region YOUR_REGION
```

### 豆包 TTS 配置

通过命令行参数传递凭据：

```bash
epub2speech input.epub output.m4b \
  --voice zh_male_lengkugege_emo_v2_mars_bigtts \
  --doubao-token YOUR_TOKEN \
  --doubao-url YOUR_BASE_URL
```

### Qwen TTS 配置

通过命令行参数传递凭据：

```bash
epub2speech input.epub output.m4b \
  --provider qwen \
  --voice Cherry \
  --qwen-token YOUR_TOKEN \
  --qwen-url YOUR_BASE_URL
```

## 工作原理

1. **EPUB 解析**: 从 EPUB 文件中提取文本内容和元数据
2. **章节检测**: 使用 EPUB 导航数据识别章节
3. **文本处理**: 清理和分割文本以实现最佳语音合成
4. **音频生成**: 使用您选择的 TTS 提供商将文本转换为语音
5. **M4B 创建**: 将音频文件与章节元数据组合成 M4B 格式

## 开发

### 作为库使用

您可以将 epub2speech 集成到自己的 Python 应用程序中：

```python
from pathlib import Path
from epub2speech import convert_epub_to_m4b, ConversionProgress
from epub2speech.tts.azure_provider import AzureTextToSpeech
# 或使用：from epub2speech.tts.doubao_provider import DoubaoTextToSpeech
# 或使用：from epub2speech.tts.qwen_provider import QwenTextToSpeech

# 初始化 TTS 提供商
tts = AzureTextToSpeech(
    subscription_key="your-key",
    region="your-region"
)

# 可选：定义进度回调
def on_progress(progress: ConversionProgress):
    print(f"{progress.progress:.1f}% - 章节 {progress.current_chapter}/{progress.total_chapters}")

# 转换 EPUB 到 M4B
result = convert_epub_to_m4b(
    epub_path=Path("input.epub"),
    workspace=Path("./workspace"),
    output_path=Path("output.m4b"),
    tts_protocol=tts,
    voice="zh-CN-XiaoxiaoNeural",
    max_chapters=None,  # 可选：限制章节数
    max_tts_segment_chars=500,  # 可选：每个 TTS 分段的最大字符数（默认：500）
    cleaning_strictness="balanced",  # 可选：conservative / balanced / aggressive
    dump_cleaning_report=False,  # 可选：每章输出 cleaning_report.json
    progress_callback=on_progress  # 可选
)

if result:
    print(f"成功：{result}")
```

### 运行测试

```bash
python test.py
```

运行特定测试模块：

```bash
python test.py --test test_epub_picker
python test.py --test test_tts
```

## 贡献

欢迎贡献！请随时提交问题或拉取请求。

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件。

## 致谢

- [ebooklib](https://github.com/aerkalov/ebooklib) 用于 EPUB 解析
- [FFmpeg](https://ffmpeg.org/) 用于音频处理
- [spaCy](https://spacy.io/) 用于自然语言处理

## 支持

如有问题和疑问：
1. 检查现有的 GitHub 问题
2. 创建新问题并提供详细信息
3. 如相关，请包含 EPUB 文件样本（确保无版权限制）
