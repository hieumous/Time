# Time

Lịch tuần từ Thứ Hai đến Chủ Nhật. Mỗi ngày có buổi sáng, buổi chiều và buổi tối để ghi việc cần làm, việc đã xong và ghi chú.

## Deploy lên Vercel

Repo: https://github.com/hieumous/Time

Vercel nhận file `app.py` (biến `app` của FastAPI) và `tool.vercel.entrypoint` trong `pyproject.toml`. Nối repo GitHub với Vercel, framework để Python, rồi bấm Deploy. Link gửi cho người khác là đường dẫn Vercel cấp, dạng `https://<tên-project>.vercel.app`.

Việc và ghi chú được lưu trong trình duyệt của từng người, vì Vercel không giữ file `data/planner.json` giữa các lần mở trang.

## Chạy trên máy

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

Mở http://127.0.0.1:8000
