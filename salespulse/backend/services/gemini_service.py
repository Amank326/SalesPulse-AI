import os
import logging
from typing import Dict, Any, List
import httpx

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Production-ready wrapper for Google Gemini API REST endpoints.
    Reads API key securely from environment variables.
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.model = "gemini-1.5-flash"
        
        # If API key is missing, log a warning but don't hard crash at startup
        # Instead, raise a clear error when methods are invoked
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set in the environment variables.")

    def _call_gemini_api(self, prompt: str) -> str:
        """Helper to execute standard REST API calls to Gemini."""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is missing in your environment configuration (.env file).")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error(f"Gemini API returned error {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"Gemini API returned error: {resp.text}")
                
                res_data = resp.json()
                text_out = res_data['candidates'][0]['content']['parts'][0]['text']
                return text_out
        except Exception as e:
            logger.exception("Error communicating with Gemini API")
            raise RuntimeError(f"Communication with Gemini failed: {e}")

    def generate_report(self, report_type: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates specific analytics reports based on the uploaded sales/forecast dataset.
        Supported report types: 'summary', 'executive', 'marketing', 'inventory', 'risk', 'revenue'
        """
        # Format the data metrics for the prompt
        metrics = data_context.get("metrics", {})
        history = data_context.get("history", {})
        forecast = data_context.get("forecast", {})

        history_summary = f"Total Historical Periods: {len(history.get('dates', []))}, Total Historical Sum: {metrics.get('total_actual', 'N/A')}"
        forecast_summary = f"Forecast Steps: {len(forecast.get('dates', []))}, Forecasted Total: {metrics.get('forecast_total', 'N/A')}"
        model_details = f"Model Selected: {metrics.get('best_model', 'N/A')} (MAE: {metrics.get('val_mae', 'N/A')}, RMSE: {metrics.get('val_rmse', 'N/A')}, R2: {metrics.get('val_r2', 'N/A')})"
        
        # Build prompt template
        prompts = {
            "summary": (
                f"You are a Principal Business Analyst. Based on this sales intelligence data:\n"
                f"- History: {history_summary}\n"
                f"- Forecast: {forecast_summary}\n"
                f"- Model details: {model_details}\n\n"
                f"Write a concise, professional Business Summary of the company's sales status, "
                f"highlighting recent trends and upcoming performance expectations. Format with markdown headings."
            ),
            "executive": (
                f"You are a Senior Strategic Executive. Based on this sales intelligence data:\n"
                f"- History: {history_summary}\n"
                f"- Forecast: {forecast_summary}\n"
                f"- Model details: {model_details}\n\n"
                f"Write a high-level Executive Report for decision makers. Include strategic takeaways, "
                f"growth projections, and high-impact operational recommendations. Format with markdown headings."
            ),
            "marketing": (
                f"You are a Chief Marketing Officer (CMO). Based on this sales data and trend analysis:\n"
                f"- History: {history_summary}\n"
                f"- Forecast: {forecast_summary}\n"
                f"Identify marketing suggestions and campaigns to capitalize on the forecast growth or offset "
                f"seasonal declines. Propose 3 detailed campaign strategies with timelines. Format with markdown headings."
            ),
            "inventory": (
                f"You are an Operations and Supply Chain Director. Based on this sales demand forecast:\n"
                f"- Recent history: {history_summary}\n"
                f"- Forecast: {forecast_summary}\n\n"
                f"Provide actionable Inventory Suggestions. Outline stocking adjustments, safety stock levels, "
                f"and potential supply chain constraints to prevent stockouts or overstocking. Format with markdown."
            ),
            "risk": (
                f"You are a Risk Management Officer. Based on this historical and forecast data:\n"
                f"- History: {history_summary}\n"
                f"- Forecast: {forecast_summary}\n"
                f"- Model performance: {model_details}\n\n"
                f"Perform a comprehensive Risk Analysis. Identify model uncertainty risks, market volatility "
                f"factors, and structural threats to the forecasted revenue. Format with markdown."
            ),
            "revenue": (
                f"You are a Corporate Finance Officer. Based on this revenue series:\n"
                f"- History: {history_summary}\n"
                f"- Forecast: {forecast_summary}\n\n"
                f"Generate detailed Revenue Insights. Analyze cash flow predictability, margin opportunities, "
                f"growth drivers, and seasonal patterns in the sales records. Format with markdown."
            )
        }

        selected_prompt = prompts.get(report_type.strip().lower())
        if not selected_prompt:
            raise ValueError(f"Unsupported report type: {report_type}")

        report_content = self._call_gemini_api(selected_prompt)
        return {
            "report_type": report_type,
            "content": report_content
        }

    def chat_with_data(self, user_message: str, data_context: Dict[str, Any], chat_history: List[Dict[str, str]] = None) -> str:
        """
        Performs context-aware natural language chat with the user's uploaded dataset and predictions.
        """
        metrics = data_context.get("metrics", {})
        history = data_context.get("history", {})
        forecast = data_context.get("forecast", {})

        # Construct background context
        context_prompt = (
            f"You are SalesPulse AI, an intelligent revenue forecasting assistant. "
            f"You are chatting with a user about their uploaded sales dataset.\n"
            f"Dataset Context:\n"
            f"- Original Date Column: {data_context.get('date_col', 'N/A')}\n"
            f"- Original Revenue Column: {data_context.get('revenue_col', 'N/A')}\n"
            f"- Time Frequency: {data_context.get('freq', 'N/A')}\n"
            f"- Total History Sum: {metrics.get('total_actual', 'N/A')}\n"
            f"- Total Forecast Sum: {metrics.get('forecast_total', 'N/A')}\n"
            f"- Best Model: {metrics.get('best_model', 'N/A')} (MAE: {metrics.get('val_mae', 'N/A')}, RMSE: {metrics.get('val_rmse', 'N/A')}, R2: {metrics.get('val_r2', 'N/A')})\n"
            f"- Historical Data: last few dates/values: {list(zip(history.get('dates', [])[-5:], history.get('values', [])[-5:]))}\n"
            f"- Forecast Predictions: {list(zip(forecast.get('dates', [])[:5], forecast.get('values', [])[:5]))}\n\n"
            f"Answer the user's questions clearly, accurately, and professionally. Use tables, bolding, and bullet points where helpful."
        )

        # Build message history string
        history_str = ""
        if chat_history:
            for msg in chat_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_str += f"{role}: {msg.get('content')}\n"

        prompt = f"{context_prompt}\n\nChat History:\n{history_str}\nUser: {user_message}\nAssistant:"
        
        return self._call_gemini_api(prompt)
