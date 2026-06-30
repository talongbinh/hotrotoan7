import streamlit as st
import google.generativeai as genai
import os
from PIL import Image

# Cấu hình bảo mật API Key từ Streamlit Secrets
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-3.5-flash")
except Exception:
    st.error("Chưa cấu hình API Key trong mục Secrets của Streamlit Cloud!")

st.title("🤖 Trợ Lý Học Tập - Thầy Long Bình")

# Khởi tạo trạng thái cuộc hội thoại
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_step" not in st.session_state:
    st.session_state.current_step = "CHAO_HOI"
if "selected_lesson" not in st.session_state:
    st.session_state.selected_lesson = None

SYSTEM_PROMPT = (
    "Bạn là trợ lý học tập của thầy Long Bình tại trường THCS Hoàng Văn Thụ. "
    "Nhiệm vụ của bạn là dùng ngôn ngữ sư phạm để GỢI Ý từng bước giải "
    "phương pháp, tuyệt đối KHÔNG ĐƯỢC giải hết bài hay đưa thẳng đáp án chữ."
)

# --- BƯỚC 1: Chào hỏi tự động ---
if st.session_state.current_step == "CHAO_HOI":
    welcome_text = "Chào em, thầy là trợ lý của thầy Long Bình. Hôm nay em cần thầy hỗ trợ bài tập nào? (Ví dụ nhập: bài 1, bài 2,...)"
    st.session_state.messages.append({"role": "assistant", "content": welcome_text})
    st.session_state.current_step = "CHO_HOC_SINH_CHON_BAI"

# Hiển thị lịch sử trò chuyện
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- BƯỚC 2: Nhận tên bài tập từ học sinh ---
if st.session_state.current_step == "CHO_HOC_SINH_CHON_BAI":
    if user_input := st.chat_input("Nhập tên bài tập tại đây..."):
        st.session_state.selected_lesson = user_input.lower().replace(" ", "")
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Chuyển trạng thái sang chờ chọn hướng đi
        st.session_state.current_step = "CHO_HOC_SINH_CHON_HUONG_GIAI"
        st.rerun()

# --- BƯỚC 3: Hiển thị lựa chọn bằng NÚT BẤM (Tránh học sinh gõ nhầm) ---
elif st.session_state.current_step == "CHO_HOC_SINH_CHON_HUONG_GIAI":
    st.warning(f"Thầy đang xử lý yêu cầu cho bài: **{st.session_state.selected_lesson.upper()}**")
    st.write("Em muốn thầy hỗ trợ theo hướng nào dưới đây?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📖 Gợi ý từng bước"):
            st.session_state.messages.append({"role": "user", "content": "Gợi ý từng bước"})
            st.session_state.current_step = "BAT_DAU_GOI_Y"
            st.rerun()
            
    with col2:
        if st.button("🎯 Xem đáp án cụ thể"):
            st.session_state.messages.append({"role": "user", "content": "Xem đáp án cụ thể"})
            
            # Quét tìm ảnh trong folder images/
            filename = f"images/{st.session_state.selected_lesson}.png"
            if os.path.exists(filename):
                # Hiển thị duy nhất 1 ảnh của bài đó
                with st.chat_message("assistant"):
                    st.image(Image.open(filename), caption="Đáp án chính xác của câu hỏi em yêu cầu.")
                st.session_state.messages.append({"role": "assistant", "content": "[Đã hiển thị ảnh đáp án]"})
            else:
                with st.chat_message("assistant"):
                    st.error("Bài này thầy chưa cập nhật file ảnh đáp án, em bấm chọn nút 'Gợi ý từng bước' nhé!")
            
            # Hoàn thành chu trình, reset quay lại từ đầu
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None
            st.button("Hỏi bài tập khác 🔄")

# --- BƯỚC 4: Tiến trình gợi ý toán học ---
elif st.session_state.current_step == "BAT_DAU_GOI_Y":
    if user_input := st.chat_input("Nhập câu trả lời hoặc thắc mắc của em..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        if "xong" in user_input.lower() or "hoàn thành" in user_input.lower():
            feedback = "Tuyệt vời! Em làm tốt lắm. Hãy bấm nút F5 hoặc tải lại trang nếu muốn hỏi bài khác nhé!"
            st.session_state.messages.append({"role": "assistant", "content": feedback})
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None
            st.rerun()
        else:
            prompt = f"{SYSTEM_PROMPT}\nHọc sinh đang hỏi bài: {st.session_state.selected_lesson}. Học sinh nói: {user_input}. Hãy đưa ra gợi ý tiếp theo."
            response = model.generate_content(prompt).text
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
