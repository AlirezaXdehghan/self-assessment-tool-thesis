import whisper
import time
import ffmpeg
import re
import os
from emailScore import sendScore

def filler_remover(text):
    fillers = [
        'absolutely',
        'actual',
        'actually',
        'amazing',
        'anyway',
        'apparently',
        'approximately',
        'badly',
        'basically',
        'begin',
        'certainly',
        'clearly',
        'completely',
        'definitely',
        'easily',
        'effectively',
        'entirely',
        'especially',
        'essentially',
        'exactly',
        'extremely',
        'fairly',
        'frankly',
        'frequently',
        'fully',
        'generally',
        'hardly',
        'heavily',
        'highly',
        'hopefully',
        'just',
        'largely',
        'like',
        'literally',
        'maybe',
        'might',
        'most',
        'mostly',
        'much',
        'necessarily',
        'nicely',
        'obviously',
        'ok',
        'okay',
        'particularly',
        'perhaps',
        'possibly',
        'practically',
        'precisely',
        'primarily',
        'probably',
        'quite',
        'rather',
        'real',
        'really',
        'relatively',
        'right',
        'seriously',
        'significantly',
        'simply',
        'slightly',
        'so',
        'specifically',
        'start',
        'strongly',
        'stuff',
        'surely',
        'things',
        'too',
        'totally',
        'truly',
        'try',
        'typically',
        'ultimately',
        'usually',
        'very',
        'virtually',
        'well',
        'whatever',
        'whenever',
        'wherever',
        'whoever',
        'widely'
    ]
    fillers_regex = [
        r'\buh+\b', r'\bah+\b', r'\baha+h+\b', r'\bahh+\b', r'\bum+\b', r'\bumm+\b', r'\buhuh+\b', r'\buhum+\b',
        r'\ber+\b',
        r'\bhmm+\b', r'\bhmmm+\b', r'\bhuh+\b', r'\blike\b', r'\byou know\b', r'\bi mean\b', r'\bsort of\b',
        r'\bkind of\b', r'\bright\b', r'\bactually\b', r'\bbasically\b', r'\bseriously\b', r'\bliterally\b',
        r'\bessentially\b', r'\bobviously\b', r'\bwell\b', r'\bso\b', r'\bokay\b', r'\bok\b', r'\bjust\b',
        r'\byou see\b', r'\byeah\b', r'\beh\b', r'\buh huh\b', r'\bmhm\b', r'\bmmm+\b', r'\boh\b', r'\bah um\b',
        r'\buh uh\b', r'\bgot it\b', r'\bright\?\b', r'\bknow what i mean\?\b', r'\bknow what i\'m saying\?\b',
        r'\blet me think\b', r'\bsort of like\b', r'\bkind of like\b', r'\bbasically like\b'
    ]

    pattern = r'\b(?:' + '|'.join(fillers_regex) + r')\b'
    filtered_text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    pattern = r'\b(?:' + '|'.join(map(re.escape, fillers)) + r')\b'
    filtered_text = re.sub(pattern, '', filtered_text, flags=re.IGNORECASE)
    return filtered_text


def speech2text(file_path: str, directory: str, timestamps, model):
    import os
    cutvideos(file_path, directory, timestamps)
    files_in_directory = os.listdir(directory)
    Answers = [file for file in files_in_directory if file.endswith('_.webm')]
    for index, Answer in enumerate(Answers):
        file = os.path.join(directory, Answer)
        result = model.transcribe(file, fp16=False)
        file = Answer + '.txt'
        with open(os.path.join(directory, file), 'w') as textfile:
            textfile.write(filler_remover(result['text']))



def cutvideos(original_video_path, directory, timestamps):
    tuples2cut = []
    for i in range(len(timestamps)-1):
        if i == 0:
            tuples2cut.append((i, 0, timestamps[i]))
        else:
            tuples2cut.append((i, timestamps[i - 1], timestamps[i]))
    for question, start, finish in tuples2cut:
        output_clip = f"{directory}/{question}_.webm"
        print(original_video_path)
        cut_webm(original_video_path, output_clip, start, finish)


def cut_webm(input_file, output_file, start_time_ms, end_time_ms):
    start_time_sec = start_time_ms / 1000.0
    duration_sec = (end_time_ms - start_time_ms) / 1000.0
    ffmpeg.input(input_file, ss=start_time_sec).output(output_file, t=duration_sec).run(overwrite_output=True)