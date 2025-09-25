<div align=center>
  <h1>EPUB to Speech</h1>
  <p><a href="./README.md">English</a> | 中文</p>
</div>

使用 Azure 文本转语音技术将 EPUB 电子书转换为高质量的有声读物。

## 功能特点

- **📚 EPUB 支持**: 兼容 EPUB 2 和 EPUB 3 格式
- **🎙️ 高质量 TTS**: 使用 Azure 认知服务语音技术进行自然语音合成
- **🌍 多语言支持**: 通过 Azure TTS 支持多种语言和语音
- **📱 M4B 输出**: 生成带章节导航的标准 M4B 有声读物格式
- **🔧 CLI 界面**: 易于使用的命令行工具，带进度跟踪

## 基本用法

将 EPUB 文件转换为有声读物：

```bash
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --azure-key YOUR_KEY --azure-region YOUR_REGION
```

## 安装

### 前置要求

- Python 3.11 或更高版本
- FFmpeg（用于音频处理）
- Azure 语音服务凭据

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

### Azure 语音服务设置

1. 在 https://azure.microsoft.com 创建 Azure 账户
2. 在 Azure 门户中创建语音服务资源
3. 从 Azure 仪表板获取您的订阅密钥和区域

## 快速开始

### 环境变量

将 Azure 凭据设置为环境变量：

```bash
export AZURE_SPEECH_KEY="您的订阅密钥"
export AZURE_SPEECH_REGION="您的区域"

epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
```

### 高级选项

```bash
# 限制前 5 个章节
epub2speech input.epub output.m4b --voice en-US-AriaNeural --max-chapters 5

# 使用自定义工作目录
epub2speech input.epub output.m4b --voice zh-CN-YunxiNeural --workspace /tmp/my-workspace

# 安静模式（无进度输出）
epub2speech input.epub output.m4b --voice ja-JP-NanamiNeural --quiet
```

## 可用语音

完整列表请参见 [Azure 神经语音](https://docs.microsoft.com/zh-cn/azure/cognitive-services/speech-service/language-support#neural-voices)。

## 工作原理

1. **EPUB 解析**: 从 EPUB 文件中提取文本内容和元数据
2. **章节检测**: 使用 EPUB 导航数据识别章节
3. **文本处理**: 清理和分割文本以实现最佳语音合成
4. **音频生成**: 使用 Azure TTS 将文本转换为语音
5. **M4B 创建**: 将音频文件与章节元数据组合成 M4B 格式

## 开发

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

- [Azure 认知服务](https://azure.microsoft.com/services/cognitive-services/) 提供文本转语音技术
- [ebooklib](https://github.com/aerkalov/ebooklib) 用于 EPUB 解析
- [FFmpeg](https://ffmpeg.org/) 用于音频处理
- [spaCy](https://spacy.io/) 用于自然语言处理

## 支持

如有问题和疑问：
1. 检查现有的 GitHub 问题
2. 创建新问题并提供详细信息
3. 如相关，请包含 EPUB 文件样本（确保无版权限制）