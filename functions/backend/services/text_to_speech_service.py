import base64
from google.cloud import texttospeech


class AudioCommentaryService:
    """
    Service to handle audio generated from text
    """

    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()

    def generate_audio_commentary(self, text: str) -> str:
        """
        Generate audio commentary and return base64 encoded audio

        Args:
            text (str): Commentary text to convert to speech

        Returns:
            str: Base64 encoded audio data
        """
        try:
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                # Choose a suitable voice
                name="en-US-Standard-C",  # A sportscaster-like voice
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            )

            # Select the type of audio file
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            # Convert audio to base64 for easy transmission
            audio_base64 = base64.b64encode(
                response.audio_content).decode('utf-8')
            return audio_base64

        except Exception as e:
            print(f"Error generating audio commentary: {e}")
            return "Audio Commentary not available momentarily"


# Initialize the service
audio_commentary_service = AudioCommentaryService()
