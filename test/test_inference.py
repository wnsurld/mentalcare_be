# scripts/test_inference.py
import os
from dotenv import load_dotenv

from app.services.inference_service import infer_emotion_and_situation

load_dotenv()

def main():
    msg = "요즘 회사 일 때문에 너무 지치고 불안해."
    info = infer_emotion_and_situation(
        user_msg=msg,
        user_profile={"name": "테스트유저"},
    )
    print("=== inference result ===")
    for k, v in info.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()

