# 🌾 KiSaanarthi – Voice-First Multilingual Agricultural Assistant

**An AI-powered multilingual agricultural assistant designed to make agricultural information more accessible through voice and text interaction.**

<p align="center">
  <b>English | हिंदी | मराठी</b>
</p>

---

## 📌 Project Overview

KiSaanarthi is a voice-first multilingual agricultural assistant developed to help farmers access agricultural information through a simple and interactive interface.

The application allows users to ask agricultural questions using either voice or text in English, Hindi, and Marathi. It uses speech recognition, multilingual semantic search, a curated agricultural knowledge base, and text-to-speech technology to provide relevant responses.

The system also integrates external APIs to provide weather information and agricultural mandi prices.

**Project Status:** Functional Academic Prototype

## 🎯 Objectives

- Make agricultural information accessible through voice-based interaction.
- Support multiple Indian languages.
- Provide relevant agricultural information using semantic search.
- Integrate weather and mandi price information.
- Provide information about agricultural schemes and crop management.
- Develop a simple and accessible interface for farmers.

## ✨ Key Features

### 1. 🎙️ Voice-Based Interaction
- Voice input through microphone.
- Speech-to-text conversion.
- Text-to-speech responses.
- Interactive question-and-answer system.

### 2. 🌐 Multilingual Support
Supports three languages:
- English
- Hindi
- Marathi

### 3. 🤖 Agricultural Assistant
- Agricultural question answering.
- Semantic similarity-based retrieval.
- Multilingual knowledge-base search.
- Relevant responses based on stored agricultural information.

### 4. 🌦️ Weather Information
- Search weather information by location.
- Current weather conditions.
- Temperature and humidity.
- Seven-day weather forecast.

### 5. 📊 Mandi Prices
- Agricultural commodity price information.
- State and district selection.
- Commodity selection.
- Date-based price filtering.
- Minimum, maximum and modal price information.

### 6. 📋 Government Schemes
Provides information about agricultural support schemes, including:
- PM-KISAN
- Pradhan Mantri Fasal Bima Yojana
- Kisan Credit Card
- PM Krishi Sinchai Yojana
- Soil Health Card
- e-NAM

### 7. 🌱 Crop Guidance
Provides general cultivation information for selected crops, including:
- Wheat
- Rice
- Cotton
- Soybean
- Sugarcane
- Tomato

---

## 🏗️ System Architecture

The application follows a modular architecture consisting of the following components:

1. **User Interface:** Streamlit-based interface for user interaction.
2. **Voice Input:** Captures user speech through the microphone.
3. **Speech Recognition:** Converts spoken queries into text.
4. **Language Processing:** Handles queries in the selected language.
5. **Semantic Search:** Uses Sentence Transformers to generate embeddings and identify relevant knowledge-base entries.
6. **Knowledge Base:** Stores multilingual agricultural questions, answers and source references in JSON format.
7. **External API Integration:** Retrieves weather and mandi price information.
8. **Text-to-Speech:** Converts responses into spoken audio.
9. **Response Display:** Presents relevant information through the Streamlit interface.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend / UI | Streamlit |
| Speech Recognition | SpeechRecognition |
| Voice Recording | Streamlit Mic Recorder |
| Text-to-Speech | Google Text-to-Speech (gTTS) |
| Semantic Search | Sentence Transformers |
| Embedding Model | Multilingual Sentence Transformer |
| Knowledge Base | JSON |
| Weather API | Open-Meteo |
| Mandi Price API | CEDA Agmarknet |
| Environment Configuration | Python dotenv |
| Version Control | Git and GitHub |

---

## 📂 Project Structure

```text
KiSaanarthi/
│
├── app.py
│
├── data/
│   └── knowledge_base.json
│
├── .streamlit/
│   └── config.toml
│
├── .gitignore
│
├── .env                 # Create locally; never upload
│
├── requirements.txt
│
└── README.md
```

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or later.
- Git.
- Internet connection.
- Microphone for voice interaction.

### Step 1: Clone the Repository

```bash
git clone https://github.com/yadnyeshpatilcr7-byte/KiSaanarthi.git
```

### Step 2: Navigate to the Project Directory

```bash
cd KiSaanarthi
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root directory.

Add your CEDA API key:

```env
CEDA_API_KEY=your_ceda_api_key
```

Replace the placeholder with your own API key.

**Important:** Never upload your `.env` file or API credentials to GitHub.

### Step 6: Run the Application

```bash
python -m streamlit run app.py
```

The application will open in your default browser.

---

## 🔌 API Integrations

### 1. Weather Information – Open-Meteo

Open-Meteo provides weather information and forecast data.

- Geocoding API: Converts location names into geographic coordinates.
- Forecast API: Retrieves current weather and forecast information.

Website: https://open-meteo.com/

### 2. Agricultural Mandi Prices – CEDA Agmarknet

The CEDA Agmarknet API is used to retrieve agricultural commodity price information.

The integration supports:
- Commodity selection.
- State and district selection.
- Date-based filtering.
- Market price retrieval.

Website: https://agmarknet.ceda.ashoka.edu.in/

---

## 📚 Agricultural Knowledge Base

The application uses a structured JSON knowledge base containing multilingual agricultural questions and answers.

Each record includes:
- Unique ID.
- Category.
- Language.
- Question.
- Answer.
- Source.
- Source URL.

The knowledge base includes information related to soil health, crop cultivation, irrigation, pest management, crop rotation, crop insurance and agricultural weather planning.

Agricultural information is curated with reference to institutional and official sources, including Tamil Nadu Agricultural University, Soil Health Card resources and PMFBY resources.

The knowledge base is an academic curated FAQ collection, not an official government dataset.

---

## 🔐 Security Considerations

- API keys are stored in environment variables.
- `.env` files are excluded using `.gitignore`.
- Virtual environments and Python cache files are excluded from version control.
- Users should configure their own API credentials before running the application.

---

## 🚀 Future Scope

Potential improvements include:

- Integration with additional Indian languages.
- Expansion of the agricultural knowledge base.
- Improved speech recognition for regional accents.
- Integration of additional agricultural advisory services.
- Personalized crop recommendations.
- Mobile-friendly interface.
- WhatsApp-based agricultural assistance.
- Field testing and evaluation with farmers and agricultural experts.

---

## ⚠️ Disclaimer

KiSaanarthi is an academic prototype developed for educational and demonstration purposes.

Agricultural information is intended for general guidance. Farmers should consult local agricultural experts, Krishi Vigyan Kendras or relevant agricultural institutions before making important crop management decisions.

Weather and mandi information depend on the availability and coverage of external API services.

---

## 👨‍💻 Project Repository

**GitHub:** https://github.com/yadnyeshpatilcr7-byte/KiSaanarthi

**Project Name:** KiSaanarthi – Voice-First Multilingual Agricultural Assistant

**Developed as:** Academic Project

---

## 🤝 Acknowledgements

We acknowledge the institutional agricultural resources and API providers whose information and services support this project, including:

- Tamil Nadu Agricultural University (TNAU)
- Soil Health Card Portal
- Pradhan Mantri Fasal Bima Yojana
- Open-Meteo
- CEDA Agmarknet

We also acknowledge the open-source Python libraries and tools used in developing this application.
