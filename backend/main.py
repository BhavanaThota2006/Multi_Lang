# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel #data validation
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from contextlib import asynccontextmanager

class TranslateRequest(BaseModel):
    source: str    # e.g. "en"
    target: str    # e.g. "hi"
    text: str
    max_length: int = 512

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    global device, tokenizer, model, supported_langs
    device = "cuda" if torch.cuda.is_available() else "cpu"
    MODEL_NAME = "facebook/m2m100_1.2B"

    print(f"🔄 Loading model {MODEL_NAME} on {device} ...")
    tokenizer = M2M100Tokenizer.from_pretrained(MODEL_NAME)
    model = M2M100ForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)

    # Get all supported language codes
    all_langs = list(tokenizer.lang_code_to_id.keys())

    # Restrict to major Asian languages only
    asian_langs = [
        "en",  # English (as intermediary)
        "hi",  # Hindi
        "ta",  # Tamil
        "te",  # Telugu
        "ml",  # Malayalam
        "bn",  # Bengali
        "ur",  # Urdu
        "gu",  # Gujarati
        "pa",  # Punjabi
        "si",  # Sinhala
        "ne",  # Nepali
        "zh",  # Chinese
        "ja",  # Japanese
        "ko",  # Korean
        "th",  # Thai
        "id",  # Indonesian
        "ms",  # Malay
        "vi",  # Vietnamese
        "ar",  # Arabic
        "fa",  # Persian
        "he",  # Hebrew
    ]

    # Keep only those that actually exist in the model
    supported_langs = [lang for lang in asian_langs if lang in all_langs]

    print(f"✅ Loaded. Supported Asian languages: {supported_langs}")

    yield

    # Cleanup on shutdown
    print("🛑 Shutting down... releasing model")
    del model
    del tokenizer


# Create FastAPI app
app = FastAPI(title="Asian Language Translator API", lifespan=lifespan)

# Allow frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "note": "use /languages and POST /translate"}

@app.get("/languages")
async def get_languages():
    return {"languages": supported_langs}

@app.post("/translate")
async def translate(req: TranslateRequest):
    if req.source not in supported_langs or req.target not in supported_langs:
        return {
            "error": "unsupported language code",
            "supported_languages": supported_langs
        }

    tokenizer.src_lang = req.source
    encoded = tokenizer(req.text, return_tensors="pt", padding=True).to(device)

    forced_bos_token_id = tokenizer.get_lang_id(req.target)
    generated_tokens = model.generate(
        **encoded,
        forced_bos_token_id=forced_bos_token_id,
        max_length=req.max_length,
        num_beams=5,
        early_stopping=True,
        no_repeat_ngram_size=3,
    )

    translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
    return {
        "source_lang": req.source,
        "target_lang": req.target,
        "translation": translation
    }
