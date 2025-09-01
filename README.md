# AI-Powered Job Recommendation System

An intelligent recommendation system that matches job titles to optimal advertising packages using AI and machine learning.

## 🚀 Features

### Core Functionality
- **Smart Job Matching**: Uses OpenAI embeddings and FAISS vector similarity search
- **Multi-Parameter Input**: Job title, seniority level, and city size
- **AI Industry Categorization**: Automatic classification using GPT-3.5
- **Word Stem Matching**: Handles Swedish compound words (e.g., "redovisningsekonom" → "ekonom")
- **Cosine Similarity Scoring**: Accurate semantic similarity measurements

### Advanced Features
- **Manual Training Data**: Add corrections when AI predictions are poor
- **Branch Mismatch Warnings**: Visual alerts when industries don't align
- **Real-time System Updates**: Reload training data without restart
- **Bilingual Support**: Full Swedish/English language switching
- **Smart Fallback Logic**: Multi-tier matching (exact → stem → industry → embedding)

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI/ML**: OpenAI (embeddings + GPT-3.5), FAISS
- **Data**: Pandas, Excel integration
- **Languages**: Python 3.9+

## 📋 Requirements

```
streamlit
openai
faiss-cpu
pandas
openpyxl
```

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI API key**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Open in browser**: http://localhost:8501

## 💡 How to Use

1. **Select Language**: Choose between 🇸🇪 Svenska or 🇬🇧 English
2. **Enter Job Details**:
   - Job title (e.g., "Software Engineer", "Sjuksköterska")
   - Seniority level
   - City size
3. **View Recommendations**: Get package, channels, and budget suggestions
4. **Improve System**: Use manual training for poor matches (score < 0.8)

## 🔧 System Architecture

### Matching Logic
1. **Exact Match**: Role + seniority + city size
2. **Word Stem Match**: Swedish compound words (score: 0.85)
3. **Industry Match**: AI categorization within same industry
4. **Embedding Fallback**: Cosine similarity search

### Data Flow
```
Input → Embedding → FAISS Search → Industry Check → Recommendation
                     ↓
              Manual Training ← Low Score Alert
```

## 📊 Training Data

- **Source**: Excel file (`Träningsdata Ragnarsson.xlsx`)
- **Structure**: Role, Category, City Size, Seniority, Channels, Package, Budget
- **Dynamic**: Add new training data through the UI

## 🌍 Language Support

The system supports full bilingual operation:
- **UI Translation**: All interface elements
- **Data Mapping**: English inputs converted to Swedish database values
- **Seamless Switching**: Change language without losing functionality

## 🔮 Future Enhancements

- [ ] More languages (Norwegian, Danish)
- [ ] Advanced analytics dashboard
- [ ] A/B testing for recommendations
- [ ] API endpoints for integration
- [ ] Automated model retraining

## 📝 License

This project is proprietary software developed for job advertising optimization.

---

**Built with ❤️ using AI and modern ML techniques**
