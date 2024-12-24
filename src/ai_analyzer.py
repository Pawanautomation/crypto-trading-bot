# ai_analyzer.py
from openai import AsyncOpenAI
from anthropic import Anthropic
import logging
from typing import Dict, Any, Optional
from config.config import Config

class AIAnalyzer:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.claude_client = Anthropic(api_key=Config.CLAUDE_API_KEY)

    def _parse_ai_response(self, response: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse AI response into structured format"""
        try:
            lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
            result = {}

            for line in lines:
                if ':' not in line:
                    continue

                key, value = [x.strip() for x in line.split(':', 1)]
                key = key.upper()

                if key == 'DECISION':
                    result['direction'] = value.upper()
                elif key == 'CONFIDENCE':
                    result['confidence'] = float(value.replace('%', ''))
                elif key == 'STOP_LOSS':
                    result['stop_loss'] = float(value.replace('%', ''))
                elif key == 'TAKE_PROFIT':
                    result['take_profit'] = float(value.replace('%', ''))
                elif key == 'RISK':
                    result['risk'] = int(value)

            result['source'] = source
            return result

        except Exception as e:
            logging.error(f"Error parsing {source} response: {str(e)}")
            return None

    def _create_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for AI analysis"""
        return f"""
        Analyze this crypto market data and provide trading recommendations:

        Current Market Data:
        - Price: ${market_data.get('current_price', 'N/A')}
        - 24h Change: {market_data.get('price_change_24h', 'N/A')}%
        - Volume: ${market_data.get('volume_24h', 'N/A')}
        - Trend: {market_data.get('trend', 'N/A')}
        - RSI: {market_data.get('indicators', {}).get('rsi_14', 'N/A')}
        - Price vs SMA: {market_data.get('indicators', {}).get('price_vs_sma', 'N/A')}%

        Provide in this exact format:
        DECISION: [BUY/SELL/HOLD]
        CONFIDENCE: [0-100]
        STOP_LOSS: [percentage]
        TAKE_PROFIT: [percentage]
        RISK: [1-10]
        """

    async def _get_gpt_analysis(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get analysis from GPT"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a crypto trading expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return self._parse_ai_response(response.choices[0].message.content, 'gpt')
        except Exception as e:
            logging.error(f"GPT analysis error: {str(e)}")
            return None

    async def _get_claude_analysis(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get analysis from Claude (async wrapper)"""
        try:
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=150,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            if response.content:
                return self._parse_ai_response(response.content[0].text, "claude")
            return None
        except Exception as e:
            logging.error(f"Claude analysis error: {str(e)}")
            return None

    async def analyze_market(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get analysis from both AIs and combine insights"""
        try:
            prompt = self._create_analysis_prompt(market_data)

            # Get analysis from both AIs
            gpt_analysis = await self._get_gpt_analysis(prompt)
            claude_analysis = await self._get_claude_analysis(prompt)

            if gpt_analysis and claude_analysis:
                return {
                    'gpt_analysis': gpt_analysis,
                    'claude_analysis': claude_analysis,
                    'gpt_confidence': gpt_analysis.get('confidence', 0),
                    'claude_confidence': claude_analysis.get('confidence', 0),
                    'agreement': gpt_analysis.get('direction') == claude_analysis.get('direction'),
                    'recommended_direction': gpt_analysis.get('direction'),
                    'average_confidence': (gpt_analysis.get('confidence', 0) +
                                        claude_analysis.get('confidence', 0)) / 2,
                    'should_trade': (
                        gpt_analysis.get('direction') == claude_analysis.get('direction') and
                        (gpt_analysis.get('confidence', 0) + claude_analysis.get('confidence', 0)) / 2 >= Config.MIN_CONFIDENCE_THRESHOLD
                    )
                }
            return None
        except Exception as e:
            logging.error(f"Error in market analysis: {str(e)}")
            return None