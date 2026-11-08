# Time

Lịch tuần từ Thứ Hai đến Chủ Nhật. Mỗi ngày có buổi sáng, buổi chiều và buổi tối để ghi việc cần làm, việc đã xong và ghi chú.

## Link gửi cho người khác

Repo: https://github.com/hieumous/Time

App chạy trên web (mở được trên điện thoại, không cần cài Python):

https://share.streamlit.io/deploy?repository=hieumous/Time&branch=main&mainModule=streamlit_app.py

Mở link đó bằng tài khoản GitHub `hieumous`, bấm Deploy. Streamlit Community Cloud sẽ cấp một đường dẫn dạng `https://<tên-app>.streamlit.app`. Đó là link gửi cho người khác. Mỗi lần đẩy code lên nhánh `main`, app tự cập nhật.

## Chạy trên máy

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\streamlit.exe run streamlit_app.py
```

Mở http://localhost:8501

Dữ liệu cá nhân nằm ở `data/planner.json` và không được đưa lên GitHub.
