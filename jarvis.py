import datetime
import os
import io
import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
from dotenv import load_dotenv
import pyautogui
import time

# Load OPENAI_API_KEY from .env file
load_dotenv()

client = OpenAI()


def start_recording():  # Function to start recording audio
    global recording, frames_list
    print("Recording started. Press Enter to stop.")
    frames_list = []

    recording = True
    sd.default.samplerate = 44100  # Sample rate
    sd.default.channels = 1  # Number of audio channels

    def callback(indata, frames, time, status):
        frames_list.append(indata.copy())

    with sd.InputStream(callback=callback):
        input()  # Wait for user to press Enter
        stop_recording()


def stop_recording():  # Function to stop recording audio, save audio + call next function
    global recording, desktop_path
    print("Recording stopped.")
    recording = False
    sd.stop()

    # Concatenate recorded frames
    full_audio = np.concatenate(frames_list, axis=0)

    # Save audio to desktop
    now = datetime.datetime.now()
    filename = f"audio_{now.strftime('%Y-%m-%d_%H-%M-%S')}.wav"
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, filename)
    # Use soundfile.write to save the audio
    sf.write(file_path, full_audio, 44100)
    print(f"Audio saved to {file_path}")
    new_transcription = get_transcription(file_path)
    print("Transcription: ", new_transcription)
    gpt_response = ask_gpt(new_transcription)
    print("GPT Response: ", gpt_response)
    execute_commands(gpt_response)


def execute_commands(gpt_response):
    lines = gpt_response.splitlines()
    if (lines[0] == "whatsapp"):
        send_whatsapp(lines[1], lines[2])
        response_text = "I sent a WhatsApp to " + \
            lines[1] + " saying " + lines[2]
        respond_to_user(response_text)

    if (lines[0] == "notes"):
        write_note_in_apple_notes(lines[1], lines[2])
        respond_to_user("I have taken a note.")

    if (lines[0] == "question"):
        text_after_question = gpt_response.split("question", 1)[-1].strip()
        respond_to_user(text_after_question)
    print("Press Enter to start recording")


def get_transcription(filename):
    audio_file = open(filename, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcript.text


def ask_gpt(transcription):
    """Ask a question to GPT."""
    instruction_prompt = '''You are a digital assistant system that only supports 3 functions - taking notes for the user, sending WhatsApp messages and answering questions. You will interpret the users's request and always start your response with either 'notes', 'whatsapp' or 'question' depending on what the user requests you to do. Then you will return a newline. If the user requests you take a note you will then return an appropriate title for the note followed by a newline and then the contents of the note. If the user requested to send a WhatsApp you will return the first name of the intended recipient followed by a newline and then the contents of the message body as it if was written in the first-person by the user with an appropriate emoji at the end. If the user just asked a general question like research or maths or fact just write a suitable answer based on your knowledge. You will always answer in this fashion. An example request might be "Please WhatsApp Mitch Williams and tell him I want to have fish for dinner as well as maybe some uh of that uh potato mash we had the other night" and you will respond with:
    whatsapp
    Mitch
    Hey, please can we have fish and some of that leftover potato mash for dinner.💪🏼.
    Thanks, now please answer the following user's request: '''

    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[{"role": "system", "content": instruction_prompt},
                  {"role": "user", "content": transcription}]
    )
    return response.choices[0].message.content


def write_note_in_apple_notes(note_title, note_body):
    """Write a note in Apple Notes."""
    # open notes
    pyautogui.keyDown('command')
    pyautogui.press('space')
    pyautogui.keyUp('command')
    pyautogui.typewrite("notes")
    pyautogui.press('enter')
    time.sleep(3)
    # Create a new note
    pyautogui.keyDown('command')
    pyautogui.press('n')
    pyautogui.keyUp('command')
    pyautogui.typewrite(note_title)
    pyautogui.press('enter')
    pyautogui.typewrite(note_body)
    # Close Notes
    pyautogui.keyDown('command')
    pyautogui.press('w')
    pyautogui.keyUp('command')


def send_whatsapp(recipient, whatsapp_message):
    """Send a message to someone in Whatsapp Web"""
    # open whatsapp
    pyautogui.keyDown('command')
    pyautogui.press('space')
    pyautogui.keyUp('command')
    pyautogui.typewrite("whatsapp")
    pyautogui.press('enter')
    time.sleep(1)
    # Search for recipient
    pyautogui.keyDown('command')
    pyautogui.press('f')
    pyautogui.keyUp('command')
    pyautogui.typewrite(recipient)
    pyautogui.press('tab')
    time.sleep(0.5)
    pyautogui.press('tab')
    pyautogui.press('enter')
    pyautogui.typewrite(whatsapp_message)
    pyautogui.press('enter')
    # Close whatsapp
    pyautogui.keyDown('command')
    pyautogui.press('w')
    pyautogui.keyUp('command')


def respond_to_user(text_response):  # tell the user audibly what you did
    response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=text_response
    )
    audio_stream = response.content
    audio_data, samplerate = sf.read(io.BytesIO(audio_stream), dtype='float32')
    sd.play(audio_data, samplerate)
    sd.wait()  # Wait until the audio is finished playing


# Main loop
recording = False
frames_list = []
desktop_path = ""

print("Press Enter to start recording")
while True:
    input()  # Wait for user to press Enter
    if not recording:
        start_recording()
    else:
        stop_recording()
