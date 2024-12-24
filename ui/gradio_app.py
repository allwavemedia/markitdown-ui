# mypy: disable-error-code="import"
"""MarkItDown Gradio Application Interface Module."""

import os
import tempfile
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional, List, Tuple, TypeVar, cast

import requests  # type: ignore[import]
import gradio as gr
from markitdown import MarkItDown


# Type variable for file-like objects
F = TypeVar('F', bound=gr.File)


def get_save_path(original_name: str) -> str:
    """Open save file dialog with suggested name."""
    # Create and configure root window
    root = tk.Tk()
    root.withdraw()  # Hide main window
    root.wm_attributes('-topmost', 1)  # Keep dialog on top
    root.focus_force()  # Force focus
    
    try:
        # Get base name without extension
        base_name = os.path.splitext(original_name)[0]
        suggested_name = f"{base_name}.md"
        
        # Show save file dialog
        save_path = filedialog.asksaveasfilename(
            title='Save Markdown File As',
            initialdir=str(Path.home() / "Documents"),
            initialfile=suggested_name,
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md")]
        )
        
        return save_path if save_path else ""
    finally:
        # Clean up
        root.quit()
        root.destroy()


def download_url_content(url: str) -> str:
    """Download content from URL and save to temporary file."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to download URL: {str(e)}") from e

    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
        tmp.write(response.content)
        return tmp.name


def preview_file(
    files: Optional[List[F]]
) -> str:
    """Generate a preview of the file content."""
    if not files or not files[0]:
        return "No file selected"

    try:
        # Preview the first selected file
        file_obj = cast(gr.File, files[0])
        file_path = (
            file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        )
        ext = os.path.splitext(file_path)[1].lower()
        
        supported_types = {
            '.pdf', '.docx', '.pptx', '.xlsx', '.jpg', '.jpeg',
            '.png', '.html', '.csv', '.json', '.xml', '.zip'
        }
        if ext not in supported_types:
            return (
                f"Unsupported file type: {ext}. "
                "Please upload one of the supported formats."
            )

        # Initialize MarkItDown
        md = MarkItDown()
        result = md.convert(file_path)
        
        # Show longer preview with word count
        preview_length = 1000
        text = result.text_content
        word_count = len(text.split())
        preview_text = (
            f"{text[:preview_length]}...\n\n"
            f"[Preview: {word_count:,} words total]"
            if len(text) > preview_length
            else text
        )
        return preview_text
    except (IOError, ValueError) as e:
        return (
            f"Preview error: {str(e)}\n"
            "Please check if the file is valid and not corrupted."
        )


def _validate_files(files: List[F]) -> Optional[Tuple[str, None]]:
    """Validate uploaded files and return error message if invalid."""
    if not files:
        return "Please upload a file to convert.", None
    
    supported_types = {
        '.pdf', '.docx', '.pptx', '.xlsx', '.jpg', '.jpeg',
        '.png', '.html', '.csv', '.json', '.xml', '.zip'
    }
    for file in files:
        file_obj = cast(gr.File, file)
        file_path = (
            file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        )
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in supported_types:
            return (
                f"Error: {ext} files not supported. "
                "Please check supported formats."
            ), None
    return None


def convert_files(
    files: List[F],
    progress: Optional[gr.Progress] = None
) -> Tuple[str, Optional[str]]:
    """
    Convert uploaded files to markdown with progress tracking.
    """
    validation_error = _validate_files(files)
    if validation_error:
        return validation_error
    
    # Initialize MarkItDown
    md = MarkItDown()
    results = []
    total_files = len(files)

    # Initialize progress tracking
    for i, file in enumerate(files):
        file_obj = cast(gr.File, file)
        file_path = (
            file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        )
        
        if progress:
            progress(
                i / total_files,
                desc=f"Converting {os.path.basename(file_path)}"
            )

        try:
            result = md.convert(file_path)
            
            # Get save path from user
            save_path = get_save_path(os.path.basename(file_path))
            if not save_path:
                results.append(
                    f"✗ Skipped {os.path.basename(file_path)} - "
                    "No save location selected"
                )
                continue

            # Create output directory if needed
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save the converted file
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(result.text_content)

            # Add file size information to the success message
            file_size = os.path.getsize(save_path)
            size_mb = file_size / (1024 * 1024)
            results.append(
                f"✓ Converted {os.path.basename(file_path)}\n"
                f"Size: {size_mb:.1f} MB\n"
                f"Saved as: {save_path}"
            )
        except (IOError, ValueError) as e:
            results.append(
                f"✗ Error: {os.path.basename(file_path)} - {str(e)}"
            )

    if progress:
        progress(1.0)
    final_result = "\n".join(results)
    return final_result, "100%"


def convert_url(
    url: str,
    progress: Optional[gr.Progress] = None
) -> Tuple[str, Optional[str]]:
    """Convert webpage content to markdown."""
    if not url:
        return "Please enter a valid URL.", None

    if progress:
        progress(0.2, desc="Downloading webpage content")
    try:
        temp_file = download_url_content(url)
        if progress:
            progress(0.6, desc="Converting to markdown")

        # Initialize MarkItDown
        md = MarkItDown()
        result = md.convert(temp_file)

        # Get save path from user
        url_filename = url.split('/')[-1] or 'webpage'
        save_path = get_save_path(url_filename)
        if not save_path:
            return "Conversion cancelled - No save location selected", None

        # Create output directory if needed
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save the converted file
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(result.text_content)

        os.unlink(temp_file)  # Clean up temporary file
        if progress:
            progress(1.0)
        return f"Successfully converted {url} to {save_path}", "100%"
    except (IOError, ValueError, requests.RequestException) as e:
        return f"Error converting URL: {str(e)}", None


def create_interface() -> gr.Blocks:
    """Create and configure the Gradio interface."""
    with gr.Blocks(
        title="MarkItDown Converter",
        theme=gr.themes.Soft()
    ) as app:
        gr.Markdown("# 📝 MarkItDown Converter")
        gr.Markdown(
            "Convert various file formats to Markdown or "
            "convert webpage content."
        )

        with gr.Tabs():
            with gr.TabItem("📁 File Conversion"):
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### 📤 Upload Files to Convert")
                        gr.Markdown(
                            "1. Drag and drop files or click to select\n"
                            "2. Preview the conversion\n"
                            "3. Click Convert and choose where to save\n\n"
                            "Supports PDF, Word, Excel, images, and more."
                        )
                        # File upload component
                        files = gr.File(  # type: ignore[no-any-return]
                            file_count="multiple",
                            label="",  # Label shown in markdown above
                            file_types=[
                                ".pdf", ".docx", ".pptx", ".xlsx",
                                ".jpg", ".jpeg", ".png", ".html",
                                ".csv", ".json", ".xml", ".zip"
                            ],
                            height=200,  # Make drop zone more prominent
                        )
                        # Preview component
                        preview = gr.Textbox(
                            label="Content Preview",
                            placeholder=(
                                "Preview of converted markdown content...\n"
                                "Check content before converting."
                            ),
                            lines=10,
                            interactive=False
                        )
                        # Check for preview handler
                        has_change = hasattr(files, 'change')
                        if has_change:
                            files.change(  # type: ignore[attr-defined]
                                fn=preview_file,
                                inputs=[files],
                                outputs=[preview]
                            )

                    with gr.Column(scale=1):
                        gr.Markdown("### 🔄 Convert & Save")
                        gr.Markdown(
                            "Click Convert to choose save location.\n"
                            "Original filename will be suggested."
                        )
                        progress_bar = gr.Textbox(
                            label="Conversion Status",
                            value="Ready to convert...",
                            interactive=False
                        )
                        # Convert button
                        convert_btn = gr.Button(
                            "🔄 Convert to Markdown",
                            variant="primary",
                            size="lg",  # Make button larger
                            # type: ignore[no-any-return]
                            elem_id="convert_btn"
                        )

                # Results display
                result = gr.Textbox(
                    label="Conversion Results",
                    placeholder="Conversion results will appear here...",
                    lines=5,
                    interactive=False
                )

                # Handle file conversion
                if hasattr(convert_btn, 'click'):
                    convert_btn.click(  # type: ignore[attr-defined]
                        fn=convert_files,
                        inputs=[files],
                        outputs=[result, progress_bar]
                    )

            with gr.TabItem("🌐 URL Conversion"):
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### 🌐 Enter URL to Convert")
                        gr.Markdown(
                            "1. Enter webpage URL\n"
                            "2. Click Convert and choose where to save\n"
                            "3. URL filename will be suggested"
                        )
                        # URL input
                        url = gr.Textbox(
                            label="",  # Label shown in markdown above
                            placeholder="Enter URL to convert..."
                        )
                    with gr.Column(scale=1):
                        gr.Markdown("### 🔄 Convert")
                        url_progress_bar = gr.Textbox(
                            label="Conversion Status",
                            value="Ready to convert...",
                            interactive=False
                        )
                        # Convert button
                        url_convert_btn = gr.Button(
                            "🔄 Convert to Markdown",
                            variant="primary",
                            size="lg",  # Make button larger
                            # type: ignore[no-any-return]
                            elem_id="url_btn"
                        )

                # Results display
                url_result = gr.Textbox(
                    label="Conversion Results",
                    placeholder="Conversion results will appear here...",
                    lines=5,
                    interactive=False
                )

                # Handle URL conversion
                if hasattr(url_convert_btn, 'click'):
                    url_convert_btn.click(  # type: ignore[attr-defined]
                        fn=convert_url,
                        inputs=[url],
                        outputs=[url_result, url_progress_bar]
                    )

        gr.Markdown("""
        ### Supported File Types
        - Documents: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx)
        - Images: JPG, PNG (with EXIF metadata and OCR)
        - Web: HTML files and URLs
        - Data: CSV, JSON, XML
        - Archives: ZIP (processes contained files)
        """)

    return app


if __name__ == "__main__":
    interface = create_interface()
    interface.launch()
