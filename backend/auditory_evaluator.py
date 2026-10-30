import whisper
import joblib
import keras
import librosa
import numpy as np
import parselmouth

whisperModel = whisper.load_model("tiny.en")
model = keras.saving.load_model('bestmo2.keras')
scaler = joblib.load('scaler-prosody.joblib')

def extract_features(audio_path):
    # Load audio file
    y, sr = librosa.load(audio_path, sr=None)
    #######
    result = whisperModel.transcribe(audio_path, language='en', word_timestamps=True)
    firstWordEnd = result['segments'][0]['words'][0]['end']
    lastWordStart = result['segments'][-1]['words'][-1]['start']
    duration = lastWordStart-firstWordEnd
    totalSpoken = 0
    for segment in result['segments']:
        for word in segment['words']:
            speakLength = word['end'] - word['start']
            if speakLength < 1.5:
                totalSpoken += speakLength
    ########
    # Total duration
    total_duration = librosa.get_duration(y=y, sr=sr)

    # Split into frames
    frame_length = 2048  # you can adjust this value
    hop_length = 512     # you can adjust this value
    frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length)

    # Silence detection
    intervals = librosa.effects.split(y, top_db=30)
    total_silence = total_duration - sum((end-start)/sr for start, end in intervals)
    percent_silence = total_silence / total_duration
    if duration < totalSpoken:
        percent_silence = 0
    else:
        percent_silence = (duration - totalSpoken) / duration

    # Fundamental frequency (f0)
    snd = parselmouth.Sound(audio_path)
    pitch = snd.to_pitch()

    f0_values = pitch.selected_array['frequency']
    f0_values = f0_values[f0_values > 0]  # Remove unvoiced frames (f0 = 0)

    min_f0 = np.min(f0_values)
    max_f0 = np.max(f0_values)
    mean_f0 = np.mean(f0_values)
    stdev_f0 = np.std(f0_values)
    range_f0 = max_f0 - min_f0

    relpos_min_f0 = np.argmin(f0_values) / len(f0_values)
    relpos_max_f0 = np.argmax(f0_values) / len(f0_values)

    # Slopes
    absslope1 = np.mean(np.abs(np.diff(f0_values[:len(f0_values)//2])))
    absslope2 = np.mean(np.abs(np.diff(f0_values[len(f0_values)//2:])))

    # Frames and voiced frames
    total_frames = len(y) // hop_length
    voiced_frames = np.sum(f0_values > 0)
    spk_rate = voiced_frames / total_frames

    # Assuming gender is known, set it manually
    gender = 1  # or 'M'

    # Aggregate features into a dictionary
    features = {
        "percentsilence": percent_silence,
        "minf0": min_f0,
        "maxf0": max_f0,
        "meanf0": mean_f0,
        "stdevf0": stdev_f0,
        "rangef0": range_f0,
        "relposminf0": relpos_min_f0,
        "relposmaxf0": relpos_max_f0,
        "absslope1": absslope1,
        "absslope2": absslope2,
        "spkRate": spk_rate,
        "Gender": gender
    }

    return features

def prosodic_eval(file):
    audio_path = file
    sample = extract_features(audio_path)
    narray = scaler.transform(np.array(list(sample.values())).reshape(1,-1))
    return model.predict(narray.reshape(1,-1))

