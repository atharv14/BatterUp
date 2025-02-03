from typing import Dict, Optional, List
import random
import google.generativeai as genai
from core.config import settings

class CommentaryService:
    def __init__(self):
        self.api_key = settings.GEMINI_KEY
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            self.model = None

    def generate_template_commentary(
        self,
        action_type: str,
        action_details: Dict,
        game_context: Dict,
        play_history: List[Dict]
    ) -> str:
        """Fallback template-based commentary generation"""
        inning_str = (
            f"{'Top' if game_context['is_top_inning'] else 'Bottom'} "
            f"of inning {game_context['inning']}"
        )
        score_str = (
            f"Score: {game_context['score']['team1']}-"
            f"{game_context['score']['team2']}"
        )

        # Pitch commentary templates
        if action_type == 'pitch':
            pitch_templates = [
                f"Pitcher winds up in the {inning_str}. {score_str}",
                f"Here comes the pitch in the {inning_str}! {score_str}",
                f"Pitcher looks in for the sign. Delivery coming up in the {inning_str}. {score_str}"
            ]
            return random.choice(pitch_templates)

        # Bat commentary templates
        if action_type == 'bat':
            bat_templates = {
                'home_run': [
                    f"CRACK! That's a home run in the {inning_str}! {score_str}",
                    f"It's going, going, GONE! A spectacular home run! {score_str}"
                ],
                'triple': [
                    f"A blazing triple in the {inning_str}! {score_str}",
                    f"The ball finds the gap and the runner is racing to third! {score_str}"
                ],
                'double': [
                    f"That's going to be extra bases in the {inning_str}! {score_str}",
                    f"A solid double! {score_str}"
                ],
                'single': [
                    f"Base hit in the {inning_str}! {score_str}",
                    f"A clean single! {score_str}"
                ],
                'out': [
                    f"The defense makes the play! Out number {game_context['outs']} in the {inning_str}",
                    f"That's an out! {score_str}"
                ]
            }
            outcome = action_details.get('outcome', 'out')
            templates = bat_templates.get(outcome, [f"The play is made in the {inning_str}! {score_str}"])
            return random.choice(templates)

        return "The game continues..."

    async def generate_ai_commentary(
        self,
        action_type: str,
        action_details: Dict,
        game_context: Dict,
        play_history: List[Dict]
    ) -> str:
        """Generate commentary using Gemini AI"""
        try:
            if not self.model:
                return self.generate_template_commentary(
                    action_type, action_details, game_context, play_history
                )

            prompt = self.create_prompt(action_type, action_details, game_context, play_history)
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            print(f"Failed to generate AI commentary: {e}")
            return self.generate_template_commentary(
                action_type, action_details, game_context, play_history
            )

    def create_prompt(
        self,
        action_type: str,
        action_details: Dict,
        game_context: Dict,
        play_history: List[Dict]
    ) -> str:
        """Create prompt for Gemini AI"""
        # Prepare play history context
        history_context = ""
        if play_history:
            history_context = "Recent Game History:\n"
            for play in play_history[-3:]:  # Last 3 plays
                if 'commentary' in play:
                    history_context += f"- {play['commentary']}\n"

        return f"""
        As a baseball commentator, provide an exciting, concise commentary:
        
        Game Situation:
        - Inning: {game_context['inning']} ({'Top' if game_context['is_top_inning'] else 'Bottom'})
        - Score: {game_context['score']['team1']}-{game_context['score']['team2']}
        - Outs: {game_context['outs']}
        
        Action Type: {action_type}
        Action Details: {action_details}
        
        {history_context}
        
        Provide a short, energetic commentary that takes into account the game's recent history.
        """

# Initialize the service
commentary_service = CommentaryService()