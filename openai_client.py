# openai_client.py
import io
import os
from openai import AzureOpenAI

REQUIRED_ENV_VARS = [
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
]


def get_missing_openai_env_vars():
    return [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]


# Azure OpenAI クライアント
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2025-04-01-preview",   # DALL·E 3 対応
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# ---------------------------------------------------------
# ① ベース画像生成（DALL·E 3 / gpt-image-1）
# ---------------------------------------------------------
def generate_base_image(prompt, size="1024x1024"):
    styled_prompt = (
        "GIFアニメーション用のベース画像として、"
        "アニメ調で、輪郭がはっきりしたシンプルなセル画風にしてください。"
        "キャラクターは正面寄りで全身が収まり、背景はできるだけ簡潔にしてください。"
        f"題材: {prompt}"
    )
    result = client.images.generate(
        model="gpt-image-1-mini",   # DALL·E 3
        prompt=styled_prompt,
        size=size,
        n=1,
        quality="low"
    )
    return result.data[0].b64_json


# ---------------------------------------------------------
# ② GPT-4.1-mini：動きを抽出してコマJSONを生成
# ---------------------------------------------------------
def extract_motion_and_generate_frames(user_prompt, frame_count=4):
    frame_examples = ",\n    ".join(
        f'{{"description": "{i}コマ目の動き"}}'
        for i in range(1, frame_count + 1)
    )
    system_prompt = f"""
あなたはGIFアニメーションの演出家です。
ユーザーの文章から「キャラクターの動き」を抽出し、
その動きを{frame_count}コマのアニメーションとして表現してください。

重要：
- 絶対に ``` や ```json のようなコードブロックを使わない
- JSON のみを返す（前後に文章を付けない）
- 各コマは小さな変化にする（大きなポーズ変更は禁止）
- キャラクターの位置・構図は固定する
- 必ず frames を {frame_count} 個返す
- JSON のキー名・構造は変更しない

出力形式（変更しない）：
{{
  "motion": "抽出した動き",
  "frames": [
    {frame_examples}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    raw = response.choices[0].message.content

    clean = (
        raw.replace("```json", "")
           .replace("```", "")
           .replace("```JSON", "")
           .strip()
    )

    return clean


# ---------------------------------------------------------
# ③ image-to-image 4コマ生成
# ---------------------------------------------------------
def generate_motion_frame(base_image_source, frame_description, size="1024x1024"):
    """
    base_image_source: ベース画像の URL またはバイト列
    frame_description: GPT が生成した「1コマの動き」
    """
    if isinstance(base_image_source, (bytes, bytearray)):
        image_bytes = bytes(base_image_source)
    else:
        raise TypeError("base_image_source must be bytes or bytearray")
    if not frame_description:
        raise ValueError("frame_description is required")

    image_file = io.BytesIO(image_bytes)
    image_file.name = "base_image.png"

    # gpt-image-1-mini に image-to-image で渡す
    result = client.images.edit(
        model="gpt-image-1-mini",
        image=image_file,
        prompt=f"これはコマ送りアニメ用画像です。元のキャラクターを維持したまま、次の動きを加えてください: {frame_description}",
        size=size,
        n=1,
        quality="low"
    )

    return result.data[0].b64_json

