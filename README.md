# 🌿 Group-6 Trash Classification

An intelligent trash recognition and classification system that helps identify trash types and categories using computer vision. The application provides a user-friendly dashboard and real-time scanning capabilities.

## Features

- 📸 **Real-time Trash Scanning** - Camera and image upload support
- 🎯 **Dual Classification** - Identifies both trash type and category
- 📊 **Interactive Dashboard** - View statistics and quick scan options
- 🛒 **Eco Shop** - Browse sustainable products
- 💬 **EcoBot** - AI chatbot for recycling guidance
- 📱 **Responsive Design** - Mobile-friendly interface

## Project Structure

```
trash-classification/
├── backend/                 # FastAPI backend server
│   ├── app.py             # Main application
│   ├── app_hierarchical.py # Hierarchical classification
│   └── predict.py         # Prediction module
├── frontend/              # Next.js frontend
│   └── trash-ui/
│       ├── app/           # Main app pages
│       ├── public/        # Static assets
│       └── package.json
├── data/                  # Dataset splits
│   ├── types_split/       # Type classifier data
│   └── category_*/        # Category-specific splits
├── models/                # Pre-trained models
│   ├── type_classifier.pt
│   └── category_*.pt
└── runs/                  # Training results
```

## Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- pip and npm

### Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install fastapi uvicorn python-multipart pillow torch torchvision

# Start backend server
python backend/app.py
```

Backend runs on: `http://127.0.0.1:8000`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend/trash-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: `http://localhost:3000`

## API Endpoints

- **POST** `/predict` - Submit image for trash classification
  - Returns: `type`, `category`, `type_confidence`, `category_confidence`

## Models

- **Type Classifier**: Classifies trash into 5 main categories (Metal, Organic, Paper, Plastic, Non-Organic)
- **Category Classifiers**: Fine-grained classification within each type

### Model Files
- `models/type_classifier.pt` - Main type classification model
- `models/category_*.pt` - Category-specific models

## Training

To train models on custom data:

```bash
python train_all_categories.py
```

## Technologies Used

### Backend
- **FastAPI** - High-performance web framework
- **PyTorch** - Deep learning framework
- **Pillow** - Image processing

### Frontend
- **Next.js** - React framework
- **TypeScript** - Type-safe JavaScript
- **CSS** - Modern styling with variables and gradients
- **Tailwind** - Utility-first CSS

## Configuration

### Environment Variables

Create `.env` file in the root:
```
BACKEND_URL=http://127.0.0.1:8000
FRONTEND_URL=http://localhost:3000
```

## Development

### Code Quality
- ESLint for code linting
- TypeScript for type safety
- CSS module organization

### Folder Organization
- Modular component structure
- Separated concerns (Backend/Frontend)
- Clear data pipeline

## Performance

- **Model Size**: Optimized for fast inference
- **Frontend**: Optimized with Next.js Turbopack
- **Caching**: Browser and server-side caching enabled

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is part of the Group-6 initiative for sustainable waste management.

## Contact

For issues and questions, please refer to the project documentation.

---

**Happy Recycling! ♻️**
