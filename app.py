
from flask import Flask, request, send_file, render_template_string
import fitz  # PyMuPDF
import io

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
  <title>Resize PDF</title>
</head>
<body>
  <h2>Upload PDF to Resize</h2>
  <form action="/resize" method="post" enctype="multipart/form-data">
    <input type="file" name="pdf" accept="application/pdf" required><br>
    Resize scale (e.g., 0.5 for 50%): <input type="text" name="zoom" value="0.5"><br>
    <button type="submit">Resize PDF</button>
  </form>
</body>
</html>
"""

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

        # Open the original PDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        output_pdf = fitz.open()

        for page in doc:
            # Create a new PDF page with scaled dimensions
            rect = page.rect
            new_width = rect.width * zoom_factor
            new_height = rect.height * zoom_factor
            new_page = output_pdf.new_page(width=new_width, height=new_height)

            # Draw the original content scaled
            new_page.show_pdf_page(
                new_page.rect, doc, page.number
            )

        output = io.BytesIO()
        output_pdf.save(output)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name="resized.pdf", mimetype="application/pdf")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
