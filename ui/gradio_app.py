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


def select_directory() -> str:
    """Open folder selection dialog and return chosen path."""
    # Create and configure root window
    root = tk.Tk()
    root.withdraw()  # Hide main window
    root.wm_attributes('-topmost', 1)  # Keep dialog on top
    root.focus_force()  # Force focus
    
    try:
        # Show folder selection dialog
        folder_path = filedialog.askdirectory(
            title='Select Output Directory',
            initialdir=str(Path.home() / "Documents")
        )
        
        # Return selected path or default
        if folder_path:
            return folder_path
        return str(Path.home() / "Documents")
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
    output_name: str,
    output_dir: str,
    progress: Optional[gr.Progress] = None
) -> Tuple[str, Optional[str]]:
    """
    Convert uploaded files to markdown with progress tracking.
    """
    validation_error = _validate_files(files)
    if validation_error:
        return validation_error
    
    md = MarkItDown()
    results = []
    total_files = len(files)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

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
            output_path = os.path.join(
                output_dir,
                (f"{output_name}_{i+1}.md"
                 if total_files > 1 else f"{output_name}.md")
            )

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.text_content)

            # Add file size information to the success message
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            results.append(
                f"✓ Converted {os.path.basename(file_path)}\n"
                f"Size: {size_mb:.1f} MB\n"
                f"Path: {output_path}"
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
    output_name: str,
    output_dir: str,
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

        md = MarkItDown()
        result = md.convert(temp_file)

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{output_name}.md")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.text_content)

        os.unlink(temp_file)  # Clean up temporary file
        if progress:
            progress(1.0)
        return f"Successfully converted {url} to {output_path}", "100%"
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
                        # File upload component
                        files = gr.File(  # type: ignore[no-any-return]
                            file_count="multiple",
                            label="Upload Files",
                            file_types=[
                                ".pdf", ".docx", ".pptx", ".xlsx",
                                ".jpg", ".jpeg", ".png", ".html",
                                ".csv", ".json", ".xml", ".zip"
                            ]
                        )
                        # Preview component
                        preview = gr.Textbox(
                            label="Preview",
                            placeholder="Preview...",
                            lines=5,
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
                        # Output settings
                        output_name = gr.Textbox(
                            label="Filename",
                            placeholder="Name...",
                            value="output"
                        )
                        with gr.Row():
                            output_dir = gr.Textbox(
                                label="Save To",
                                placeholder="Path...",
                                value=str(Path.home() / "Documents"),
                                scale=4
                            )
                            browse_btn = gr.Button(
                                "📂 Browse",
                                scale=1
                            )
                        progress_bar = gr.Textbox(
                            label="Status",
                            value="0%",
                            interactive=False
                        )
                        # Convert button
                        convert_btn = gr.Button(
                            "🔄 Convert",
                            variant="primary",
                            # type: ignore[no-any-return]
                            elem_id="convert_btn"
                        )

                # Results display
                result = gr.Textbox(
                    label="Results",
                    lines=5,
                    interactive=False
                )

                # Setup event handlers
                has_browse = hasattr(browse_btn, 'click')
                has_convert = hasattr(convert_btn, 'click')
                
                if has_browse:
                    browse_btn.click(
                        fn=select_directory,
                        inputs=None,
                        outputs=output_dir
                    )
                if has_convert:
                    convert_btn.click(  # type: ignore[attr-defined]
                        fn=convert_files,
                        inputs=[files, output_name, output_dir],
                        outputs=[result, progress_bar]
                    )

            with gr.TabItem("🌐 URL Conversion"):
                with gr.Row():
                    with gr.Column(scale=2):
                        # URL input
                        url = gr.Textbox(
                            label="URL",
                            placeholder="URL..."
                        )

                    with gr.Column(scale=1):
                        # Output settings
                        url_output_name = gr.Textbox(
                            label="Filename",
                            placeholder="Name...",
                            value="webpage"
                        )
                        with gr.Row():
                            url_output_dir = gr.Textbox(
                                label="Save To",
                                placeholder="Path...",
                                value=str(Path.home() / "Documents"),
                                scale=4
                            )
                            url_browse_btn = gr.Button(
                                "📂 Browse",
                                scale=1
                            )
                        url_progress_bar = gr.Textbox(
                            label="Status",
                            value="0%",
                            interactive=False
                        )
                        # Convert button
                        url_convert_btn = gr.Button(
                            "🔄 Convert",
                            variant="primary",
                            # type: ignore[no-any-return]
                            elem_id="url_btn"
                        )

                # Results display
                url_result = gr.Textbox(
                    label="Results",
                    lines=5,
                    interactive=False
                )

                # Setup event handlers
                has_url_browse = hasattr(url_browse_btn, 'click')
                has_url_convert = hasattr(url_convert_btn, 'click')
                
                if has_url_browse:
                    url_browse_btn.click(
                        fn=select_directory,
                        inputs=None,
                        outputs=url_output_dir
                    )
                if has_url_convert:
                    url_convert_btn.click(  # type: ignore[attr-defined]
                        fn=convert_url,
                        inputs=[url, url_output_name, url_output_dir],
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
