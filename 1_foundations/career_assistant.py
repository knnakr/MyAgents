"""
Career Assistant AI Agent System
Uses Groq API with Llama model for intelligent career communication

Architecture:
1. Primary Career Agent - Generates professional responses to employer messages
2. Response Evaluator Agent - Critiques and validates responses before sending
3. Notification System - Alerts via Telegram Bot for new messages and responses
4. Unknown Question Detector - Identifies questions requiring human intervention
"""

from dotenv import load_dotenv
from groq import Groq
import json
import os
import requests
from pypdf import PdfReader
from datetime import datetime
from typing import Dict, List, Tuple
import gradio as gr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

load_dotenv(override=True)

# ==================== NOTIFICATION SYSTEM ====================

async def send_telegram_async(message: str, priority: str = "normal"):
    """
    Send notification via Telegram Bot (async)
    Priority: normal, high, emergency
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️  Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env)")
        return False
    
    try:
        # Lazy import to avoid dependency if not using Telegram
        from telegram import Bot
        
        bot = Bot(token=bot_token)
        
        # Format message with emoji based on priority
        emoji = "📬" if priority == "normal" else "⚡" if priority == "high" else "🚨"
        formatted_message = f"{emoji} *Career Assistant*\n\n{message}"
        
        await bot.send_message(
            chat_id=chat_id,
            text=formatted_message,
            parse_mode="Markdown"
        )
        print(f"✅ Telegram notification sent (priority: {priority})")
        return True
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def send_telegram(message: str, priority: str = "normal"):
    """
    Synchronous wrapper for Telegram notification
    Priority: normal, high, emergency
    """
    try:
        # Use asyncio.run() to handle event loop properly
        asyncio.run(send_telegram_async(message, priority))
        return True
    except Exception as e:
        print(f"❌ Telegram notification failed: {e}")
        return False

def notify_new_message(employer_name, message_preview):
    """Alert when new employer message arrives"""
    text = f"📨 *NEW EMPLOYER MESSAGE*\n\n*From:* {employer_name}\n\n*Preview:*\n{message_preview[:150]}..."
    return send_telegram(text, priority="high")

def notify_response_sent(employer_name, response_preview):
    """Alert when response is approved and sent"""
    text = f"✅ *RESPONSE SENT*\n\n*To:* {employer_name}\n\n*Response Preview:*\n{response_preview[:150]}..."
    return send_telegram(text, priority="normal")

def notify_human_intervention(reason, context):
    """Emergency alert for unknown questions or issues"""
    text = f"🚨 *HUMAN INTERVENTION NEEDED*\n\n*Reason:* {reason}\n\n*Context:*\n{context[:150]}..."
    return send_telegram(text, priority="emergency")

def send_email_notification(subject, body, to_email=None):
    """
    Send email notification via SMTP
    Optional: Set EMAIL_* env variables for email notifications
    """
    if not to_email:
        to_email = os.getenv("EMAIL_RECIPIENT")
    
    if not to_email:
        return False  # Email not configured
    
    try:
        from_email = os.getenv("EMAIL_SENDER")
        password = os.getenv("EMAIL_PASSWORD")
        smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        
        if not all([from_email, password]):
            return False
        
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def log_evaluation(employer_name, employer_message, response, evaluation, status, revision_count):
    """
    Log evaluation scores and feedback for analysis
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "employer_name": employer_name,
        "employer_message_preview": employer_message[:100],
        "response_preview": response[:100],
        "evaluation_scores": {
            "professional_tone": evaluation.get("professional_tone", 0),
            "clarity": evaluation.get("clarity", 0),
            "completeness": evaluation.get("completeness", 0),
            "safety": evaluation.get("safety", 0),
            "relevance": evaluation.get("relevance", 0),
            "overall_score": evaluation.get("overall_score", 0)
        },
        "pass": evaluation.get("pass", False),
        "feedback": evaluation.get("feedback", ""),
        "status": status,
        "revision_count": revision_count
    }
    
    with open("evaluation_logs.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return log_entry

# ==================== TOOL FUNCTIONS ====================

def record_employer_contact(email, company, name="Name not provided", role="Role not specified"):
    """Record employer contact information"""
    send_telegram(f"📧 *EMPLOYER CONTACT RECORDED*\n\n*Name:* {name}\n*Company:* {company}\n*Email:* {email}\n*Role:* {role}", priority="normal")
    # In production, save to database
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "email": email,
        "company": company,
        "name": name,
        "role": role
    }
    with open("employer_contacts.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return {"recorded": "success", "timestamp": log_entry["timestamp"]}

def record_unknown_question(question, confidence_score=0.0):
    """Record questions that require human intervention"""
    notify_human_intervention(
        reason="Unknown/Low Confidence Question",
        context=question
    )
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "confidence": confidence_score,
        "requires_review": True
    }
    with open("unknown_questions.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return {"recorded": "success", "human_review_required": True}

def schedule_interview(date, time, format_type, interviewer="Not specified"):
    """Accept and schedule interview invitations"""
    send_telegram(f"📅 *INTERVIEW SCHEDULED*\n\n*Date:* {date}\n*Time:* {time}\n*Format:* {format_type}\n*Interviewer:* {interviewer}", priority="high")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "interview_date": date,
        "interview_time": time,
        "format": format_type,
        "interviewer": interviewer
    }
    with open("interviews.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return {"scheduled": "success", "details": log_entry}

def decline_offer(company, reason="pursuing other opportunities"):
    """Politely decline job offers"""
    send_telegram(f"❌ *OFFER DECLINED*\n\n*Company:* {company}\n*Reason:* {reason}", priority="normal")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "company": company,
        "reason": reason,
        "action": "declined"
    }
    with open("declined_offers.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return {"declined": "success", "company": company}

# ==================== TOOL DEFINITIONS FOR GROQ ====================

tools = [
    {
        "type": "function",
        "function": {
            "name": "record_employer_contact",
            "description": "Use this when an employer provides their contact information or wants to schedule follow-up",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Employer's email address"},
                    "company": {"type": "string", "description": "Company name"},
                    "name": {"type": "string", "description": "Employer's name"},
                    "role": {"type": "string", "description": "Employer's role/position"}
                },
                "required": ["email", "company"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "ALWAYS use this for questions about: salary negotiation, legal matters, deep technical topics outside your expertise, or when confidence is low",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question requiring human review"},
                    "confidence_score": {"type": "number", "description": "Confidence level 0-1"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_interview",
            "description": "Use this to accept and schedule interview invitations",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Interview date"},
                    "time": {"type": "string", "description": "Interview time"},
                    "format_type": {"type": "string", "description": "Interview format (phone/video/in-person)"},
                    "interviewer": {"type": "string", "description": "Interviewer name if provided"}
                },
                "required": ["date", "time", "format_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "decline_offer",
            "description": "Use this to politely decline job offers",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string", "description": "Company making the offer"},
                    "reason": {"type": "string", "description": "Polite reason for declining"}
                },
                "required": ["company"]
            }
        }
    }
]

# ==================== CAREER ASSISTANT CLASS ====================

class CareerAssistant:
    
    def __init__(self, cv_path="me/summaryMe.txt", linkedin_pdf_path="me/Profile.pdf"):
        """Initialize Career Assistant with Groq API"""
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "qwen/qwen3-32b"  # Qwen model
        self.name = "Kenan Akar"
        self.cv_content = ""
        self.linkedin_content = ""
        
        # Load CV/Profile information
        try:
            with open(cv_path, "r", encoding="utf-8") as f:
                self.cv_content = f.read()
        except FileNotFoundError:
            self.cv_content = "CV file not found. Using basic profile."
        
        # Load LinkedIn PDF if available
        try:
            reader = PdfReader(linkedin_pdf_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.linkedin_content += text
        except FileNotFoundError:
            self.linkedin_content = "LinkedIn profile not available."
        
        print(f"✅ Career Assistant initialized with Groq Llama model")
    
    def get_system_prompt(self):
        """Generate system prompt with career context"""
        return f"""You are {self.name}'s Career Assistant AI Agent. You handle communications with potential employers on behalf of {self.name}.

PERSONALITY & TONE:
- Professional, concise, and polite
- Enthusiastic but not desperate
- Confident in skills and experience
- Diplomatic and tactful

CAPABILITIES:
1. Answer interview invitations professionally
2. Respond to technical questions about skills/experience
3. Politely decline offers when appropriate
4. Ask clarifying questions when needed
5. Schedule meetings and follow-ups

CRITICAL RULES:
- NEVER make false claims about skills or experience
- NEVER say "I don't have experience" - instead use record_unknown_question tool
- NEVER commit to salary ranges without human approval (use record_unknown_question tool)
- NEVER answer legal or contract questions (use record_unknown_question tool)
- If a technical question asks about skills/technologies NOT in your CV, IMMEDIATELY use record_unknown_question tool
- If confidence is low or question is outside expertise, use record_unknown_question tool
- For deep technical questions beyond the CV scope, use record_unknown_question tool
- Always maintain {self.name}'s authentic voice and values

IMPORTANT: When asked about technical skills you don't have, DO NOT apologize or say you lack experience. Instead:
1. Use record_unknown_question tool to flag it
2. Express interest in discussing the role requirements
3. Highlight transferable skills from your actual experience

PROFILE CONTEXT:
## CV Summary:
{self.cv_content}

## LinkedIn Profile:
{self.linkedin_content}

Use this information to answer questions accurately. Stay in character as {self.name}'s professional representative."""

    def handle_tool_calls(self, tool_calls):
        """Execute tool functions and return results"""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"🔧 Tool called: {tool_name} with args: {arguments}")
            
            # Get the function from globals
            tool_function = globals().get(tool_name)
            if tool_function:
                result = tool_function(**arguments)
            else:
                result = {"error": "Tool not found"}
            
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results

    def generate_response(self, employer_message: str) -> Tuple[str, List]:
        """
        Generate response to employer message
        Returns: (response_text, conversation_messages)
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": employer_message}
        ]
        
        # Agent loop with tool calling
        max_iterations = 5
        iteration = 0
        tools_used = set()  # Track which tools have been called
        
        while iteration < max_iterations:
            iteration += 1
            
            # After using tools, force final response without tools
            use_tools = tools if iteration == 1 else None
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=use_tools,
                temperature=0.7,
                max_tokens=2000
            )
            
            choice = response.choices[0]
            
            # Check if tools need to be called
            if choice.finish_reason == "tool_calls" and iteration == 1:
                assistant_message = choice.message
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })
                
                # Execute tools
                tool_results = self.handle_tool_calls(assistant_message.tool_calls)
                messages.extend(tool_results)
                
                # Add instruction for final response
                messages.append({
                    "role": "user",
                    "content": "Based on the tool results above, please provide your professional response to the employer."
                })
            else:
                # Response is ready
                return choice.message.content, messages
        
        return "I apologize, but I need more information to respond appropriately. Could you please rephrase your message?", messages

    def evaluate_response(self, employer_message: str, generated_response: str) -> Dict:
        """
        Response Evaluator Agent - Critiques the generated response
        Returns evaluation with score and feedback
        """
        evaluator_prompt = f"""You are a Response Evaluator Agent. Your job is to critique AI-generated career communication responses.

EMPLOYER MESSAGE:
{employer_message}

GENERATED RESPONSE:
{generated_response}

Evaluate the response on these criteria (score each 0-10):
1. **Professional Tone**: Is it appropriately professional and polite?
2. **Clarity**: Is the message clear and easy to understand?
3. **Completeness**: Does it fully address the employer's message?
4. **Safety**: Are there any false claims, hallucinations, or red flags?
5. **Relevance**: Is it relevant and on-topic?

CRITICAL CHECKS:
- Does it make any claims not supported by the CV/profile?
- Does it commit to things requiring human approval (salary, contracts)?
- Is the tone appropriate for employer communication?
- Are there any grammatical or spelling errors?

Provide your evaluation in JSON format:
{{
    "professional_tone": <score 0-10>,
    "clarity": <score 0-10>,
    "completeness": <score 0-10>,
    "safety": <score 0-10>,
    "relevance": <score 0-10>,
    "overall_score": <average score>,
    "pass": <true if overall_score >= 7.5, else false>,
    "feedback": "<brief explanation of issues if any>",
    "suggested_improvements": "<specific suggestions if score < 7.5>"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": evaluator_prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        evaluation = json.loads(response.choices[0].message.content)
        print(f"\n📊 Evaluation Score: {evaluation.get('overall_score', 0)}/10")
        
        return evaluation

    def revise_response(self, employer_message: str, original_response: str, evaluation_feedback: str) -> str:
        """Revise response based on evaluator feedback"""
        revision_prompt = f"""The following response to an employer was evaluated and needs improvement.

EMPLOYER MESSAGE:
{employer_message}

ORIGINAL RESPONSE:
{original_response}

EVALUATOR FEEDBACK:
{evaluation_feedback}

Please generate an improved response that addresses the feedback while maintaining professionalism and authenticity. Make it concise and effective."""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": revision_prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content

    def process_employer_message(self, employer_message: str, employer_name: str = "Employer") -> Dict:
        """
        Main workflow: Process employer message with evaluation and notification
        """
        print(f"\n{'='*60}")
        print(f"📨 NEW MESSAGE FROM: {employer_name}")
        print(f"{'='*60}\n")
        
        # Step 1: Notify about new message
        notify_new_message(employer_name, employer_message)
        
        # Step 2: Generate initial response
        print("🤖 Generating response...")
        response, conversation = self.generate_response(employer_message)
        
        # Step 3: Evaluate response
        print("\n🔍 Evaluating response quality...")
        evaluation = self.evaluate_response(employer_message, response)
        
        max_revisions = 2
        revision_count = 0
        
        # Step 4: Revise if needed
        while not evaluation.get("pass", False) and revision_count < max_revisions:
            revision_count += 1
            print(f"\n⚠️  Response needs improvement (Attempt {revision_count}/{max_revisions})")
            print(f"Feedback: {evaluation.get('feedback', 'No specific feedback')}")
            
            feedback = f"{evaluation.get('feedback', '')} {evaluation.get('suggested_improvements', '')}"
            response = self.revise_response(employer_message, response, feedback)
            evaluation = self.evaluate_response(employer_message, response)
        
        # Step 5: Final decision
        if evaluation.get("pass", False):
            print(f"\n✅ Response approved! (Score: {evaluation.get('overall_score', 0)}/10)")
            notify_response_sent(employer_name, response)
            
            # Optional: Send email notification
            send_email_notification(
                subject=f"✅ Career Assistant: Response Sent to {employer_name}",
                body=f"Response approved and sent.\n\nScore: {evaluation.get('overall_score', 0)}/10\n\nResponse:\n{response}"
            )
            
            status = "approved_and_sent"
        else:
            print(f"\n⚠️  Response quality concerns remain. Requesting human review...")
            notify_human_intervention(
                reason="Response quality below threshold",
                context=f"Score: {evaluation.get('overall_score', 0)}/10. {evaluation.get('feedback', '')}"
            )
            
            # Optional: Send email alert
            send_email_notification(
                subject=f"🚨 Career Assistant: Human Review Needed - {employer_name}",
                body=f"Response quality below threshold.\n\nScore: {evaluation.get('overall_score', 0)}/10\n\nFeedback: {evaluation.get('feedback', '')}\n\nPlease review manually."
            )
            
            status = "requires_human_review"
        
        # Log evaluation for analysis
        log_evaluation(employer_name, employer_message, response, evaluation, status, revision_count)
        
        return {
            "employer_message": employer_message,
            "generated_response": response,
            "evaluation": evaluation,
            "status": status,
            "revision_count": revision_count,
            "timestamp": datetime.now().isoformat()
        }


# ==================== GRADIO INTERFACE ====================

def create_gradio_interface():
    """Create interactive Gradio UI for testing"""
    assistant = CareerAssistant()
    
    def chat_interface(employer_message, employer_name):
        if not employer_message.strip():
            return "Please enter an employer message.", "{}"
        
        result = assistant.process_employer_message(employer_message, employer_name)
        
        # Format output
        output = f"""**Generated Response:**
{result['generated_response']}

**Status:** {result['status']}
**Evaluation Score:** {result['evaluation'].get('overall_score', 0)}/10
**Revisions Made:** {result['revision_count']}

**Detailed Evaluation:**
- Professional Tone: {result['evaluation'].get('professional_tone', 0)}/10
- Clarity: {result['evaluation'].get('clarity', 0)}/10
- Completeness: {result['evaluation'].get('completeness', 0)}/10
- Safety: {result['evaluation'].get('safety', 0)}/10
- Relevance: {result['evaluation'].get('relevance', 0)}/10

**Feedback:** {result['evaluation'].get('feedback', 'N/A')}
"""
        
        return output, json.dumps(result, indent=2)
    
    with gr.Blocks(title="Career Assistant AI Agent", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🤖 Career Assistant AI Agent
        ## Intelligent Career Communication with Multi-Agent System
        
        This system includes:
        - **Career Agent**: Generates professional responses using Groq Llama
        - **Evaluator Agent**: Critiques responses for quality and safety
        - **Notification System**: Alerts via Telegram bot
        - **Unknown Question Detection**: Triggers human intervention when needed
        """)
        
        with gr.Row():
            with gr.Column():
                employer_name_input = gr.Textbox(
                    label="Employer Name",
                    placeholder="e.g., Sarah from TechCorp",
                    value="Potential Employer"
                )
                employer_message_input = gr.Textbox(
                    label="Employer Message",
                    placeholder="Enter the message from the employer...",
                    lines=6
                )
                submit_btn = gr.Button("Generate Response", variant="primary")
            
            with gr.Column():
                response_output = gr.Markdown(label="Response & Evaluation")
                json_output = gr.Code(label="Full JSON Result", language="json")
        
        submit_btn.click(
            fn=chat_interface,
            inputs=[employer_message_input, employer_name_input],
            outputs=[response_output, json_output]
        )
        
        # Test cases
        gr.Markdown("## 📋 Quick Test Cases")
        
        with gr.Row():
            test1 = gr.Button("Test 1: Interview Invitation")
            test2 = gr.Button("Test 2: Technical Question")
            test3 = gr.Button("Test 3: Salary Negotiation (Unknown)")
        
        test1.click(
            lambda: ("HR Manager from Google", "Hi Kenan, We were impressed with your profile. Would you be available for a technical interview next Tuesday at 2 PM EST via Zoom? Please confirm. Best, Sarah"),
            outputs=[employer_name_input, employer_message_input]
        )
        
        test2.click(
            lambda: ("CTO from StartupXYZ", "Hi Kenan, I see you have experience in data science. Can you explain your approach to building machine learning pipelines and what frameworks you prefer?"),
            outputs=[employer_name_input, employer_message_input]
        )
        
        test3.click(
            lambda: ("Hiring Manager from Meta", "Hi Kenan, We'd like to extend an offer. Our salary range is $150K-$200K. We need to know your expected compensation and if you have any other offers. Also, would you sign a non-compete?"),
            outputs=[employer_name_input, employer_message_input]
        )
    
    return app


# ==================== MAIN ====================

if __name__ == "__main__":
    # Initialize and launch Gradio interface
    app = create_gradio_interface()
    app.launch(share=False, server_name="127.0.0.1", server_port=7860)
