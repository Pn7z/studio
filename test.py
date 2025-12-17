import streamlit as st
import cv2
import numpy as np
from skimage import color
from PIL import Image

def load_image(image_file):
    img = Image.open(image_file)
    return np.array(img)

def smart_crop_center(img, crop_ratio=0.5):
    """
    智慧裁切：只取圖片中央區域，排除周圍邊框干擾 (如木作邊、陰影)
    crop_ratio: 0.5 代表取中央 50%
    """
    h, w, _ = img.shape
    center_h, center_w = h // 2, w // 2
    crop_h, crop_w = int(h * crop_ratio), int(w * crop_ratio)
    
    start_y = center_h - crop_h // 2
    start_x = center_w - crop_w // 2
    
    return img[start_y:start_y+crop_h, start_x:start_x+crop_w]

def calculate_delta_e(img_std, img_tgt):
    """計算 CIEDE2000 色差"""
    # 轉換為 Lab 色彩空間
    lab_std = color.rgb2lab(img_std)
    lab_tgt = color.rgb2lab(img_tgt)
    
    # 取平均值代表該區域顏色
    avg_lab_std = np.mean(lab_std, axis=(0,1))
    avg_lab_tgt = np.mean(lab_tgt, axis=(0,1))
    
    # reshape 為了符合 scikit-image 的輸入格式
    avg_lab_std = avg_lab_std.reshape(1, 1, 3)
    avg_lab_tgt = avg_lab_tgt.reshape(1, 1, 3)

    # 計算 Delta E
    delta_e = color.deltaE_ciede2000(avg_lab_std, avg_lab_tgt)[0][0]
    return delta_e

# --- APP 介面設計 ---
st.set_page_config(page_title="LUXUS 智眼驗收", page_icon="🎨")

st.title("🎨 LUXUS 智眼驗收系統 (MVP)")
st.markdown("### AI 輔助驗收工具：科學化解決色差爭議")

# 側邊欄設定
st.sidebar.header("⚙️ 參數設定")
threshold = st.sidebar.slider("合格標準 (Delta E)", 1.0, 10.0, 3.0, 0.1)
st.sidebar.info(f"目前設定：色差值 < {threshold} 為合格")

st.write("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 樣板基準 (Standard)")
    st.info("請上傳簽約時的樣板照片 (含木邊可)")
    file_std = st.file_uploader("上傳樣板圖", type=['jpg', 'png', 'jpeg'], key="std")

with col2:
    st.subheader("2. 完工現況 (Target)")
    st.info("請上傳完工後的牆面照片")
    file_tgt = st.file_uploader("上傳完工圖", type=['jpg', 'png', 'jpeg'], key="tgt")

if file_std and file_tgt:
    # 讀取圖片
    img_std_origin = load_image(file_std)
    img_tgt_origin = load_image(file_tgt)

    # 執行智慧裁切
    img_std_crop = smart_crop_center(img_std_origin)
    img_tgt_crop = smart_crop_center(img_tgt_origin)

    st.write("---")
    st.subheader("🔍 AI 分析視角 (已排除邊框干擾)")
    
    # 顯示裁切後的對比
    col_preview1, col_preview2 = st.columns(2)
    with col_preview1:
        st.image(img_std_crop, caption="樣板採樣區 (AI Crop)", use_column_width=True)
    with col_preview2:
        st.image(img_tgt_crop, caption="完工採樣區 (AI Crop)", use_column_width=True)

    # 計算與判定
    if st.button("🚀 開始 AI 驗收判定"):
        with st.spinner('AI 正在進行色彩光譜分析...'):
            delta_e = calculate_delta_e(img_std_crop, img_tgt_crop)
            
            st.write("---")
            st.header("📊 驗收結果報告")
            
            metric_col1, metric_col2 = st.columns([1, 2])
            
            with metric_col1:
                st.metric(label="Delta E 色差值", value=f"{delta_e:.2f}")
            
            with metric_col2:
                if delta_e < threshold:
                    st.success(f"✅ 驗收通過 (PASS)")
                    st.markdown(f"**判定說明：** 色差值 {delta_e:.2f} 低於合約標準 {threshold}。符合國際標準驗收規範。")
                    st.balloons()
                else:
                    st.error(f"❌ 驗收失敗 (FAIL)")
                    st.markdown(f"**判定說明：** 色差值 {delta_e:.2f} 高於合約標準 {threshold}。建議進行修補或重做。")

else:
    st.warning("請先上傳兩張照片以開始分析。")

# 頁尾
st.markdown("---")
st.caption("Powered by LUXUS AI Tech | 內部測試版 v0.1")
