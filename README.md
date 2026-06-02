# 📄 MinerU-DocTrans: Layout-Preserving PDF Translator

An advanced, layout-preserving online PDF translation application. This tool leverages the power of **MinerU (Magic-PDF)** for deep document structure analysis and the **Baidu Translation API** for high-efficiency text translation, finally rendering a professional **Word (.docx)** document with editable formulas and embedded images.

## ✨ Key Features

- **High-Fidelity Layout Preservation**: Maintains headers, paragraphs, and list structures using MinerU's advanced PDF parsing.
- **Editable Mathematical Formulas**: Automatically converts LaTeX formulas into **Word Native Equation Objects (OMML)** via Pandoc.
- **Formula & Image Protection (ZPX Masking)**: Uses a proprietary masking strategy to prevent the translation engine from corrupting LaTeX code, images, or table structures.
- **Dual Parsing Engines**:
    - **⚡ Agent Mode**: Lightweight, fast, and token-free (supports files up to 10MB/20 pages).
    - **🎯 Pro Mode**: High-precision analysis for complex documents (supports files up to 200MB/200 pages, requires MinerU Token).
- **Batch Translation Efficiency**: Implements text-chunking to bypass API rate limits, increasing translation speed by up to 50x compared to line-by-line processing.
- **規整 Tables**: Keeps complex Markdown/HTML tables intact to prevent formatting breakage during translation.

## 🚀 Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **PDF Parsing**: [MinerU (Magic-PDF)](https://mineru.net/)
- **Translation**: [Baidu Translation Open Platform](https://fanyi-api.baidu.com/)
- **Document Rendering**: [Pandoc](https://pandoc.org/) & `pypandoc`
- **Logic**: Python 3.10

## 🛠️ Installation & Local Setup

### Prerequisites
- Python 3.10+
- **Pandoc** installed on your system (Required for Word generation).

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pdf-translator.git
   cd pdf-translator
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Pandoc**:
   - **Windows**: `winget install pandoc` or download from the official site.
   - **Mac**: `brew install pandoc`
   - **Linux**: `sudo apt-get install pandoc`

4. **Run the App**:
   ```bash
   streamlit run app.py
   ```

## ☁️ Deployment on Streamlit Cloud

When deploying to Streamlit Cloud, ensure your repository contains the following files in the root directory:

1. **`requirements.txt`**: Contains Python libraries (`streamlit`, `requests`, `pypandoc`).
2. **`packages.txt`**: Contains one line: `pandoc`. This triggers the system-level installation of the rendering engine.
3. **`runtime.txt`**: Set to `python-3.10`.

## 📖 Usage Guide

1. **Get API Keys**:
   - Obtain a `Baidu AppID` and `Secret Key` from the [Baidu Translation Portal](https://fanyi-api.baidu.com/).
   - (Optional) Obtain a `MinerU Token` from [MinerU.net](https://mineru.net/) for Pro Mode.
2. **Configure Sidebar**: Enter your API credentials and select the target language.
3. **Upload & Translate**: Upload your PDF. The system will:
   - Extract text, images, and formulas.
   - Mask sensitive technical content.
   - Translate text in optimized chunks.
   - Re-assemble and render the `.docx` file.
4. **Download**: Get your translated Word document and Markdown source.

## ⚠️ Important Notes

- **Baidu API Limits**: If using the "Standard Free Tier," the API is limited to 1 QPS. The app includes a built-in delay (`time.sleep`) to comply with this.
- **Formatting**: For best results with images, use the **Pro Mode**. The Agent mode is optimized for speed and text-only accuracy.
- **Tables**: Tables are currently kept in their original language within the translated document to ensure structural integrity.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

### Acknowledgments
- [OpenDataLab](https://opendatalab.com/) for the amazing MinerU parsing engine.
- The Pandoc community for the document conversion Swiss-Army knife.
