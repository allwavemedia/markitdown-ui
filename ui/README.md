# MarkItDown Gradio Interface

A modern, user-friendly graphical interface for converting various file formats to Markdown. This application extends the MarkItDown command-line utility with an intuitive web-based interface.

## Features

- Upload and convert multiple files simultaneously
- Convert web pages directly from URLs
- Real-time conversion progress tracking
- Live preview with word count
- Native file save dialog with smart filename suggestions
- Batch processing with detailed status updates
- Modern, intuitive interface

## Supported File Types

- Documents: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx)
- Images: JPG/JPEG, PNG (with EXIF metadata and OCR)
- Web: HTML files and direct URLs
- Data: CSV, JSON, XML
- Archives: ZIP (processes contained files)

## Installation

1. Ensure Python 3.8+ is installed:
```bash
python --version
```

2. Install required packages:
```bash
pip install markitdown gradio requests
```

## Usage

1. Start the application:
```bash
python gradio/gradio_app.py
```

2. Open your web browser to http://localhost:7860

### Converting Files
1. Click "File Conversion" tab
2. Drag and drop files or click to select
3. Preview the conversion result
4. Click "Convert to Markdown"
5. Choose save location in the dialog (original filename will be suggested)
6. Monitor progress and view results

### Converting URLs

1. Click "URL Conversion" tab
2. Enter webpage URL
3. Click "Convert to Markdown"
4. Choose save location in the dialog (URL-based filename will be suggested)
5. Monitor progress and access converted file

## Error Handling

The interface provides clear feedback for:
- Invalid file types
- Failed URL downloads
- Conversion errors
- File system issues
- Network problems

## Tips

- Preview content before converting
- Original filenames are preserved with .md extension
- Save dialog remembers last used location
- Monitor progress for large files
- Check error messages if issues occur

## Support

For issues and feature requests:
- GitHub Issues: https://github.com/microsoft/markitdown/issues
- Documentation: https://microsoft.github.io/markitdown