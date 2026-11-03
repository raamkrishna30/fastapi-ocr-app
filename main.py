from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import easyocr

app = FastAPI(title="Fast & Free OCR API")

# Initialize EasyOCR engine
reader = easyocr.Reader(['en'], gpu=False)

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OCR Studio - Modern Text Extractor</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center justify-center p-6">

        <div class="max-w-4xl w-full bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-8">
            <header class="text-center mb-8">
                <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
                    AI OCR Text Extractor
                </h1>
                <p class="text-slate-400 mt-2">Upload your image and extract clean readable text instantly</p>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <!-- Left Column: Upload Section -->
                <div class="flex flex-col items-center justify-center border-2 border-dashed border-slate-600 rounded-xl p-6 bg-slate-800/50 hover:border-blue-500 transition duration-300 relative" id="dropZone">
                    <input type="file" id="imageInput" accept="image/*" class="hidden" onchange="handleFileSelect(event)">
                    
                    <div id="uploadPrompt" class="text-center cursor-pointer" onclick="document.getElementById('imageInput').click()">
                        <i class="fa-solid fa-cloud-arrow-up text-5xl text-blue-400 mb-4"></i>
                        <p class="text-sm font-semibold text-slate-200">Click to upload or drag & drop image</p>
                        <p class="text-xs text-slate-400 mt-1">PNG, JPG, JPEG supported</p>
                    </div>

                    <img id="imagePreview" class="hidden max-h-64 rounded-lg object-contain shadow-md mb-4" alt="Uploaded Preview">
                    
                    <button id="changeBtn" onclick="document.getElementById('imageInput').click()" class="hidden text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-md text-slate-300 mb-4">
                        Change Image
                    </button>

                    <button id="extractBtn" onclick="uploadImage()" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 rounded-lg shadow-lg transition duration-200 hidden">
                        Extract Text
                    </button>
                </div>

                <!-- Right Column: Result Section -->
                <div class="flex flex-col bg-slate-900/60 border border-slate-700 rounded-xl p-6 relative">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-lg font-semibold text-slate-300">Extracted Output</h2>
                        <button onclick="copyToClipboard()" id="copyBtn" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-600 px-3 py-1.5 rounded-md flex items-center gap-1.5">
                            <i class="fa-regular fa-copy"></i> Copy
                        </button>
                    </div>

                    <div id="loader" class="hidden flex-1 flex flex-col items-center justify-center">
                        <div class="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        <p class="text-xs text-slate-400 mt-3">Processing OCR engine...</p>
                    </div>

                    <textarea id="resultText" readonly placeholder="Your extracted text will appear here..." 
                        class="w-full flex-1 bg-transparent text-slate-200 resize-none outline-none text-sm font-mono leading-relaxed placeholder-slate-600 focus:ring-0"></textarea>
                </div>
            </div>
        </div>

        <script>
            let selectedFile = null;

            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    selectedFile = file;
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const preview = document.getElementById('imagePreview');
                        preview.src = e.target.result;
                        preview.classList.remove('hidden');
                        document.getElementById('uploadPrompt').classList.add('hidden');
                        document.getElementById('changeBtn').classList.remove('hidden');
                        document.getElementById('extractBtn').classList.remove('hidden');
                    }
                    reader.readAsDataURL(file);
                }
            }

            async function uploadImage() {
                if (!selectedFile) return;

                const loader = document.getElementById('loader');
                const resultText = document.getElementById('resultText');
                const extractBtn = document.getElementById('extractBtn');

                loader.classList.remove('hidden');
                resultText.classList.add('hidden');
                extractBtn.disabled = true;
                extractBtn.classList.add('opacity-50');

                let formData = new FormData();
                formData.append("file", selectedFile);

                try {
                    let response = await fetch("/ocr", {
                        method: "POST",
                        body: formData
                    });

                    let data = await response.json();
                    resultText.value = data.extracted_text || "No text detected in image.";
                } catch (err) {
                    resultText.value = "Error processing image. Please try again.";
                } finally {
                    loader.classList.add('hidden');
                    resultText.classList.remove('hidden');
                    extractBtn.disabled = false;
                    extractBtn.classList.remove('opacity-50');
                }
            }

            function copyToClipboard() {
                const copyText = document.getElementById("resultText");
                if (copyText.value) {
                    navigator.clipboard.writeText(copyText.value);
                    const btn = document.getElementById("copyBtn");
                    btn.innerHTML = `<i class="fa-solid fa-check text-green-400"></i> Copied!`;
                    setTimeout(() => {
                        btn.innerHTML = `<i class="fa-regular fa-copy"></i> Copy`;
                    }, 2000);
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/ocr")
async def extract_text(file: UploadFile = File(...)):
    image_bytes = await file.read()
    results = reader.readtext(image_bytes, detail=0)
    extracted_text = " ".join(results)

    return {
        "filename": file.filename,
        "extracted_text": extracted_text,
        "raw_lines": results
    }