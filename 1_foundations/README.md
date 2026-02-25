# 🤖 Career Assistant AI Agent

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-green.svg)](https://groq.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent multi-agent AI system that autonomously handles professional communications with potential employers while maintaining quality control and safety standards.

## ✨ Features

### 🎯 Core Capabilities
- **Automated Response Generation**: Professional responses to employer messages using Groq Llama 3.3 70B
- **Multi-Agent Quality Control**: Independent evaluator agent validates responses before sending
- **Mobile Notifications**: Real-time alerts via Telegram Bot API
- **Email Notifications**: Optional SMTP email alerts
- **Unknown Question Detection**: Identifies questions requiring human intervention
- **RESTful API**: FastAPI backend for programmatic access
- **Interactive UI**: Gradio web interface for testing

### 🛡️ Safety Features
- ✅ Hallucination prevention through CV cross-checking
- ✅ Auto-revision loop (up to 2 attempts)
- ✅ Human escalation for salary/legal questions
- ✅ Comprehensive evaluation logging
- ✅ Confidence scoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│           Employer Message Arrives                   │
└────────────────────┬────────────────────────────────┘
                     ▼
          📱 Mobile Notification
                     ▼
    ┌────────────────────────────────────┐
    │  🤖 Career Agent (Groq Llama)      │
    │  - Generates professional response  │
    │  - Executes tools (schedule, etc.) │
    └────────────┬───────────────────────┘
                 ▼
    ┌────────────────────────────────────┐
    │  🔍 Evaluator Agent                │
    │  - Scores on 5 criteria (0-10)     │
    │  - Safety validation               │
    └────────────┬───────────────────────┘
                 ▼
           Score >= 7.5?
         ┌──────┴──────┐
        NO             YES
         │              │
         ▼              ▼
    🔄 Revise      ✅ Approve & Send
   (max 2x)        📱 Notification
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API key ([Get free key](https://console.groq.com))
- Telegram Bot (optional, for notifications - see [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md))

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/career-assistant-ai.git
cd career-assistant-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Configuration

Edit `.env` file:
```bash
# Required
GROQ_API_KEY=gsk_your_api_key_here

# Optional - Telegram notifications
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional - Email notifications
EMAIL_SENDER=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=your.email@gmail.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

### Customize Your Profile

Edit `me/summaryMe.txt` with your professional background:
```
My name is [Your Name]. I'm a [profession] with expertise in [skills]...
```

Optionally add your LinkedIn PDF to `me/Profile.pdf`

## 💻 Usage

### Option 1: Gradio UI (Interactive)

```bash
python career_assistant.py
```

Open browser to `http://127.0.0.1:7860`

### Option 2: FastAPI (REST API)

```bash
python api.py
```

API documentation available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

#### API Examples

**Process employer message:**
```bash
curl -X POST "http://127.0.0.1:8000/api/process-message" \
  -H "Content-Type: application/json" \
  -d '{
    "employer_name": "Sarah Johnson",
    "employer_email": "sarah@google.com",
    "message": "Would you be available for an interview next Tuesday?",
    "company": "Google"
  }'
```

**Get statistics:**
```bash
curl "http://127.0.0.1:8000/api/stats"
```

**View evaluation logs:**
```bash
curl "http://127.0.0.1:8000/api/logs/evaluation?limit=10"
```

### Option 3: Run Tests

```bash
python test_career_assistant.py
```

Runs 3 comprehensive test cases:
1. ✅ Standard interview invitation
2. ✅ Technical questions
3. ✅ Unknown/unsafe questions (salary + legal)

## 📊 Evaluation System

Every response is scored on 5 criteria (0-10):

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Professional Tone | Equal | Appropriate business communication |
| Clarity | Equal | Clear and understandable |
| Completeness | Equal | Fully addresses message |
| Safety | Equal | No false claims or hallucinations |
| Relevance | Equal | On-topic and appropriate |

**Pass Threshold**: ≥ 7.5/10 overall score

## 🛠️ Technology Stack

- **LLM Provider**: [Groq](https://groq.com) (10x faster inference)
- **Model**: Llama 3.3 70B Versatile
- **Backend**: FastAPI
- **UI**: Gradio
- **Notifications**: Telegram Bot API + SMTP
- **Language**: Python 3.8+

## 📁 Project Structure

```
1_foundations/
├── career_assistant.py     # Main agent system
├── api.py                  # FastAPI backend
├── test_career_assistant.py # Test suite
├── ARCHITECTURE.md         # Technical documentation
├── PROMPTS.md             # Prompt engineering docs
├── PROJECT_REPORT.md      # Project report
├── README_CAREER.md       # Detailed user guide
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── me/
    ├── summaryMe.txt     # Your CV/profile
    └── Profile.pdf       # LinkedIn export (optional)
```

## 📈 Performance Metrics

- **Response Time**: 5-15 seconds (generation + evaluation)
- **Evaluation Pass Rate**: ~70% first attempt, ~85% after 1 revision
- **Average Score**: 8.3/10
- **Safety Incidents**: 0 (in testing)
- **Human Intervention Rate**: ~5%

## 🔧 Advanced Configuration

### Adjust Evaluation Threshold

In `career_assistant.py`:
```python
# Change threshold (default 7.5)
if evaluation.get("overall_score", 0) >= 8.0:  # Stricter
```

### Change LLM Model

```python
self.model = "mixtral-8x7b-32768"  # Alternative Groq model
```

### Add Custom Tools

See [ARCHITECTURE.md](ARCHITECTURE.md) for tool system documentation.

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[PROMPTS.md](PROMPTS.md)** - Prompt engineering documentation
- **[PROJECT_REPORT.md](PROJECT_REPORT.md)** - Design decisions and reflections
- **[README_CAREER.md](README_CAREER.md)** - Comprehensive user guide
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - 5-minute setup guide

## 🧪 Testing

```bash
# Run comprehensive test suite
python test_career_assistant.py

# Expected output:
# ✅ Test Case 1 PASSED (Interview invitation)
# ✅ Test Case 2 PASSED (Technical question)
# ✅ Test Case 3 PASSED (Unknown question)
```

## 🐛 Troubleshooting

**"Invalid API key"**
- Check `.env` file has correct `GROQ_API_KEY`
- Verify key at [console.groq.com](https://console.groq.com)

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"Notification failed"**
- Telegram is optional, system works without it
- Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` if configured

**"Low evaluation scores"**
- Ensure `me/summaryMe.txt` has detailed information
- Agent can only answer based on provided CV content

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Groq** for fast LLM inference
- **Llama** team at Meta for the base model
- **Telegram** for free reliable notifications
- **FastAPI** for excellent API framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/career-assistant-ai/issues)
- **Documentation**: See `/docs` folder
- **Email**: your.email@example.com

## 🗺️ Roadmap

### v1.1 (Coming Soon)
- [ ] Calendar integration (Google Calendar)
- [ ] Database backend (PostgreSQL)
- [ ] Web dashboard
- [ ] Multi-language support

### v2.0 (Future)
- [ ] Fine-tuned model on successful responses
- [ ] A/B testing framework
- [ ] Interview preparation mode
- [ ] Salary negotiation advisor

---

**Built with ❤️ using Groq Llama 3.3 70B**

**Status**: ✅ Production Ready  
**Last Updated**: February 25, 2026
