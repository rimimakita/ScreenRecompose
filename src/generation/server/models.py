import os
import io
import re
import threading

import torch
from transformers import AutoProcessor, Blip2ForConditionalGeneration
from diffusers import AutoPipelineForText2Image, DDIMScheduler

CACHE_DIR = "/workspace/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

KEYWORDS = ["text", "numbers", "logo", "wall"]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.float16

caption_processor = None
caption_model = None
pipe = None
pipe_lock = threading.Lock()


def init_models():
    """caption生成モデルと画像生成モデルを読み込む。"""

    global caption_processor, caption_model, pipe

    caption_processor = AutoProcessor.from_pretrained(
        "Salesforce/blip2-opt-2.7b",
        cache_dir=CACHE_DIR,
        use_fast=False,
    )

    caption_model = Blip2ForConditionalGeneration.from_pretrained(
        "Salesforce/blip2-opt-2.7b",
        torch_dtype=dtype,
        device_map="auto",
        cache_dir=CACHE_DIR,
    ).eval()

    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=dtype,
        variant="fp16",
        use_safetensors=True,
        cache_dir=CACHE_DIR,
    ).to(device)

    pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

    with torch.no_grad():
        _ = pipe(
            prompt=["dummy"],
            height=448,
            width=448,
            num_inference_steps=1,
            guidance_scale=0.0,
        ).images


def clean_caption(caption):
    """caption内の不要または禁止したい語を置換する。"""

    text = caption

    text = re.sub(
        r"screenshot|screen\s+shot",
        "image",
        text,
        flags=re.IGNORECASE,
    )

    for keyword in KEYWORDS:
        pattern = re.compile(
            re.escape(keyword),
            flags=re.IGNORECASE,
        )
        text = pattern.sub("object", text)

    return text.strip()


def build_prompt(caption):
    """captionから画像生成用のpromptを作成する。"""

    prompt_caption = clean_caption(caption)

    return (
        f"A photo of a {prompt_caption} item on a white background, "
        f"centered, no text, no shadow, no packaging."
    )


def generate_caption(image):
    """入力画像からcaptionを生成する。"""

    with torch.no_grad():
        inputs = caption_processor(
            images=image,
            return_tensors="pt",
        ).to(device)

        generated_ids = caption_model.generate(
            **inputs,
            max_new_tokens=30,
        )

        caption = caption_processor.tokenizer.decode(
            generated_ids[0],
            skip_special_tokens=True,
        )

    return caption.strip()


def generate_images(index_caption_pairs):
    """captionのリストから生成画像を作成し、JPEG bytesに変換する。"""

    prompts = [
        build_prompt(caption)
        for _, caption in index_caption_pairs
    ]

    with pipe_lock, torch.no_grad():
        images = pipe(
            prompt=prompts,
            height=512,
            width=512,
            num_inference_steps=1,
            guidance_scale=0.0,
        ).images

    results = []

    for (rect_id, caption), image in zip(index_caption_pairs, images):
        cleaned_caption = clean_caption(caption)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        results.append(
            (rect_id, buffer.read(), cleaned_caption)
        )

    return results
