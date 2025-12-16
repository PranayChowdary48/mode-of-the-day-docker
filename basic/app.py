import random
import datetime
import redis
from flask import Flask, render_template

app = Flask(__name__)

# Redis connection
redis_client = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

MOODS = {
    "Happy": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExY2FubWFtNDhxbDNsOTV6Z2ExbXdtYTdrZm9hOHd2bG44NjQ1eW5ldCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/fUQ4rhUZJYiQsas6WD/giphy.gif",
    "Sad": "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3NDF2cGVuZWs1bnVkNTVqdTFmYjdqamo4Ynd0bjVocHoxYjNoZWt5ayZlcD12MV9naWZzX3NlYXJjaCZjdD1n/2rtQMJvhzOnRe/giphy.gif",
    "Angry": "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3Nzh3ZWIxbnJianduaGhtbzl1ZGwxYnd3Y2E1eDV4ZDgxcmMzZWY3YSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/29bKyyjDKX1W8/giphy.gif",
    "Tired": "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGxpZzEwaXBzdjA1ZzN5dnFzdmZrem02ZzdpMXdudDR4Ynk3NXJqMCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Zsc4dATQgcBmU/giphy.gif",
    "Hungry": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcWF4ZXU3MmdidzZwZDF2bXRsZmRoNjFtbWV0YzdmYzF2YXIzOXZtNiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/jKaFXbKyZFja0/giphy.gif",
    "Proud": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNDdhNXQyNXAxZm84ajI5eTNvNDR6YWR6Mnl0bDlndHFqc2t0MW95ciZlcD12MV9naWZzX3NlYXJjaCZjdD1n/Vg2TAoPzDstzy/giphy.gif",
    "Love": "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3aTFyanZnNHg5NWprN2EzM3o2YjNzbmdlZG8zYm1iOWdjYzN4NGNhaiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/XtluHogie3wB2/giphy.gif",
}

def seconds_until_midnight():
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    midnight = datetime.datetime.combine(tomorrow.date(), datetime.time.min)
    return int((midnight - now).total_seconds())

@app.route("/")
def mood_of_the_day():
    today = datetime.date.today().isoformat()
    redis_key = f"mood:{today}"

    cached = redis_client.hgetall(redis_key)

    if cached:
        mood = cached["mood"]
        gif = cached["gif"]
    else:
        mood, gif = random.choice(list(MOODS.items()))
        redis_client.hset(redis_key, mapping={"mood": mood, "gif": gif})
        redis_client.expire(redis_key, seconds_until_midnight())

    return render_template("index.html", mood=mood, gif=gif)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)