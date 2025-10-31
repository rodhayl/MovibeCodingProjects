# MovibeCodingProjects

## 🎯 Repository Purpose

This repository serves as a centralized hub for all my personal "vibe coding" projects - experimental, proof-of-concept (POC), and minimum viable product (MVP) applications built for learning, exploration, and rapid prototyping.

## ⚠️ General Disclaimer

**All projects in this repository are experimental in nature.** They are built as learning exercises and rapid prototypes, focusing on exploration and iteration rather than production-grade code. Expect:

- 🧪 Experimental features and implementations
- 🔬 POC/MVP-level code quality
- 🚀 Fast iteration over perfect architecture
- 🎨 Creative solutions and "vibe coding" approaches
- ⚡ Learning-focused development

**Use any code from this repository at your own risk!**

---

## 📁 Repository Structure

Each subdirectory contains a self-contained project with its own:
- README with project-specific details
- Dependencies and requirements
- Configuration files
- Project-specific .gitignore

```
MovibeCodingProjects/
├── PDFUtils/              # PDF manipulation and OCR utilities
├── YTVideoDownloader/     # YouTube and multi-platform video downloader
├── [Future Project 1]/    # Coming soon...
└── ...
```

---

## 🚀 Current Projects

### [PDFUtils](./PDFUtils)

A cross-platform desktop application for PDF manipulation with advanced OCR capabilities.

**Key Features:**
- Core operations: Merge, split, compress, extract pages
- Advanced OCR with preprocessing (Tesseract, Kraken)
- Table extraction (Camelot, pdfplumber)
- Barcode/QR code detection
- Zonal OCR for region-based text extraction
- Handwriting recognition
- Modern Tkinter GUI with ttkbootstrap support

**Technologies:** Python, Tkinter, pypdf, PyMuPDF, Tesseract, pytest

**Status:** ✅ Feature-complete with comprehensive test coverage

[**👉 View PDFUtils README**](./PDFUtils/README.md)

---

### [YTVideoDownloader](./YTVideoDownloader)

A cross-platform GUI application for downloading videos from YouTube, Vimeo, and many other platforms with advanced cookie management.

**Key Features:**
- Multi-platform support (YouTube, Vimeo, and more)
- Full playlist download with video selection
- Real-time video info fetching and format selection
- Manual audio-video format mixing
- Automated cookie management for YouTube authentication
- Browser cookie extraction (Chrome, Firefox, Edge, Safari)
- Bundled FFmpeg for seamless video/audio merging
- Progress tracking with visual feedback
- Custom output directory selection

**Technologies:** Python, CustomTkinter, yt-dlp, FFmpeg, pytest

**Status:** ✅ Feature-complete with automated cookie handling

**Distribution:** Pre-built executable available at `dist/VideoDownloader.exe`

[**👉 View YTVideoDownloader README**](./YTVideoDownloader/README.md)

---

## 🛠️ Development Philosophy

This repository embraces a **"vibe coding"** approach:

1. **Learn by Doing**: Build projects to explore new technologies and concepts
2. **Rapid Prototyping**: Focus on getting ideas working quickly
3. **Iterative Improvement**: Refine through usage and feedback
4. **Open Experimentation**: Try unconventional approaches and learn from failures
5. **Documentation as Discovery**: Write docs while learning, not after perfecting

---

## 📋 Project Guidelines

Each project in this repository should:

- ✅ Be self-contained with minimal cross-dependencies
- ✅ Include a comprehensive README
- ✅ Have clear installation and usage instructions
- ✅ List all dependencies explicitly
- ✅ Include a disclaimer about its experimental nature
- ✅ Follow basic version control practices

---

## 🎓 Learning Areas

This repository serves as a playground for exploring:

- Desktop application development (GUI frameworks: Tkinter, CustomTkinter)
- Document processing and manipulation
- OCR and computer vision
- Media downloading and processing (video/audio)
- Web scraping and authentication management
- Data extraction and transformation
- Testing strategies and test-driven development
- Packaging and distribution (PyInstaller, executables)
- Cross-platform compatibility
- Modern Python development practices

---

## 🤝 Contributing

While these are personal learning projects, suggestions and feedback are welcome! Feel free to:

- Open issues for bugs or ideas
- Submit PRs for improvements
- Share your experiences using the projects
- Suggest new project ideas for exploration

---

## 📜 License

Unless otherwise specified in individual projects, all code in this repository is released under the **MIT License**. See individual project directories for specific licensing information.

Third-party dependencies maintain their original licenses.

---

## 🔮 Future Projects

This repository will grow as I explore new ideas and technologies. Potential areas of interest:

- Web scraping and automation utilities
- Data visualization and analysis tools
- API integrations and wrappers
- CLI productivity tools
- Machine learning experiments
- Media processing utilities
- And whatever sparks curiosity!

---

## 📫 Contact & Feedback

This is a personal learning repository, but I'm always open to discussions about the projects, technologies used, or new ideas to explore.

**Remember:** This is a space for experimentation, learning, and having fun with code! 🎉

---

*Last updated: October 2025*
