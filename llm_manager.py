import os
import random
import json
import time
import re
import base64
import config
import personalities

# Gemini models use the Google Generative AI SDK
GEMINI_MODELS = {"gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro"}
LOCAL_MODELS = {"llava", "gemma4:12b"}


class LLMManager:
    def __init__(self):
        self.current_personality = personalities.DEFAULT_PERSONALITY
        self.active_model = config.DEFAULT_MODEL

        # Initialize Gemini client if API key available
        self._gemini_client = None
        api_key = config.GOOGLE_API_KEY
        if api_key:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=api_key)
                print(f"[LLM] Gemini API initialized")
            except Exception as e:
                print(f"[LLM] Gemini init failed: {e}")
        
    def set_model(self, model_name: str) -> None:
        self.active_model = model_name
        print(f"[LLM] Model set to: {model_name} ({'cloud' if model_name in GEMINI_MODELS else 'local'})")
        
    def get_model(self) -> str:
        return self.active_model
    
    def set_personality(self, personality_key: str) -> None:
        self.current_personality = personality_key
    
    def get_personality(self) -> str:
        return self.current_personality

    def _is_gemini(self, model: str) -> bool:
        return model in GEMINI_MODELS

    def _execute_gemini(self, model: str, text_content: str, images: list, system_prompt: str) -> str:
        """Call Gemini API via google-genai SDK."""
        if not self._gemini_client:
            raise ValueError("Gemini API key not configured")

        from google.genai import types

        # Build content parts
        parts = []
        
        # Add images first
        for img_b64 in images:
            img_bytes = base64.b64decode(img_b64)
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        
        # Add text
        parts.append(types.Part.from_text(text=text_content))

        response = self._gemini_client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=config.LLM_MAX_TOKENS,
                temperature=0.9,
            ),
        )

        text = response.text
        if not text or not text.strip():
            raise ValueError("Gemini returned empty content")
        
        return self._clean_text(text)

    def _execute_ollama(self, model: str, text_content: str, images: list, system_prompt: str) -> str:
        """Call local Ollama API."""
        import requests
        
        user_msg = {"role": "user", "content": text_content}
        if images:
            user_msg["images"] = images
            
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                user_msg
            ],
            "stream": False,
            "options": {
                "num_predict": config.LLM_MAX_TOKENS
            }
        }
        
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=120.0  # Local models need more time
        )
        resp.raise_for_status()
        data = resp.json()
            
        message = data.get("message", {})
        text = message.get("content", "")
        
        # If standard content is empty, check for reasoning/thinking tokens
        if not text or not text.strip():
            thinking = message.get("thinking", "")
            if thinking:
                lines = [line.strip() for line in thinking.strip().split('\n') if line.strip()]
                if lines:
                    text = lines[-1]
                else:
                    raise ValueError("Model returned empty content")
            else:
                raise ValueError("Model returned empty content")
                
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """Strip quotes and whitespace from model output."""
        text = text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        return text

    def _execute_model(self, model: str, text_content: str, images: list, system_prompt: str) -> str:
        """Route to the correct backend based on model name."""
        if self._is_gemini(model):
            return self._execute_gemini(model, text_content, images, system_prompt)
        else:
            return self._execute_ollama(model, text_content, images, system_prompt)
    
    def generate_message(self, event: dict) -> str:
        system_prompt = personalities.get_system_prompt(self.current_personality)
        
        user_msg = {
            'trigger': event.get('trigger', 'unknown'),
            'application': event.get('application', 'unknown'),
            'website': event.get('website', ''),
            'duration_minutes': round(event.get('duration_minutes', 0)),
            'rage_level': event.get('rage_level', 0),
            'previous_warnings': event.get('previous_warnings', 0)
        }

        # Build text content (inject system prompt for local models)
        text_content = f"INSTRUCTIONS:\n{system_prompt}\n\nCURRENT CONTEXT:\n{json.dumps(user_msg)}\n\nTASK: Based on the instructions and the image provided, output exactly one short sarcastic line."

        # Extract images
        images = []
        if 'screenshot_base64' in event:
            images.append(event['screenshot_base64'])
            print(f"[Vision] LLM request includes image ({len(event['screenshot_base64'])*3//4//1024} KB)")
        else:
            print("[Vision] LLM request is text-only (no screenshot)")
            
        # Try active model
        try:
            result = self._execute_model(self.active_model, text_content, images, system_prompt)
            print(f"[LLM] Generated heckle: {result}")
            return result
        except Exception as e:
            print(f"[LLM] Active model ({self.active_model}) failed: {e}")
            
        # Fallback chain: try other models
        fallback_order = [m for m in config.MODELS if m != self.active_model]
        for fallback_model in fallback_order:
            try:
                print(f"[LLM] Trying fallback: {fallback_model}...")
                result = self._execute_model(fallback_model, text_content, images, system_prompt)
                print(f"[LLM] Fallback heckle: {result}")
                return result
            except Exception as e2:
                print(f"[LLM] Fallback {fallback_model} failed: {e2}")
                continue
                
        # All models failed — canned response
        print("[LLM] All models failed. Using canned response...")
        return personalities.get_fallback(self.current_personality, user_msg['rage_level'])
            
    def generate_lie_response(self, is_lie: bool, claimed: str, actual_app: str, actual_domain: str) -> str:
        if is_lie:
            event = {
                'trigger': 'lie_detected',
                'application': actual_app,
                'website': actual_domain,
                'rage_level': 5,
                'duration_minutes': 0,
                'previous_warnings': 0,
                'claimed': claimed
            }
        else:
            event = {
                'trigger': 'productive_streak',
                'application': actual_app,
                'website': actual_domain,
                'rage_level': 0,
                'duration_minutes': 0,
                'previous_warnings': 0,
                'claimed': claimed
            }
            
        return self.generate_message(event)
