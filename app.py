import streamlit as st
import google.generativeai as genai
import os
from PIL import Image

# 1. Cấu hình bảo mật API Key từ Streamlit Secrets
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-3.5-flash")
except Exception:
    st.error("Chưa cấu hình API Key trong mục Secrets của Streamlit Cloud!")

st.title("🤖 Trợ Lý Học Tập - Thầy Long Bình")

# 2. Khởi tạo và quản lý trạng thái cuộc hội thoại (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_step" not in st.session_state:
    # Trạng thái ban đầu: BƯỚC 1 - Chào hỏi
    st.session_state.current_step = "CHAO_HOI"
if "selected_lesson" not in st.session_state:
    st.session_state.selected_lesson = None

# Định nghĩa câu lệnh hệ thống để AI đóng vai giáo viên
SYSTEM_PROMPT = (
    "Bạn là trợ lý học tập của thầy Long Bình tại trường THCS Hoàng Văn Thụ. "
    "Nhiệm vụ của bạn là dùng ngôn ngữ sư phạm, gần gũi để GỢI Ý từng bước giải "
    "phương pháp, tuyệt đối KHÔNG ĐƯỢC giải hết bài hay đưa thẳng đáp án chữ."
)

# --- BƯỚC 1: Xử lý lời chào tự động khi học sinh mở app ---
if st.session_state.current_step == "CHAO_HOI":
    welcome_text = "Chào em, thầy là trợ lý của thầy Long Bình. Hôm nay em cần thầy hỗ trợ bài tập nào? (Ví dụ: bài 1)"
    st.session_state.messages.append({"role": "assistant", "content": welcome_text})
    st.session_state.current_step = "CHO_HOC_SINH_CHON_BAI"

# Hiển thị lại lịch sử trò chuyện
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Nhận tin nhắn nhập vào từ học sinh
if user_input := st.chat_input("Nhập tin nhắn của em tại đây..."):
    # Hiển thị tin nhắn của học sinh lên màn hình
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # --- BƯỚC 2: Học sinh vừa chọn bài, chatbot hỏi phân nhánh ---
    if st.session_state.current_step == "CHO_HOC_SINH_CHON_BAI":
        st.session_state.selected_lesson = user_input.lower().replace(" ", "")
        
        ask_choice = f"Thầy đã ghi nhận em hỏi về **{user_input}**. Em muốn thầy **Gợi ý từng bước** để tự giải hay muốn **Xem đáp án cụ thể** luôn?"
        
        with st.chat_message("assistant"):
            st.write(ask_choice)
        st.session_state.messages.append({"role": "assistant", "content": ask_choice})
        st.session_state.current_step = "CHO_HOC_SINH_CHON_HUONG_GIAI"

    # --- BƯỚC 3: Xử lý phân nhánh "Gợi ý" hoặc "Đáp án" ---
    elif st.session_state.current_step == "CHO_HOC_SINH_CHON_HUONG_GIAI":
        user_choice = user_input.lower()
        
        # Nhánh 3a: Học sinh chọn XEM ĐÁP ÁN CỤ THỂ
        if "đáp án" in user_choice or "xem đáp án" in user_choice or "cụ thể" in user_choice:
            # Tìm chính xác 1 file ảnh tương ứng trong folder images/
            filename = f"images/{st.session_state.selected_lesson}.png"
            
            with st.chat_message("assistant"):
                if os.path.exists(filename):
                    # CHỈ hiển thị đúng 1 ảnh đáp án được yêu cầu
                    st.image(Image.open(filename), caption=f"Đáp án chính xác cho bài của em.")
                    st.session_state.messages.append({"role": "assistant", "content": f"[Hiển thị ảnh đáp án của bài]"})
                else:
                    msg_error = "Bài này thầy chưa cập nhật file ảnh đáp án lên hệ thống rồi, em chọn hướng 'Gợi ý' để thầy hướng dẫn nhé!"
                    st.write(msg_error)
                    st.session_state.messages.append({"role": "assistant", "content": msg_error})
            
            # Reset lại chu kỳ để học sinh có thể hỏi bài khác
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None

        # Nhánh 3b: Học sinh chọn GỢI Ý TỪNG BƯỚC
        else:
            prompt = f"{SYSTEM_PROMPT}\nHọc sinh đang làm bài: {st.session_state.selected_lesson}. Học sinh nói: {user_input}. Hãy đưa ra gợi ý bước đầu tiên."
            try:
                response = model.generate_content(prompt).text
                with st.chat_message("assistant"):
                    st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_step = "DANG_GOI_Y"
            except Exception as e:
                st.error(f"Lỗi gọi AI: {e}")

    # --- BƯỚC 4: Tiếp tục quá trình gợi ý hoặc nhận xét khi học sinh giải xong ---
    elif st.session_state.current_step == "DANG_GOI_Y":
        if "xong" in user_input.lower() or "hoàn thành" in user_input.lower():
            feedback = "Tuyệt vời! Em làm tốt lắm. Hãy chuẩn bị sang bài tập tiếp theo nhé!"
            with st.chat_message("assistant"):
                st.write(feedback)
            st.session_state.messages.append({"role": "assistant", "content": feedback})
            
            # Reset chu kỳ mới
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None
        else:
            # Tiếp tục gợi ý bước tiếp theo
            prompt = f"{SYSTEM_PROMPT}\nHọc sinh đang thảo luận bài: {st.session_state.selected_lesson}. Học sinh phản hồi: {user_input}. Hãy tiếp tục dẫn dắt."
            try:
                response = model.generate_content(prompt).text
                with st.chat_message("assistant"):
                    st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Lỗi: {e}")
