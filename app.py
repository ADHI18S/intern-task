import os
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

# Initialize Flask app
app = Flask(__name__)

# Set folders for storing files
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
PDF_FOLDER = "pdfs"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.config["PDF_FOLDER"] = PDF_FOLDER

# Function to add text to an image
def add_text_to_image(image_path):
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        text = os.path.basename(image_path)  # Get the filename

        font = ImageFont.load_default()  # Use the default font
        width, height = img.size

        # Calculate text size and position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        position = ((width - text_width) // 2, height - text_height - 10)  # Center at the bottom
        draw.text(position, text, fill="white", font=font)

        # Save processed image
        processed_image_path = os.path.join(PROCESSED_FOLDER, "processed_" + os.path.basename(image_path))
        img.save(processed_image_path)
        return processed_image_path
    except Exception as e:
        print(f"Error in image processing: {e}")
        return None

# Function to convert image to PDF
def convert_to_pdf(image_path):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.image(image_path, x=10, y=10, w=180)

        pdf_filename = os.path.basename(image_path).replace(".png", ".pdf").replace(".jpg", ".pdf")
        pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
        pdf.output(pdf_path)
        return pdf_path
    except Exception as e:
        print(f"Error in PDF conversion: {e}")
        return None

# Home page (File upload form)
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded", 400

        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400

        # Save uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Process the image
        processed_image_path = add_text_to_image(file_path)
        if not processed_image_path:
            return "Failed to process image", 500

        pdf_path = convert_to_pdf(processed_image_path)
        if not pdf_path:
            return "Failed to convert image to PDF", 500

        return f"""
        <h2>Upload Successful!</h2>
        <p>Download your files:</p>
        <a href='/download/image/{os.path.basename(processed_image_path)}' target='_blank'>Download Processed Image</a><br>
        <a href='/download/pdf/{os.path.basename(pdf_path)}' target='_blank'>Download PDF</a><br>
        <a href='/'>Upload another file</a>
        """

    return '''
    <!doctype html>
    <title>Upload Image</title>
    <h1>Upload Image</h1>
    <form action="/" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <input type="submit" value="Upload">
    </form>
    '''

# Serve Processed Image & PDF
@app.route("/download/image/<filename>")
def download_image(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

@app.route("/download/pdf/<filename>")
def download_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
