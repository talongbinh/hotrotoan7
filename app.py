import streamlit as st
import google.generativeai as genai
import os
from PIL import Image
import google.api_core.exceptions

# --- 1. CẤU HÌNH BẢO MẬT API KEY ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-3.0-flash")
except Exception:
    st.error("Chưa cấu hình API Key trong mục Secrets của Streamlit Cloud!")

st.title("🤖 Trợ Lý Học Tập - Thầy Long Bình")

# --- 2. KHỞI TẠO TRẠNG THÁI CUỘC HỘI THOẠI (SESSION STATE) ---
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

# --- BƯỚC 1: CHÀO HỎI TỰ ĐỘNG ---
if st.session_state.current_step == "CHAO_HOI":
    welcome_text = "Chào em, thầy là trợ lý của thầy Long Bình. Hôm nay em cần thầy hỗ trợ bài tập nào? (Ví dụ nhập: bài 1, bài 2,...)"
    st.session_state.messages = [{"role": "assistant", "content": welcome_text}]
    st.session_state.current_step = "CHO_HOC_SINH_CHON_BAI"

# Hiển thị lịch sử trò chuyện
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- BƯỚC 2: NHẬN TÊN BÀI TẬP TỪ HỌC SINH ---
if st.session_state.current_step == "CHO_HOC_SINH_CHON_BAI":
    if user_input := st.chat_input("Nhập tên bài tập tại đây..."):
        st.session_state.selected_lesson = user_input.lower().replace(" ", "")
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.current_step = "CHO_HOC_SINH_CHON_HUONG_GIAI"
        st.rerun()

# --- BƯỚC 3: HIỂN THỊ LỰA CHỌN NÚT BẤM ---
elif st.session_state.current_step == "CHO_HOC_SINH_CHON_HUONG_GIAI":
    st.warning(f"Thầy đang xử lý yêu cầu cho bài: **{st.session_state.selected_lesson.upper()}**")
    st.write("Em muốn thầy hỗ trợ theo hướng nào dưới đây?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📖 Gợi ý từng bước"):
            st.session_state.messages.append({"role": "user", "content": "Gợi ý từng bước"})
            # Chuyển trạng thái để xuống dưới gọi AI (Không gọi AI trực tiếp trong button)
            st.session_state.current_step = "KICH_HOAT_GOI_Y_DAU_TIEN"
            st.rerun()
            
    with col2:
        if st.button("🎯 Xem đáp án cụ thể"):
            st.session_state.messages.append({"role": "user", "content": "Xem đáp án cụ thể"})
            
            # Quét tìm mọi đuôi file ảnh trong folder images
            lesson = st.session_state.selected_lesson
            possible_files = [
                f"images/{lesson}.jpg", f"images/{lesson}.png", 
                f"images/{lesson}.jpeg", f"images/{lesson}.JPG", f"images/{lesson}.PNG"
            ]
            
            filename = None
            for f_path in possible_files:
                if os.path.exists(f_path):
                    filename = f_path
                    break
            
            if filename:
                with st.chat_message("assistant"):
                    st.image(Image.open(filename), caption=f"Đáp án chính xác cho bài {lesson.upper()}")
                st.session_state.messages.append({"role": "assistant", "content": f"[Đã hiển thị ảnh đáp án bài {lesson}]"})
            else:
                if not os.path.exists("images"):
                    err_msg = "LỖI: Ứng dụng không tìm thấy thư mục tên là 'images' trên GitHub của thầy."
                else:
                    files_in_folder = os.listdir("images")
                    err_msg = f"Thầy chưa tìm thấy file '{lesson}.jpg' trong thư mục 'images'. Hiện trong thư mục này chỉ có: {files_in_folder}"
                
                with st.chat_message("assistant"):
                    st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
            
            # Hoàn thành chu trình đáp án, reset về ban đầu
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None
            st.button("Hỏi bài tập khác 🔄")

# --- BƯỚC EXTRA: KÍCH HOẠT CÂU GỢI Ý ĐẦU TIÊN TỪ AI ---
elif st.session_state.current_step == "KICH_HOAT_GOI_Y_DAU_TIEN":
    with st.spinner("Thầy đang suy nghĩ câu gợi ý..."):
        prompt = f"{SYSTEM_PROMPT}\nHọc sinh đang làm bài: {st.session_state.selected_lesson}. Hãy đưa ra câu hỏi gợi mở hoặc gợi ý bước 1 để hướng dẫn học sinh."
        try:
            response = model.generate_content(prompt).text
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_step = "DANG_GOI_Y"
            st.rerun()
        except google.api_core.exceptions.ResourceExhausted:
            st.error("Hệ thống AI đang nhận quá nhiều yêu cầu cùng lúc. Em vui lòng chờ 1 phút rồi gõ tin nhắn bất kỳ để kích hoạt lại nhé!")
        except Exception:
            st.error("Thầy gặp chút gián đoạn nhỏ, em thử gõ gì đó để kích hoạt lại nhé!")

# --- BƯỚC 4: TIẾN TRÌNH THẢO LUẬN, GỢI Ý TIẾP THEO ---
elif st.session_state.current_step == "DANG_GOI_Y":
    if user_input := st.chat_input("Nhập câu trả lời hoặc thắc mắc của em..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        if "xong" in user_input.lower() or "hoàn thành" in user_input.lower():
            feedback = "Tuyệt vời! Em làm tốt lắm. Hãy bấm nút Tải lại trang hoặc gõ tiếp tên bài mới để hỏi nhé!"
            st.session_state.messages.append({"role": "assistant", "content": feedback})
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None
            st.rerun()
        else:
            prompt = f"{SYSTEM_PROMPT}\nHọc sinh đang thảo luận bài: {st.session_state.selected_lesson}. Học sinh phản hồi: {user_input}. Hãy tiếp tục dẫn dắt bằng câu hỏi gợi mở bước tiếp theo."
            try:
                response = model.generate_content(prompt).text
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            except google.api_core.exceptions.ResourceExhausted:
                st.error("Hệ thống AI đang quá tải một chút. Em vui lòng chờ 1 phút rồi gõ lại nhé!")
            except Exception:
                st.error("Hệ thống gặp gián đoạn nhỏ, em thử gõ lại câu trả lời nhé!")
