# AI Photo Deduplicator

English | [中文](./README.md)

AI-powered photo deduplication tool based on perceptual hashing and deep learning.

## Features

- 🖼️ **Multiple Algorithms**: pHash, dHash, aHash, ResNet/VGG
- 📁 **Batch Processing**: Multi-threaded scanning
- 🎯 **Smart Matching**: Adjustable similarity threshold
- 🖥️ **User Friendly**: Streamlit web UI

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run GUI
streamlit run ui/app.py

# CLI usage
python -m photo_dedup scan /path/to/photos
```

## License

MIT
