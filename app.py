import os
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

# Initialize Flask app
app = Flask(__name__)

# Folder to store uploaded and processed files
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
PDF_FOLDER = "pdfs"

# Ensure the directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.config["PDF_FOLDER"] = PDF_FOLDER

# Function to overlay text on an image
def add_text_to_image(image_path):
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        text = os.path.basename(image_path)

        font = ImageFont.load_default()
        width, height = img.size

        # Use textbbox() to calculate text dimensions
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        position = ((width - text_width) // 2, height - text_height - 10)
        draw.text(position, text, fill="white", font=font)

        processed_image_path = os.path.join(PROCESSED_FOLDER, "processed_" + os.path.basename(image_path))
        img.save(processed_image_path)
        return processed_image_path
    except Exception as e:
        print(f"Error in image processing: {e}")
        return None

# Function to convert an image to a PDF
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

# API endpoint to upload and process an image
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        processed_image_path = add_text_to_image(file_path)
        if not processed_image_path:
            return jsonify({"error": "Failed to process image"}), 500

        pdf_path = convert_to_pdf(processed_image_path)
        if not pdf_path:
            return jsonify({"error": "Failed to convert image to PDF"}), 500

        return jsonify({
            "message": "File processed successfully",
            "download_image": f"/download/image/{os.path.basename(processed_image_path)}",
            "download_pdf": f"/download/pdf/{os.path.basename(pdf_path)}"
        })
    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {e}"}), 500

# API endpoints to serve processed files
@app.route("/download/image/<filename>")
def download_image(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

@app.route("/download/pdf/<filename>")
def download_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

# Run Flask application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
