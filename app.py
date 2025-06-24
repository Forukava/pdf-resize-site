
from flask import Flask, request, send_file, render_template_string
import fitz  # PyMuPDF
import io
import subprocess
import tempfile
import os

app = Flask(__name__)

HTML_FORM = """<!DOCTYPE html>
<html>
<head>
  <title>Resize and Compress PDF</title>
</head>
<body>
  <h2>Upload PDF to Resize and Compress</h2>
  <form action="/resize" method="post" enctype="multipart/form-data">
    <input type="file" name="pdf" accept="application/pdf" required><br>
    Resize scale (e.g., 0.5 for 50%): <input type="text" name="zoom" value="0.5"><br>
    Compression:
    <select name="compression">
      <option value="none">None</option>
      <option value="/screen">Low (Screen)</option>
      <option value="/ebook">Medium (eBook)</option>
      <option value="/printer">High (Printer)</option>
    </select><br>
    <button type="submit">Resize PDF</button>
  </form>
</body>
</html>"""


def compress_pdf(input_bytes, quality="/screen"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as input_file:
        input_file.write(input_bytes)
        input_path = input_file.name

    output_path = input_path.replace(".pdf", "_compressed.pdf")

    try:
        subprocess.run([
            "gs", "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={quality}",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path
        ], check=True)
        with open(output_path, "rb") as f:
            return f.read()
    finally:
        os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_FORM)


@app.route("/resize", methods=["POST"])
def resize_pdf():
    try:
        if 'pdf' not in request.files:
            return "No PDF file part", 400

        uploaded_file = request.files['pdf']
        if uploaded_file.filename == '':
            return "No selected file", 400

        try:
            zoom_factor = float(request.form.get('zoom', 0.5))
        except ValueError:
            return "Zoom must be a number", 400

        compression = request.form.get('compression', 'none')

        # Resize with PyMuPDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        output_pdf = fitz.open()

        for page in doc:
            rect = page.rect
            new_width = rect.width * zoom_factor
            new_height = rect.height * zoom_factor
            new_page = output_pdf.new_page(width=new_width, height=new_height)
            new_page.show_pdf_page(new_page.rect, doc, page.number)

        output = io.BytesIO()
        output_pdf.save(output)
        output.seek(0)
        pdf_data = output.read()

        # Apply compression if selected
        if compression != "none":
            pdf_data = compress_pdf(pdf_data, quality=compression)

        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name="resized.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
