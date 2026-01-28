import os
import time
import whisper
import torch
import sys

# --- PATH SETUP ---
# Ensuring FFmpeg is accessible for Whisper processing
ffmpeg_bin_path = r'C:\ffmpeg\bin'
os.environ["PATH"] += os.pathsep + ffmpeg_bin_path

# Model load: "small" is better for technical words like Python/SQL than "base"

model = whisper.load_model("small") 

def save_audio(audio_bytes):
    """
    Saves audio bytes into the specific project directory structure.
    """
    # Matching the folder structure shown in your VS Code explorer
    save_dir = os.path.join("app", "data", "recordings")
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Using .mp3 format as it works well with Whisper
    filename = os.path.join(save_dir, f"user_intro_{int(time.time())}.mp3")
    
    try:
        with open(filename, 'wb') as f:
            f.write(audio_bytes)
        print(f"DEBUG: Audio file saved at {filename}")
        return filename # Returns the exact path for the voice_node to use
    except Exception as e:
        print(f"Error saving audio file: {e}")
        return None

def transcribe_audio_local(audio_path):
    """
    Transcribes the local audio file using OpenAI Whisper.
    """
    try:
        if not os.path.exists(audio_path):
            print(f"DEBUG: File not found at {audio_path}")
            return "Audio file not found."

        print(f"DEBUG: Transcribing {audio_path}...")
        
        # fp16=False ensures it runs on CPU if no GPU is available
        result = model.transcribe(audio_path, fp16=False)
        
        text = result.get("text", "").strip()
        
        if not text:
            print("DEBUG: Whisper found no speech in the audio.")
            return "No clear audio detected."
            
        print(f"DEBUG: Transcription result: {text}")
        return text
        
    except Exception as e:
        print(f"Whisper Transcription Error: {e}")
        return f"Transcription error. Please ensure FFmpeg is in {ffmpeg_bin_path}"