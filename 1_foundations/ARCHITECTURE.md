# Career Assistant AI Agent - Architecture Documentation

## System Overview

The Career Assistant AI Agent is a multi-agent system designed to handle professional communications with potential employers autonomously while maintaining quality and safety standards.

## Architecture Components

### 1. Primary Career Agent
**Technology**: Groq API with Llama 3.3 70B model

**Responsibilities**:
- Receive and process employer messages
- Generate professional responses based on CV/profile context
- Execute appropriate tools (scheduling, recording, declining)
- Maintain professional tone and stay in character

**Key Features**:
- Context-aware responses using CV and LinkedIn data
- Tool calling for actions (schedule interviews, record contacts)
- Professional tone calibration
- Iterative refinement based on evaluator feedback

### 2. Response Evaluator Agent (Critic/Judge)
**Technology**: Groq API with Llama 3.3 70B model (separate instance)

**Responsibilities**:
- Evaluate generated responses before sending
- Score responses on 5 criteria (0-10 scale each)
- Trigger revisions for low-quality responses
- Prevent hallucinations and false claims

**Evaluation Criteria**:
1. **Professional Tone** (0-10): Appropriate business communication style
2. **Clarity** (0-10): Clear and understandable message
3. **Completeness** (0-10): Fully addresses employer's questions
4. **Safety** (0-10): No false claims, hallucinations, or inappropriate commitments
5. **Relevance** (0-10): On-topic and contextually appropriate

**Threshold**: Overall score must be ≥ 7.5/10 to pass

**Auto-Revision**: Up to 2 automatic revision attempts if score < 7.5

### 3. Notification System
**Technology**: Pushover API

**Notification Types**:

| Event | Priority | Description |
|-------|----------|-------------|
| New Employer Message | High (1) | Alert when employer message arrives |
| Response Sent | Normal (0) | Confirmation when response approved and sent |
| Human Intervention | Emergency (2) | Critical alert for unknown questions or safety issues |

**Mobile Integration**:
- Real-time push notifications to mobile device
- Includes message preview and context
- Enables quick human review when needed

### 4. Unknown Question Detection System

**Triggers for Human Intervention**:
- Salary negotiation questions
- Legal/contract terms (non-compete, IP assignment)
- Deep technical questions outside CV scope
- Low confidence score from agent (< 0.5)
- Ambiguous or unusual requests

**Tool**: `record_unknown_question(question, confidence_score)`
- Logs question to file
- Triggers emergency notification
- Flags for human review

## System Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    EMPLOYER MESSAGE ARRIVES                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          📱 NOTIFICATION: New Message from Employer          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│   🤖 CAREER AGENT: Generate Response                        │
│   - Load CV/LinkedIn context                                 │
│   - Generate professional response                           │
│   - Execute tools if needed (schedule, record, etc.)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│   🔍 EVALUATOR AGENT: Critique Response                     │
│   - Score on 5 criteria (0-10 each)                          │
│   - Calculate overall score                                  │
│   - Check for safety issues                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  Score >= 7.5?
                  ┌────┴────┐
                 NO         YES
                  │           │
                  ▼           ▼
    ┌───────────────────┐   ┌───────────────────┐
    │ REVISION LOOP     │   │ ✅ APPROVED       │
    │ (Max 2 attempts)  │   │                   │
    │ - Incorporate     │   │ 📱 NOTIFICATION:  │
    │   feedback        │   │ Response Sent     │
    │ - Re-evaluate     │   │                   │
    └─────┬─────────────┘   └───────────────────┘
          │
          ▼
    Still failing?
          │
          ▼
    ┌───────────────────┐
    │ 🚨 HUMAN          │
    │ INTERVENTION      │
    │ - Emergency alert │
    │ - Log issue       │
    └───────────────────┘
```

## Tool System

### Available Tools

#### 1. `record_employer_contact`
Records employer information for follow-up
```json
{
  "email": "employer@company.com",
  "company": "Company Name",
  "name": "Employer Name",
  "role": "Their Position"
}
```

#### 2. `schedule_interview`
Accepts and logs interview invitations
```json
{
  "date": "2026-03-03",
  "time": "2:00 PM EST",
  "format_type": "video/phone/in-person",
  "interviewer": "Interviewer Name"
}
```

#### 3. `decline_offer`
Politely declines job offers
```json
{
  "company": "Company Name",
  "reason": "pursuing other opportunities"
}
```

#### 4. `record_unknown_question`
Flags questions requiring human review
```json
{
  "question": "The question text",
  "confidence_score": 0.3
}
```

## Data Flow

### Input Processing
1. Employer message received
2. System prompt includes CV + LinkedIn context
3. Message processed by Career Agent with tool access

### Response Generation
1. Career Agent generates draft response
2. Tools executed if needed (e.g., schedule_interview)
3. Draft sent to Evaluator Agent

### Quality Assurance
1. Evaluator scores response on 5 criteria
2. If score < 7.5: Trigger revision
3. If score ≥ 7.5: Approve for sending
4. Max 2 revision attempts

### Notification & Logging
1. All events logged to files
2. Critical events → Mobile notifications
3. Human intervention for edge cases

## Security & Safety Features

### Hallucination Prevention
- Evaluator checks claims against CV
- Safety score penalizes unverifiable statements
- Revision loop to correct issues

### Commitment Controls
- Agent instructed to NEVER commit to salary without human approval
- Legal/contract questions trigger unknown_question tool
- Explicit rules in system prompt

### Confidence Thresholds
- Low confidence (< 0.5) triggers human intervention
- Unknown topic detection
- Out-of-scope question handling

## Configuration

### Environment Variables Required
```bash
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### File Structure
```
1_foundations/
├── career_assistant.py       # Main system implementation
├── test_career_assistant.py  # Test suite (3 test cases)
├── ARCHITECTURE.md           # This file
├── README_CAREER.md          # User guide
├── me/
│   ├── summary.txt           # CV/profile summary
│   └── linkedin.pdf          # LinkedIn export (optional)
├── employer_contacts.log     # Logged employer contacts
├── interviews.log            # Scheduled interviews
├── declined_offers.log       # Declined offers
└── unknown_questions.log     # Questions requiring review
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Provider | Groq API | Fast inference for Llama models |
| Model | Llama 3.3 70B Versatile | High-quality text generation |
| Notifications | Pushover API | Mobile push notifications |
| UI | Gradio | Interactive testing interface |
| Language | Python 3.8+ | Core implementation |
| Tools | Function Calling | Agent actions and integrations |

## Performance Characteristics

- **Response Time**: 2-5 seconds per generation
- **Evaluation Time**: 1-3 seconds per evaluation
- **Revision Cycles**: 0-2 automatic revisions
- **Total Processing**: 5-15 seconds typical
- **Notification Latency**: < 1 second

## Failure Modes & Handling

### 1. Low Quality Response
- **Detection**: Evaluator score < 7.5
- **Action**: Auto-revision (up to 2 attempts)
- **Escalation**: Human review if still failing

### 2. Unknown Question
- **Detection**: Agent uncertainty or topic mismatch
- **Action**: Trigger `record_unknown_question` tool
- **Notification**: Emergency alert to human

### 3. API Failure
- **Detection**: Groq API timeout or error
- **Action**: Graceful error message
- **Fallback**: Log and notify for manual handling

### 4. Safety Violation
- **Detection**: Evaluator safety score < 7
- **Action**: Force revision
- **Escalation**: Human review required

## Extension Points

### Future Enhancements
1. **RAG Integration**: Vector database for CV context
2. **Multi-Language Support**: Translate employer messages
3. **Calendar Integration**: Auto-schedule interviews
4. **Email Integration**: Auto-send responses via SMTP
5. **Database Backend**: PostgreSQL for persistent storage
6. **Analytics Dashboard**: Track response quality over time
7. **A/B Testing**: Compare response strategies
8. **Learning Loop**: Fine-tune on successful responses

## Testing Strategy

### Required Test Cases
1. **Standard Interview Invitation**
   - Expected: Professional acceptance, high score, notification sent
   
2. **Technical Question**
   - Expected: CV-based answer, no false claims, high safety score
   
3. **Unknown/Unsafe Question**
   - Expected: Trigger unknown_question tool, human intervention

### Test Execution
```bash
python test_career_assistant.py
```

### Success Criteria
- All 3 test cases pass
- Evaluation scores ≥ 7.5 for appropriate cases
- Tools triggered correctly
- Notifications sent
- No hallucinations or false claims

## Deployment Considerations

### Development
```bash
# Install dependencies
pip install groq gradio pypdf requests python-dotenv

# Set environment variables
export GROQ_API_KEY="your_groq_api_key_here"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"

# Run development UI
python career_assistant.py
```

### Production
1. Deploy on cloud platform (AWS/GCP/Azure)
2. Use environment variables for secrets
3. Set up monitoring and logging
4. Configure email integration
5. Add authentication for UI
6. Implement rate limiting
7. Set up database for persistence

## Conclusion

This architecture provides a robust, safe, and efficient career communication system that:
- ✅ Automates employer responses professionally
- ✅ Maintains quality through multi-agent evaluation
- ✅ Ensures safety with hallucination prevention
- ✅ Enables human oversight via notifications
- ✅ Handles edge cases gracefully
- ✅ Scales for production use
