import streamlit as st
import base64
import json

from gif_maker import make_gif
from openai_client import (
    get_missing_openai_env_vars,
    generate_base_image,
    extract_motion_and_generate_frames,
    generate_motion_frame
)

st.title("GIFアニメ生成アプリ（DALL·E 3：ベース画像 → 可変コマGIF）")

missing_env_vars = get_missing_openai_env_vars()
if missing_env_vars:
    st.error(
        "Azure OpenAI の設定が不足しています: "
        + ", ".join(missing_env_vars)
    )
    st.stop()

# -----------------------------
# ① ベース画像生成（DALL·E 3 / gpt-image-1-mini）
# -----------------------------
user_prompt = st.text_area(
    "キャラの説明（ベース画像用）",
    "かわいいちびキャラが立っている"
)

if st.button("ベース画像を生成（gpt-image-1-mini）"):
    try:
        base_b64 = generate_base_image(user_prompt)
        img_bytes = base64.b64decode(base_b64)
    except Exception as exc:
        st.error(f"ベース画像の生成に失敗しました: {exc}")
    else:
        st.image(img_bytes)
        st.session_state["base_image_b64"] = base_b64
        st.session_state["base_image_bytes"] = img_bytes

if st.session_state.get("base_image_bytes"):
    st.caption("現在のベース画像")
    st.image(st.session_state["base_image_bytes"])



# -----------------------------
# ② GIF用4コマ生成（gpt-image-1-mini image-to-image）
# -----------------------------
motion_prompt = st.text_area(
    "動きの説明（例：右手を振る、瞬きする）",
    "瞬きする"
)

frame_count = st.slider(
    "コマ数",
    min_value=2,
    max_value=8,
    value=4,
    step=1
)

if st.button(f"{frame_count}コマ画像を生成して確認する（gpt-image-1-mini）"):

    base_image_bytes = st.session_state.get("base_image_bytes")

    if not base_image_bytes:
        st.error("ベース画像がありません。先にベース画像を生成してください。")
        st.stop()
    try:
        motion_json = extract_motion_and_generate_frames(
            motion_prompt,
            frame_count=frame_count
        )
        motion_data = json.loads(motion_json)
        frames = motion_data["frames"]
        if not isinstance(frames, list) or len(frames) != frame_count:
            raise ValueError(f"frames must contain exactly {frame_count} items")
        for frame in frames:
            if not isinstance(frame, dict) or not frame.get("description"):
                raise ValueError("each frame must include a description")
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        st.error(f"コマ指示の生成結果を解析できませんでした: {exc}")
        st.code(motion_json if "motion_json" in locals() else "")
        st.stop()
    except ValueError as exc:
        st.error(f"コマ指示の形式が不正です: {exc}")
        st.code(motion_json if "motion_json" in locals() else "")
        st.stop()
    except Exception as exc:
        st.error(f"コマ指示の生成に失敗しました: {exc}")
        st.stop()

    st.json(motion_data)

    frame_images = []
    frame_descriptions = []
    for frame in frames:
        try:
            frame_b64 = generate_motion_frame(base_image_bytes, frame["description"])
            frame_bytes = base64.b64decode(frame_b64)
            frame_images.append(frame_bytes)
            frame_descriptions.append(frame["description"])
        except Exception as exc:
            st.error(f"コマ画像の生成に失敗しました: {exc}")
            break
    else:
        st.session_state["generated_frames"] = frame_images
        st.session_state["generated_frame_descriptions"] = frame_descriptions
        st.session_state["generated_frame_count"] = frame_count
        st.session_state["generated_motion_data"] = motion_data
        st.session_state.pop("generated_gif_bytes", None)

generated_frames = st.session_state.get("generated_frames")
generated_frame_descriptions = st.session_state.get(
    "generated_frame_descriptions",
    []
)
generated_motion_data = st.session_state.get("generated_motion_data")
generated_frame_count = st.session_state.get("generated_frame_count")

if generated_frames:
    if generated_motion_data:
        st.subheader("各コマへの指示")
        for index, frame in enumerate(generated_motion_data.get("frames", []), start=1):
            description = frame.get("description", "")
            st.write(f"{index}コマ目: {description}")
    st.subheader("生成されたコマ画像")
    for index, frame_bytes in enumerate(generated_frames):
        caption = (
            generated_frame_descriptions[index]
            if index < len(generated_frame_descriptions)
            else f"{index + 1}コマ目"
        )
        st.image(frame_bytes, caption=caption)

    gif_duration = st.slider(
        "GIFのコマ表示時間（秒）",
        min_value=0.05,
        max_value=3.0,
        value=0.2,
        step=0.05,
        key="gif_duration"
    )

    if st.button("確認したコマ画像からGIFアニメを作成"):
        try:
            gif_bytes = make_gif(generated_frames,  duration=gif_duration)
        except Exception as exc:
            st.error(f"GIFアニメの生成に失敗しました: {exc}")
        else:
            st.session_state["generated_gif_bytes"] = gif_bytes

generated_gif_bytes = st.session_state.get("generated_gif_bytes")
if generated_gif_bytes:
    st.subheader("生成されたGIFアニメ")
    st.caption(
        f"{generated_frame_count}コマ / "
        f"1コマあたり {st.session_state.get('gif_duration', 0.2):.2f} 秒"
    )
    st.image(generated_gif_bytes)
    st.download_button(
        "GIFをダウンロード",
        data=generated_gif_bytes,
        file_name="animation.gif",
        mime="image/gif"
    )
