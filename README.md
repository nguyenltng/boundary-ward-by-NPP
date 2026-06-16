# 🗺️ Convert Address VN — Streamlit App

Ứng dụng chuyển đổi và chuẩn hoá địa chỉ Việt Nam theo đơn vị hành chính mới (từ tháng 7/2025).

## Tính năng

- Upload file Excel chứa địa chỉ đầy đủ
- Tự động phân tích → tách ra `address`, `ward`, `city`
- Hỗ trợ địa chỉ cũ (63 tỉnh) và tự động chuyển sang đơn vị hành chính mới (34 tỉnh)
- Download kết quả dưới dạng Excel
- Hiển thị thống kê tỷ lệ parse thành công

## Cấu trúc file

```
convert-address-VN/
├── app.py              # Streamlit UI chính
├── requirements.txt    # Dependencies
├── .streamlit/
│   └── config.toml     # Dark theme config
└── README.md
```

## Chạy local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy lên Streamlit Community Cloud (share.streamlit.io)

### Bước 1: Push code lên GitHub

```bash
git init
git add .
git commit -m "feat: add streamlit UI for address conversion"
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

### Bước 2: Deploy trên share.streamlit.io

1. Truy cập **https://share.streamlit.io** và đăng nhập bằng GitHub
2. Nhấn **"Create app"** → **"Deploy a public app from GitHub"**
3. Điền thông tin:
   - **Repository**: `<username>/<repo-name>`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Nhấn **"Deploy!"**

Sau vài phút, app sẽ live tại `https://<app-name>.streamlit.app`.

## Cấu hình sidebar

Trong thanh sidebar bên trái của app, bạn có thể đổi **"Tên cột địa chỉ đầu vào"** nếu file Excel của bạn dùng tên cột khác (mặc định là `address_full`).
