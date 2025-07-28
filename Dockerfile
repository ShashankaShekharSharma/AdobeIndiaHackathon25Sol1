FROM python:3.10

WORKDIR /app

# Install required libraries
RUN pip install pymupdf

# Copy the processing script into the image
COPY pdf_parser.py .

# Set the entrypoint
CMD ["python", "pdf_parser.py"]
