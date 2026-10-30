import os
from protonmail import ProtonMail
from datetime import datetime

def sendScore(results, recipient,uuid):
    username = os.environ["PROTON_USER"]
    password = os.environ["PROTON_PASSWORD"]

    proton = ProtonMail()
    proton.login(username, password)

    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    new_message = proton.create_message(
    recipients=[recipient],
    subject=f"Exam Scores for the date {formatted_datetime}",
    body=f"You Can See Your Scores At $BACKENDADDRESS/EvaluateExam/{uuid}\nresults",  # html or just text
    )

    sent_message = proton.send_message(new_message)