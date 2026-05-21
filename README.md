# ScreenRecompose

Semantic-aware generative content replacement system for privacy protection during screen sharing.

## Overview

ScreenRecompose is a real-time privacy protection system for screen sharing environments such as online meetings.

Instead of conventional masking or blurring methods, the system replaces private regions with semantically appropriate generated content to preserve visual naturalness and contextual consistency.

The system combines:

- Object detection
- Semantic region management
- Caption generation
- Image generation
- Real-time overlay rendering

to provide visually natural obfuscation during screen sharing.

---

## Features

- Real-time screen privacy protection
- Semantic-aware content replacement
- YOLO-based private information detection
- Context-preserving image generation
- Overlay-based rendering system
- Scroll-aware region management
- Asynchronous image generation pipeline
- Cached overlay reuse for responsiveness

---

## System Architecture

```text
Screen Capture
      ↓
Object Detection (YOLOv5)
      ↓
Region Management
      ↓
Caption Generation
      ↓
Image Generation
      ↓
Overlay Rendering
      ↓
Protected Screen Output
```

---

## Project Structure

```text
ScreenRecompose/
├── src/
│   ├── detection/
│   ├── generation/
│   ├── models/
│   ├── regions/
│   ├── rendering/
│   └── main.py
│
├── data/
├── models/
├── outputs/
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Requirements

- Python 3.10+
- macOS recommended
- GPU recommended for image generation

Main libraries:

- pygame
- torch
- ultralytics
- opencv-python
- numpy
- requests
- flask

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourname/ScreenRecompose.git
cd ScreenRecompose
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running

```bash
cd src
python main.py
```

---

## Models

Place required models in the `models/` directory.

Example:

```text
models/
├── yolov5.pt
├── sdxl_turbo/
└── blip2/
```

---

## Data

Place required datasets and resources in the `data/` directory.

Example:

```text
data/
├── EOWL-v1.1.2/
└── icons/
```

---

## Notes

- Large model files are excluded from Git tracking.
- Generated outputs and cache files are ignored by `.gitignore`.
- This repository mainly contains implementation code.

---

## Research Context

This project was developed as part of research on privacy protection during screen sharing using generative AI.

The system focuses on preserving:

- viewing experience
- contextual understanding
- visual naturalness

while reducing perceived identifiability of private information.

---

## License

MIT License