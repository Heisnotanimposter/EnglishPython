# Install necessary libraries
!pip install torch librosa numpy matplotlib

# Importing necessary libraries
import torch
import numpy as np
import librosa
import matplotlib.pyplot as plt
from scipy.io.wavfile import write

# Clone FastSpeech2 repository and install dependencies
!git clone https://github.com/ming024/FastSpeech2
!pip install -r FastSpeech2/requirements.txt

# Clone HiFi-GAN repository
!git clone https://github.com/jik876/hifi-gan
!pip install -r hifi-gan/requirements.txt

# Load FastSpeech2 model (pre-trained)
from FastSpeech2.inference import infer_model
fastspeech2 = infer_model()

# Load HiFi-GAN vocoder (pre-trained)
from hifi_gan.models import Generator
hifigan = Generator().to('cuda')
checkpoint = torch.load("hifi-gan/pretrained_model/checkpoint_500000.pth.tar", map_location='cuda')
hifigan.load_state_dict(checkpoint['generator'])
hifigan.eval().remove_weight_norm()

# Function to generate Mel-spectrogram
def generate_mel_spectrogram(text):
    mel = fastspeech2(text)
    return mel

# Function to generate speech from Mel-spectrogram
def mel_to_audio(mel):
    mel = torch.FloatTensor(mel).unsqueeze(0).to('cuda')
    with torch.no_grad():
        audio = hifigan(mel).squeeze().cpu().numpy()
    return audio

# Text to speech generation
text = "Hello, this is a high-performance text to speech system."
mel_spectrogram = generate_mel_spectrogram(text)
audio = mel_to_audio(mel_spectrogram)

# Save audio file
write("output_speech.wav", 22050, audio)

# Display Mel-spectrogram
plt.figure(figsize=(10, 4))
plt.imshow(mel_spectrogram, aspect='auto', origin='lower', interpolation='none')
plt.title('Mel-spectrogram')
plt.show()

# Play audio (requires IPython.display)
import IPython.display as ipd
ipd.Audio(audio, rate=22050)