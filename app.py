
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
    uploaded_file = request.files['pdf']
    zoom_factor = float(request.form.get('zoom', 0.5))

    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    new_pdf = fitz.open()

    for page in doc:
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        pix = page.get_pixmap(matrix=mat)
        img_pdf = fitz.open("pdf", pix.tobytes("pdf"))
        new_pdf.insert_pdf(img_pdf)

    output = io.BytesIO()
    new_pdf.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="resized.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
