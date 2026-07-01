import streamlit as st
import google.generativeai as genai
import os
from PIL import Image
import google.api_core.exceptions

# --- 1. CẤU HÌNH BẢO MẬT API KEY ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
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
    "Bạn là trợ lý học tập môn Toán và Khoa học tự nhiên của thầy Long Bình tại trường THCS Hoàng Văn Thụ. "
    "Nhiệm vụ của bạn là đóng vai một giáo viên sư phạm chuẩn mực. Khi được cung cấp hình ảnh bài toán, "
    "hãy phân tích kỹ đề bài và hình vẽ trong ảnh để hướng dẫn học sinh giải theo từng bước nhỏ. "
    "TỪNG BƯỚC MỘT: Chỉ gợi ý hoặc đặt câu hỏi mở cho bước đầu tiên, chờ học sinh trả lời rồi mới nhận xét và hướng dẫn tiếp. "
    "TUYỆT ĐỐI KHÔNG ĐƯỢC giải hết toàn bộ bài, không đưa thẳng đáp án chữ ngay từ đầu."
)

# Hàm tìm đường dẫn ảnh dựa vào tên bài
def find_image_path(lesson):
    possible_files = [
        f"images/{lesson}.jpg", f"images/{lesson}.png", 
        f"images/{lesson}.jpeg", f"images/{lesson}.JPG", f"images/{lesson}.PNG"
    ]
    for f_path in possible_files:
        if os.path.exists(f_path):
            return f_path
    return None

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
            st.session_state.current_step = "KICH_HOAT_GOI_Y_DAU_TIEN"
            st.rerun()
            
    with col2:
        if st.button("🎯 Xem đáp án cụ thể"):
            st.session_state.messages.append({"role": "user", "content": "Xem đáp án cụ thể"})
            
            img_path = find_image_path(st.session_state.selected_lesson)
            if img_path:
                with st.chat_message("assistant"):
                    st.image(Image.open(img_path), caption=f"Đáp án chính xác cho bài {st.session_state.selected_lesson.upper()}")
                st.session_state.messages.append({"role": "assistant", "content": f"[Đã hiển thị ảnh đáp án bài {st.session_state.selected_lesson}]"})
            else:
                err_msg = f"Thầy chưa tìm thấy file ảnh '{st.session_state.selected_lesson}.jpg' trong thư mục 'images'."
                with st.chat_message("assistant"):
                    st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
            
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None
            st.button("Hỏi bài tập khác 🔄")

# --- BƯỚC EXTRA: AI TỰ ĐỌC ẢNH VÀ ĐƯA RA CÂU GỢI Ý ĐẦU TIÊN ---
elif st.session_state.current_step == "KICH_HOAT_GOI_Y_DAU_TIEN":
    with st.spinner("Thầy đang nhìn hình vẽ và đọc đề bài để đưa ra gợi ý..."):
        lesson_key = st.session_state.selected_lesson
        img_path = find_image_path(lesson_key)
        
        # Chuẩn bị nội dung gửi đi cho AI
        prompt_content = [
            f"{SYSTEM_PROMPT}\n"
            f"Học sinh đang yêu cầu hướng dẫn làm bài: {lesson_key.upper()}.\n"
            f"Nhiệm vụ: Hãy nhìn kỹ hình ảnh đính kèm, phân tích câu hỏi trong ảnh và đưa ra câu hỏi gợi mở bước 1."
        ]
        
        # Nếu tìm thấy file ảnh tương ứng trong thư mục, đính kèm vào cho AI đọc luôn
        if img_path:
            try:
                img_data = Image.open(img_path)
                prompt_content.append(img_data)
            except Exception:
                pass

        try:
            # Truyền mảng chứa cả chữ và ảnh vào hàm generate_content
            response = model.generate_content(prompt_content).text
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_step = "DANG_GOI_Y"
            st.rerun()
        except google.api_core.exceptions.ResourceExhausted:
            st.error("Hệ thống AI đang nhận quá nhiều yêu cầu cùng lúc. Em vui lòng chờ 1 phút rồi gõ tin nhắn bất kỳ nhé!")
            if user_input := st.chat_input("Gõ chữ bất kỳ để thử lại..."):
                st.rerun()
        except Exception:
            st.error("Thầy gặp chút gián đoạn nhỏ, em thử gõ gì đó để kích hoạt lại nhé!")
            if user_input := st.chat_input("Gõ chữ bất kỳ để thử lại..."):
                st.rerun()

# --- BƯỚC 4: TIẾN TRÌNH THẢO LUẬN, GỢI Ý TIẾP THEO ---
elif st.session_state.current_step == "DANG_GOI_Y":
    if user_input := st.chat_input("Nhập câu trả lời hoặc thắc mắc của em..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        if "xong" in user_input.lower() or "hoàn thành" in user_input.lower():
            feedback = "Tuyệt vời! Em làm tốt lắm. Hãy chuẩn bị sang bài tập tiếp theo nhé!"
            st.session_state.messages.append({"role": "assistant", "content": feedback})
            st.session_state.current_step = "CHAO_HOI"
            st.session_state.selected_lesson = None
            st.rerun()
        else:
            lesson_key = st.session_state.selected_lesson
            img_path = find_image_path(lesson_key)
            
            # Giữ ngữ cảnh ảnh xuyên suốt cuộc hội thoại
            prompt_content = [
                f"{SYSTEM_PROMPT}\n"
                f"Học sinh đang giải bài toán trong ảnh này.\n"
                f"Học sinh phản hồi: {user_input}.\n"
                f"Nhiệm vụ: Dựa vào hình ảnh bài toán và câu trả lời của học sinh, hãy đưa ra nhận xét ngắn gọn và gợi ý bước tiếp theo."
            ]
            
            if img_path:
                try:
                    prompt_content.append(Image.open(img_path))
                except Exception:
                    pass
                    
            try:
                response = model.generate_content(prompt_content).text
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            except google.api_core.exceptions.ResourceExhausted:
                st.error("Hệ thống AI đang quá tải một chút. Em vui lòng chờ 1 phút rồi gõ lại nhé!")
            except Exception:
                st.error("Hệ thống gặp gián đoạn nhỏ, em thử gõ lại câu trả lời nhé!")
