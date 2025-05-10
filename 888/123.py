import streamlit as st
import requests
import logging
import time

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)

# API 密钥
STABLE_DIFFUSION_API_KEY = "sk-drvRI8SfNEUPUYr2nTLDFVc6fPi4Ng5n6dDIhntYUeVjlrSa"
HEYGEN_API_KEY = "ZTA2Y2FiYjY5NWMyNDg2MmE1ZTkzNzZiZWQyMTRlYmMtMTc0NTk0MzEwNw=="

# 检查 API 密钥是否已设置
if not STABLE_DIFFUSION_API_KEY or not HEYGEN_API_KEY:
    st.error("请确保已正确设置 Stable Diffusion 和 HeyGen 的 API 密钥。")
    st.stop()

# HeyGen API 函数
def generate_video(avatar_id, input_text, voice_id="2d5b0e6cf36f460aa7fc47e3eee4ba54"):
    """使用 HeyGen 生成视频"""
    url = "https://api.heygen.com/v2/video/generate"
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": input_text,
                    "voice_id": voice_id
                },
                "background": {
                    "type": "color",
                    "value": "#ffffff"
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        }
    }
    logging.debug(f"HeyGen 请求体: {data}")
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"生成视频失败：{response.text}")
        return None

def check_video_status(video_id):
    """查询视频生成状态"""
    url = f"https://api.heygen.com/v2/videos/{video_id}"
    headers = {
        "X-Api-Key": HEYGEN_API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"查询状态失败：{response.text}")
        return None

# 设置网页标题
st.title("MetaFrame")

# 输入场景或剧情文本
st.header("输入场景或剧情")
scene_description = st.text_input("请输入场景或剧情描述")

# 预设 HeyGen 角色 ID（使用官方预设角色，无需上传图片）
PRESET_AVATAR_IDS = [
    "Daisy-inskirt-20220818",  # 示例角色 ID 1
    "Alex-office-20220818",    # 示例角色 ID 2
    "Emma-coffee-20220818"     # 示例角色 ID 3
]

# 生成按钮
if st.button("生成内容"):
    if scene_description:
        st.write("内容生成中，请稍候...")

        # 生成场景图片（Stable Diffusion）
        try:
            sd_url = "https://api.stablediffusionapi.com/v1/generate"
            headers = {
                "Authorization": f"Bearer {STABLE_DIFFUSION_API_KEY}",
                "Content-Type": "application/json; charset=utf-8"
            }
            response = requests.post(
                sd_url,
                headers=headers,
                json={"prompt": scene_description}
            )
            response.raise_for_status()
            scene_image_url = response.json().get("image_url")
            st.image(scene_image_url, caption="生成的场景图片")
        except Exception as e:
            st.error(f"场景图片生成失败：{str(e)}")

        # 使用预设角色生成视频（无需上传图片）
        for i, avatar_id in enumerate(PRESET_AVATAR_IDS):
            st.subheader(f"生成角色 {i+1} 的视频")
            try:
                st.info(f"使用预设角色: {avatar_id}")
                st.info("开始生成视频...")
                video_data = generate_video(avatar_id, f"场景描述：{scene_description}")
                
                if video_data and "video_id" in video_data:
                    video_id = video_data["video_id"]
                    st.info(f"视频生成中（ID: {video_id}），请耐心等待...")
                    
                    # 创建进度条
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 轮询检查状态
                    max_attempts = 20
                    for attempt in range(max_attempts):
                        progress = (attempt + 1) / max_attempts
                        progress_bar.progress(progress)
                        
                        status_data = check_video_status(video_id)
                        status = status_data.get("status")
                        message = status_data.get("message", "")
                        
                        status_text.text(f"状态: {status} - {message} ({attempt+1}/{max_attempts})")
                        
                        if status == "completed":
                            st.success("视频生成完成！")
                            st.video(status_data.get("video_url"))
                            break
                        elif status == "failed":
                            st.error(f"视频生成失败：{message}")
                            break
                        else:
                            time.sleep(10)  # 等待 10 秒后重试
                    else:
                        st.warning("查询超时，请在 HeyGen 控制台查看结果")
            except Exception as e:
                st.error(f"生成角色 {i+1} 的视频失败：{str(e)}")
    else:
        st.error("请填写场景描述。")
